/**
 * @file ota.c
 * @brief C6 gateway OTA client (#34). See ota.h for the flow.
 */
#include "ota.h"
#include "ota_logic.h"
#include "config.h"
#include "backend_tls.h"   /* http(s)/ws(s) and the server certificate (#66) */
#include "wifi_client.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_ota_ops.h"
#include "esp_app_desc.h"
#include "esp_http_client.h"
#include "esp_system.h"
#include "nvs.h"
#include "psa/crypto.h"

static const char *TAG = "c6_ota";

#define OTA_NVS_KEY        "ota_target"
#define HEALTH_TIMEOUT_MS  (120 * 1000)    /* a new image must reach the backend within this */

static volatile bool s_running = false;
static char s_mac[DEVICE_MAC_STR_LEN];

/* ── Reporting ───────────────────────────────────────────────────── */

static void report(const char *state, const char *version, esp_err_t err, const char *why)
{
    char json[320];
    snprintf(json, sizeof(json),
             "{\"mac_address\":\"%s\",\"state\":\"%s\",\"version\":\"%s\",\"error\":\"%s\",\"error_code\":%d}",
             s_mac, state, version ? version : "", why ? why : "", (int)err);
    int status = http_post_api("/api/device/ota/status", json, NULL, 0);
    ESP_LOGI(TAG, "OTA %s %s → HTTP %d%s%s", state, version ? version : "", status,
             why && *why ? ": " : "", why ? why : "");
}

static void fail(const char *version, esp_err_t err, const char *why)
{
    ESP_LOGE(TAG, "OTA to %s failed: %s (%s)", version, why, esp_err_to_name(err));
    report("failed", version, err, why);
}

static void remember_target(const char *version)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        if (version) {
            nvs_set_str(h, OTA_NVS_KEY, version);
        } else {
            nvs_erase_key(h, OTA_NVS_KEY);
        }
        nvs_commit(h);
        nvs_close(h);
    }
}

/* ── Download + install ──────────────────────────────────────────── */

/* Stream the image into `part` while hashing it. Returns ESP_OK and fills
 * digest, or an error (nothing is made bootable on error). */
static esp_err_t download(const ota_offer_t *o, const esp_partition_t *part,
                          esp_ota_handle_t *handle, uint8_t digest[32])
{
    char url[320], path[160];
    snprintf(path, sizeof(path), "/api/device/firmware/download?mac_address=%s&version=%s", s_mac, o->version);
    http_api_url(url, sizeof(url), path);
    esp_http_client_config_t cfg = { .url = url, .method = HTTP_METHOD_GET, .timeout_ms = 30000, .buffer_size = 4096 };
    BACKEND_TLS_APPLY(cfg);
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    if (!client) return ESP_ERR_NO_MEM;
    esp_http_client_set_header(client, "X-API-Key", g_cfg.api_key);

    esp_err_t err = esp_http_client_open(client, 0);
    if (err != ESP_OK) {
        esp_http_client_cleanup(client);
        return err;
    }
    int64_t length = esp_http_client_fetch_headers(client);
    int status = esp_http_client_get_status_code(client);
    if (status != 200 || (length > 0 && length != (int64_t)o->size)) {
        ESP_LOGE(TAG, "download refused: HTTP %d, %lld bytes (expected %lu)", status,
                 (long long)length, (unsigned long)o->size);
        esp_http_client_cleanup(client);
        return status != 200 ? ESP_ERR_INVALID_RESPONSE : ESP_ERR_INVALID_SIZE;
    }

    psa_crypto_init();
    psa_hash_operation_t hash = PSA_HASH_OPERATION_INIT;
    if (psa_hash_setup(&hash, PSA_ALG_SHA_256) != PSA_SUCCESS) {
        esp_http_client_cleanup(client);
        return ESP_FAIL;
    }
    err = esp_ota_begin(part, o->size, handle);
    char *buf = err == ESP_OK ? malloc(4096) : NULL;
    if (err == ESP_OK && !buf) err = ESP_ERR_NO_MEM;
    uint32_t total = 0;
    int n = 0;
    while (err == ESP_OK && (n = esp_http_client_read(client, buf, 4096)) > 0) {
        psa_hash_update(&hash, (const uint8_t *)buf, n);
        err = esp_ota_write(*handle, buf, n);
        total += n;
    }
    free(buf);
    bool complete = esp_http_client_is_complete_data_received(client);
    esp_http_client_cleanup(client);
    size_t dlen = 0;
    psa_status_t ps = psa_hash_finish(&hash, digest, 32, &dlen);
    if (err == ESP_OK && (n < 0 || !complete || total != o->size)) {
        ESP_LOGE(TAG, "download incomplete: %lu of %lu bytes", (unsigned long)total, (unsigned long)o->size);
        err = ESP_ERR_INVALID_SIZE;
    }
    if (err == ESP_OK && (ps != PSA_SUCCESS || dlen != 32)) err = ESP_FAIL;
    return err;
}

static void ota_task(void *arg)
{
    (void)arg;
    const char *running = esp_app_get_description()->version;
    char body[512], req[160];
    ota_offer_t offer;

    /* 1. What is on offer? (the server moves us queued → precheck) */
    snprintf(req, sizeof(req), "{\"mac_address\":\"%s\",\"current_version\":\"%s\"}", s_mac, running);
    int status = http_post_api("/api/device/firmware/check", req, body, sizeof(body));
    if (status != 200 || ota_parse_check(body, &offer) != 0 || !offer.available) {
        ESP_LOGI(TAG, "No usable update on offer (HTTP %d)", status);
        goto done;
    }
    ESP_LOGI(TAG, "Update offered: %s → %s (%lu bytes, deployment %d)", running, offer.version,
             (unsigned long)offer.size, offer.deployment_id);

    const esp_partition_t *part = esp_ota_get_next_update_partition(NULL);
    if (!part || offer.size > part->size) {
        fail(offer.version, ESP_ERR_INVALID_SIZE, "image does not fit the OTA slot");
        goto done;
    }

    /* 2. Download while hashing (the server marks us downloading). */
    esp_ota_handle_t handle = 0;
    uint8_t digest[32];
    esp_err_t err = download(&offer, part, &handle, digest);
    if (err != ESP_OK) {
        if (handle) esp_ota_abort(handle);
        fail(offer.version, err, "download");
        goto done;
    }

    /* 3. Verify: the backend's SHA-256, then the image itself. */
    report("verifying", offer.version, ESP_OK, NULL);
    if (!ota_digest_matches(digest, offer.sha256)) {
        esp_ota_abort(handle);
        fail(offer.version, ESP_ERR_INVALID_CRC, "SHA-256 mismatch");
        goto done;
    }
    err = esp_ota_end(handle);              /* chip id, segments, appended SHA-256 */
    if (err != ESP_OK) {
        fail(offer.version, err, "image verification");
        goto done;
    }

    /* 4. Install: make it the boot image. */
    report("installing", offer.version, ESP_OK, NULL);
    err = esp_ota_set_boot_partition(part);
    if (err != ESP_OK) {
        fail(offer.version, err, "set boot partition");
        goto done;
    }

    /* 5. Reboot. Success is reported by the new image (ota_c6_boot_check). */
    remember_target(offer.version);
    report("rebooting", offer.version, ESP_OK, NULL);
    vTaskDelay(pdMS_TO_TICKS(500));
    esp_restart();

done:
    s_running = false;
    vTaskDelete(NULL);
}

void ota_c6_set_mac(const char *mac)
{
    snprintf(s_mac, sizeof(s_mac), "%s", mac);
}

bool ota_c6_start(void)
{
    if (s_running) return false;
    if (!s_mac[0]) {
        ESP_LOGW(TAG, "OTA requested before the MAC is known");
        return false;
    }
    s_running = true;
    if (xTaskCreate(ota_task, "c6_ota", 8192, NULL, 4, NULL) != pdPASS) {
        s_running = false;
        return false;
    }
    return true;
}

bool ota_c6_in_progress(void)
{
    return s_running;
}

/* ── After boot ──────────────────────────────────────────────────── */

static void health_watchdog(void *arg)
{
    (void)arg;
    vTaskDelay(pdMS_TO_TICKS(HEALTH_TIMEOUT_MS));
    esp_ota_img_states_t st;
    if (esp_ota_get_state_partition(esp_ota_get_running_partition(), &st) == ESP_OK
        && st == ESP_OTA_IMG_PENDING_VERIFY) {
        ESP_LOGE(TAG, "New image not healthy after %d s: rebooting into the previous one",
                 HEALTH_TIMEOUT_MS / 1000);
        esp_restart();                      /* the bootloader rolls back an unconfirmed image */
    }
    vTaskDelete(NULL);
}

void ota_c6_boot_check(bool healthy)
{
    const char *running = esp_app_get_description()->version;
    esp_ota_img_states_t st;
    bool pending = esp_ota_get_state_partition(esp_ota_get_running_partition(), &st) == ESP_OK
                   && st == ESP_OTA_IMG_PENDING_VERIFY;

    char target[32] = "";
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
        size_t len = sizeof(target);
        if (nvs_get_str(h, OTA_NVS_KEY, target, &len) != ESP_OK) target[0] = '\0';
        nvs_close(h);
    }

    if (pending) {
        if (!healthy) {
            /* Wi-Fi / backend not up yet: give it HEALTH_TIMEOUT_MS, then revert. */
            xTaskCreate(health_watchdog, "ota_health", 3072, NULL, 3, NULL);
            return;
        }
        report("health_check", running, ESP_OK, NULL);
        esp_ota_mark_app_valid_cancel_rollback();
        ESP_LOGI(TAG, "Image %s confirmed: rollback cancelled", running);
        report("success", running, ESP_OK, NULL);
        remember_target(NULL);
    } else if (target[0]) {
        if (strcmp(target, running) != 0) {
            /* We set `target` before rebooting, but the old image runs: the
             * bootloader reverted an image that failed its health check. */
            ESP_LOGW(TAG, "Update to %s was rolled back; running %s", target, running);
            report("rolled_back", target, ESP_OK, "bootloader reverted the image");
        }
        remember_target(NULL);
    }
}
