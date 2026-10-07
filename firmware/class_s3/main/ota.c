/**
 * @file ota.c
 * @brief OTA module for the S3 class hub — temporary WiFi hop.
 *
 * The S3 normally runs ESP-NOW mesh + SPI master and is OFF WiFi.
 * When the C6 relays a MSG_OTA_PROMPT over SPI, we:
 *   1. spawn an OTA task (mesh + SPI keep running during WiFi attach),
 *   2. start WiFi STA using g_cfg credentials,
 *   3. register + heartbeat with the backend,
 *   4. GET /api/device/register + /firmware/check, then /firmware/download,
 *   5. stream the .bin into the inactive OTA partition,
 *   6. set the boot partition and restart.
 *
 * After restart the S3 boots normally into mesh + SPI master role with
 * the new firmware; settings survive in NVS.
 */

#include "ota.h"
#include "config.h"
#include "spi_master.h"
#include "mesh_master.h"
#include "protocol.h"

#include <string.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_ota_ops.h"
#include "esp_efuse.h"
#include "esp_mac.h"

static const char *TAG = "s3_ota";

static EventGroupHandle_t s_wifi_events;
static volatile bool     s_ota_in_progress = false;
static volatile bool     s_ota_ackd        = false;

/* ── WiFi (OTA hop) ───────────────────────────────────────────────── */

static void _wifi_event_handler(void *arg, esp_event_base_t ev, int32_t id,
                                void *data)
{
    (void)arg;
    if (ev == WIFI_EVENT) {
        switch (id) {
        case WIFI_EVENT_STA_START:
            esp_wifi_connect();
            break;
        case WIFI_EVENT_STA_DISCONNECTED:
            ESP_LOGW(TAG, "OTA WiFi disconnected — retrying");
            xEventGroupClearBits(s_wifi_events, WIFI_CONNECTED_BIT);
            esp_wifi_connect();
            break;
        default:
            break;
        }
    } else if (ev == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(s_wifi_events, WIFI_CONNECTED_BIT);
        xEventGroupClearBits(s_wifi_events, WIFI_FAIL_BIT);
        ESP_LOGI(TAG, "OTA WiFi: got IP");
    }
}

static bool _wifi_attach(void)
{
    s_wifi_events = xEventGroupCreate();

    wifi_config_t cfg = {
        .sta = { .threshold.authmode = WIFI_AUTH_WPA2_PSK },
    };
    /* Bounded copy — SSID max is 32 bytes, password up to 63.
     * strlcpy always NUL-terminates, preventing format-truncation warnings. */
    strlcpy((char *)cfg.sta.ssid, g_cfg.wifi_ssid, sizeof(cfg.sta.ssid));
    strlcpy((char *)cfg.sta.password, g_cfg.wifi_pass, sizeof(cfg.sta.password));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, _wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, _wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &cfg));

    /* mesh_master_init() may have already started WiFi for ESP-NOW.
     * Only call esp_wifi_start() if it isn't up yet. */
    wifi_mode_t mode;
    if (esp_wifi_get_mode(&mode) != ESP_OK || mode == WIFI_MODE_NULL) {
        ESP_ERROR_CHECK(esp_wifi_start());
    } else {
        ESP_LOGI(TAG, "WiFi already started (ESP-NOW) — reconfiguring for OTA");
        esp_wifi_connect();
    }

    ESP_LOGI(TAG, "OTA: connecting to WiFi '%s' ...", g_cfg.wifi_ssid);

    EventBits_t bits = xEventGroupWaitBits(
        s_wifi_events, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
        pdFALSE, pdFALSE, pdMS_TO_TICKS(20000));
    return (bits & WIFI_CONNECTED_BIT) != 0;
}

/* ── Backend helpers ──────────────────────────────────────────────── */

static void _url(char *buf, size_t sz, const char *path)
{
    snprintf(buf, sz, "http://%s:%u%s", g_cfg.backend_host,
             g_cfg.backend_port, path);
}

static void _get_mac(char *out, size_t sz)
{
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);
    snprintf(out, sz, "%02x%02x%02x%02x%02x%02x",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static int _http_post(const char *url, const char *json)
{
    char resp_buf[512];
    esp_http_client_config_t config = {
        .url        = url,
        .method     = HTTP_METHOD_POST,
        .timeout_ms = 10000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) return 0;

    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_header(client, "X-API-Key", g_cfg.api_key);

    int status = 0;
    esp_err_t err = esp_http_client_open(client, strlen(json));
    if (err == ESP_OK) {
        int wlen = esp_http_client_write(client, json, strlen(json));
        if (wlen > 0) {
            esp_http_client_fetch_headers(client);
            while (esp_http_client_read(client, resp_buf, sizeof(resp_buf) - 1) > 0) {
            }
            status = esp_http_client_get_status_code(client);
        }
        esp_http_client_close(client);
    }
    esp_http_client_cleanup(client);
    return status;
}

/** POST /firmware/check — returns 1 if an update is pending, 0 otherwise. */
static int _firmware_check(const char *mac, const char *cur_version,
                           char *version_out, size_t version_sz)
{
    char url[256];
    _url(url, sizeof(url), "/api/device/firmware/check");

    char json[256];
    snprintf(json, sizeof(json),
             "{\"mac_address\":\"%s\",\"current_version\":\"%s\"}",
             mac, cur_version);

    char body[512] = {0};
    esp_http_client_config_t config = {
        .url        = url,
        .method     = HTTP_METHOD_POST,
        .timeout_ms = 10000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) return 0;

    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_header(client, "X-API-Key", g_cfg.api_key);

    int update_available = 0;
    esp_err_t err = esp_http_client_open(client, strlen(json));
    if (err == ESP_OK) {
        int wlen = esp_http_client_write(client, json, strlen(json));
        if (wlen > 0) {
            int status = esp_http_client_fetch_headers(client);
            if (status >= 200 && status < 300) {
                int total = 0;
                int n;
                while ((n = esp_http_client_read(client, body + total,
                                                 sizeof(body) - 1 - total)) > 0) {
                    total += n;
                }
                body[total] = '\0';
                /* Look for "update_available":true and "version":"..." */
                if (strstr(body, "\"update_available\":true")) {
                    update_available = 1;
                    const char *v = strstr(body, "\"version\":\"");
                    if (v && version_out) {
                        v += strlen("\"version\":\"");
                        int i = 0;
                        while (v[i] && v[i] != '"' && i < (int)version_sz - 1) {
                            version_out[i] = v[i];
                            i++;
                        }
                        version_out[i] = '\0';
                    }
                }
            }
        }
        esp_http_client_close(client);
    }
    esp_http_client_cleanup(client);
    return update_available;
}

/* ── OTA apply ────────────────────────────────────────────────────── */

static esp_err_t _download_and_apply(const char *mac, const char *version)
{
    char url[320];
    _url(url, sizeof(url), "/api/device/firmware/download");
    /* Append query params */
    char full_url[400];
    snprintf(full_url, sizeof(full_url), "%s?mac_address=%s&version=%s",
             url, mac, version);

    esp_http_client_config_t config = {
        .url        = full_url,
        .method     = HTTP_METHOD_GET,
        .timeout_ms = 60000,
        .buffer_size = 8192,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) return ESP_FAIL;
    esp_http_client_set_header(client, "X-API-Key", g_cfg.api_key);

    /* Get partition info */
    const esp_partition_t *update_part = esp_ota_get_next_update_partition(NULL);
    if (!update_part) {
        esp_http_client_cleanup(client);
        ESP_LOGE(TAG, "No OTA partition available");
        return ESP_ERR_NOT_FOUND;
    }
    ESP_LOGI(TAG, "OTA target: %s @ 0x%lx", update_part->label,
             (unsigned long)update_part->address);

    esp_ota_handle_t ota_handle = 0;
    esp_err_t ret = esp_ota_begin(update_part, OTA_SIZE_UNKNOWN, &ota_handle);
    if (ret != ESP_OK) {
        esp_http_client_cleanup(client);
        return ret;
    }

    char *buf = malloc(8192);
    if (!buf) {
        esp_ota_abort(ota_handle);
        esp_http_client_cleanup(client);
        return ESP_ERR_NO_MEM;
    }

    esp_err_t err = esp_http_client_open(client, 0);
    if (err != ESP_OK) {
        free(buf);
        esp_ota_abort(ota_handle);
        esp_http_client_cleanup(client);
        return err;
    }

    esp_http_client_fetch_headers(client);
    int total = 0;
    int n;
    while ((n = esp_http_client_read(client, buf, 8192)) > 0) {
        ret = esp_ota_write(ota_handle, buf, n);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "esp_ota_write failed: %s", esp_err_to_name(ret));
            free(buf);
            esp_ota_abort(ota_handle);
            esp_http_client_cleanup(client);
            return ret;
        }
        total += n;
    }

    free(buf);
    esp_http_client_cleanup(client);

    /* The download endpoint is HTTP (no TLS for LAN) — esp_ota_end still needs
     * to run before we commit the boot partition. */
    ret = esp_ota_end(ota_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_ota_end failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_ota_set_boot_partition(update_part);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_ota_set_boot_partition failed: %s",
                 esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "OTA complete: %d bytes, reboot into new firmware", total);
    return ESP_OK;
}

/* ── Public API ───────────────────────────────────────────────────── */

bool ota_in_progress(void)
{
    return s_ota_in_progress;
}

void ota_mark_ackd(void)
{
    s_ota_ackd = true;
}

static void _ota_task(void *arg)
{
    (void)arg;
    s_ota_in_progress = true;
    s_ota_ackd        = false;

    char mac[16];
    _get_mac(mac, sizeof(mac));

    /* 1. Attach to classroom WiFi */
    if (!_wifi_attach()) {
        ESP_LOGE(TAG, "OTA aborted — could not connect to WiFi; rebooting to mesh");
        s_ota_in_progress = false;
        vTaskDelay(pdMS_TO_TICKS(500));
        esp_restart();  /* cleanly rebuild ESP-NOW mesh state */
        return;
    }

    /* 2. Register + heartbeat (so backend knows we're briefly online) */
    char reg_url[256];
    _url(reg_url, sizeof(reg_url), "/api/device/register");
    char reg[256];
    snprintf(reg, sizeof(reg),
             "{\"mac_address\":\"%s\",\"device_type\":\"%s\","
             "\"device_name\":\"imPress S3\",\"firmware_version\":\"%s\"}",
             mac, DEVICE_TYPE, FIRMWARE_VERSION);
    _http_post(reg_url, reg);

    char hb_url[256];
    _url(hb_url, sizeof(hb_url), "/api/device/heartbeat");
    char hb[256];
    snprintf(hb, sizeof(hb),
             "{\"mac_address\":\"%s\",\"battery_pct\":100,\"rssi\":0,"
             "\"firmware_version\":\"%s\",\"student_count\":%d}",
             mac, FIRMWARE_VERSION, mesh_master_get_student_count());
    _http_post(hb_url, hb);

    /* 3. Check for pending update */
    char target_version[32] = "";
    if (!_firmware_check(mac, FIRMWARE_VERSION, target_version,
                         sizeof(target_version))) {
        ESP_LOGI(TAG, "No pending update — rebooting back to mesh duty");
        s_ota_in_progress = false;
        vTaskDelay(pdMS_TO_TICKS(500));
        esp_restart();
        return;
    }

    ESP_LOGI(TAG, "Update pending: %s → %s", FIRMWARE_VERSION, target_version);

    /* 4. Download + apply */
    esp_err_t ret = _download_and_apply(mac, target_version);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "OTA failed: %s; rebooting to mesh duty",
                 esp_err_to_name(ret));
        s_ota_in_progress = false;
        vTaskDelay(pdMS_TO_TICKS(500));
        esp_restart();
        return;
    }

    /* 5. Tell C6 so it can relay firmware/applied to the server. */
    payload_ota_prompt_t ack;
    memset(&ack, 0, sizeof(ack));
    snprintf(ack.version, sizeof(ack.version), "%s", target_version);
    /* MSG_OTA_APPLIED is a final ACK signal back to the C6 */
    uint8_t encoded[MSG_MAX_SIZE];
    int len = msg_encode(MSG_OTA_APPLIED, (const uint8_t *)&ack, sizeof(ack),
                         encoded, sizeof(encoded));
    if (len > 0) {
        spi_master_send(encoded, len);
    }

    /* 6. Short delay for the C6 to pick up the ACK, then reboot. */
    vTaskDelay(pdMS_TO_TICKS(1500));
    ESP_LOGI(TAG, "Rebooting into new firmware ...");
    esp_restart();
}

bool ota_start(const char *version, const char *token)
{
    if (s_ota_in_progress) {
        ESP_LOGW(TAG, "OTA already in progress");
        return false;
    }
    (void)version;
    (void)token;
    BaseType_t ok = xTaskCreate(_ota_task, "s3_ota", 8192, NULL, 5, NULL);
    return ok == pdPASS;
}