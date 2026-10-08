/**
 * @file config.c
 * @brief C6 runtime configuration — NVS persistence with Kconfig fallback.
 */

#include "config.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include <string.h>

static const char *TAG = "c6_cfg";

c6_config_t g_cfg;

/* Helper: overlay an NVS string onto a caller buffer that holds the default.
 * Missing, empty (len counts the NUL, so 1 = "") or oversized values leave the
 * default untouched — check BEFORE copying, or an empty value wipes it. */
static void _read_str(nvs_handle_t h, const char *key, char *buf, size_t sz)
{
    size_t len = 0;
    if (nvs_get_str(h, key, NULL, &len) != ESP_OK || len <= 1 || len > sz) {
        return;
    }
    nvs_get_str(h, key, buf, &sz);
    ESP_LOGD(TAG, "NVS %s = %s", key, buf);
}

void init_nvs_config(void)
{
    /* Start from compile-time defaults. */
    snprintf(g_cfg.wifi_ssid, sizeof(g_cfg.wifi_ssid), "%s", CFG_WIFI_SSID);
    snprintf(g_cfg.wifi_pass, sizeof(g_cfg.wifi_pass), "%s", CFG_WIFI_PASS);
    snprintf(g_cfg.backend_host, sizeof(g_cfg.backend_host), "%s", CFG_BACKEND_HOST);
    g_cfg.backend_port    = CFG_BACKEND_PORT;
    snprintf(g_cfg.api_key, sizeof(g_cfg.api_key), "%s", CFG_API_KEY);
    snprintf(g_cfg.prov_key, sizeof(g_cfg.prov_key), "%s", CFG_API_KEY);
    g_cfg.class_id        = CFG_CLASS_ID;
    g_cfg.hb_interval_s   = CFG_HB_INTERVAL_S;
    g_cfg.ws_ping_s       = CFG_WS_PING_S;
    g_cfg.ping_interval_s = CFG_PING_INTERVAL_S;
    g_cfg.spi_batch_max_ms = CFG_SPI_BATCH_MAX;
    g_cfg.batch_max       = CFG_BATCH_MAX;

    /* NVS must be initialized before we can read/write it. */
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        ESP_LOGE(TAG, "NVS open failed — using defaults");
        return;
    }

    /* First boot: persist the compile-time defaults so later edits stick. */
    uint8_t init_flag = 0;
    if (nvs_get_u8(h, NVS_KEY_INIT, &init_flag) != ESP_OK || init_flag != 1) {
        ESP_LOGI(TAG, "First boot — writing default config to NVS");
        nvs_set_str(h, NVS_KEY_WIFI_SSID, g_cfg.wifi_ssid);
        nvs_set_str(h, NVS_KEY_WIFI_PASS, g_cfg.wifi_pass);
        nvs_set_str(h, NVS_KEY_BACKEND_H, g_cfg.backend_host);
        nvs_set_u16(h, NVS_KEY_BACKEND_P, g_cfg.backend_port);
        nvs_set_str(h, NVS_KEY_API_KEY, g_cfg.api_key);
        nvs_set_i32(h, NVS_KEY_CLASS_ID, g_cfg.class_id);
        nvs_set_u8(h, NVS_KEY_INIT, 1);
        nvs_commit(h);
    }

    /* Overlay persisted values (they win over defaults). */
    _read_str(h, NVS_KEY_WIFI_SSID, g_cfg.wifi_ssid, sizeof(g_cfg.wifi_ssid));
    _read_str(h, NVS_KEY_WIFI_PASS, g_cfg.wifi_pass, sizeof(g_cfg.wifi_pass));
    _read_str(h, NVS_KEY_BACKEND_H, g_cfg.backend_host, sizeof(g_cfg.backend_host));
    uint16_t port = 0;
    if (nvs_get_u16(h, NVS_KEY_BACKEND_P, &port) == ESP_OK && port > 0) {
        g_cfg.backend_port = port;
    }
    _read_str(h, NVS_KEY_API_KEY, g_cfg.api_key, sizeof(g_cfg.api_key));
    snprintf(g_cfg.prov_key, sizeof(g_cfg.prov_key), "%s", g_cfg.api_key);
    char dev_key[NVS_KEY_KEY_LEN] = "";
    _read_str(h, NVS_KEY_DEV_KEY, dev_key, sizeof(dev_key));
    if (dev_key[0]) {
        snprintf(g_cfg.api_key, sizeof(g_cfg.api_key), "%s", dev_key);
    }
    int32_t cid = 0;
    if (nvs_get_i32(h, NVS_KEY_CLASS_ID, &cid) == ESP_OK) {
        g_cfg.class_id = cid;
    }

    /* Diagnostics (#39): a rising count with short uptimes means a reset loop. */
    int32_t boots = 0;
    nvs_get_i32(h, NVS_KEY_BOOT_COUNT, &boots);
    g_cfg.boot_count = (uint32_t)boots + 1;
    nvs_set_i32(h, NVS_KEY_BOOT_COUNT, (int32_t)g_cfg.boot_count);
    nvs_commit(h);

    nvs_close(h);

    ESP_LOGI(TAG, "WiFi: %s  backend: %s:%u  class_id: %ld",
             g_cfg.wifi_ssid, g_cfg.backend_host, g_cfg.backend_port,
             (long)g_cfg.class_id);
}

/**
 * @brief Persist the class ID the backend assigned us (survives reboot).
 */
void nvs_save_class_id(int32_t class_id)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        return;
    }
    nvs_set_i32(h, NVS_KEY_CLASS_ID, class_id);
    nvs_commit(h);
    nvs_close(h);
    g_cfg.class_id = class_id;
    ESP_LOGI(TAG, "Class ID saved to NVS: %ld", (long)class_id);
}

/* ── Per-device key (#66) ───────────────────────────────────────────── */

static void _store_dev_key(const char *key)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        return;
    }
    nvs_set_str(h, NVS_KEY_DEV_KEY, key);
    nvs_commit(h);
    nvs_close(h);
}

void cfg_set_device_key(const char *key)
{
    if (!key || !key[0] || strlen(key) >= sizeof(g_cfg.api_key)) return;
    _store_dev_key(key);
    snprintf(g_cfg.api_key, sizeof(g_cfg.api_key), "%s", key);
    ESP_LOGI(TAG, "Device key stored; it replaces the shared key");
}

void cfg_clear_device_key(void)
{
    _store_dev_key("");
    snprintf(g_cfg.api_key, sizeof(g_cfg.api_key), "%s", g_cfg.prov_key);
    ESP_LOGW(TAG, "Device key refused by the backend: back to the shared key");
}

bool cfg_has_device_key(void)
{
    return g_cfg.prov_key[0] && strcmp(g_cfg.api_key, g_cfg.prov_key) != 0;
}

