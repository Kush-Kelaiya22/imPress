/**
 * @file config.c
 * @brief S3 runtime configuration — NVS persistence with Kconfig fallback.
 */

#include "config.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include <string.h>

static const char *TAG = "s3_cfg";

s3_config_t g_cfg;

/* ── NVS string helpers ── */

static void _nvs_read_str(nvs_handle_t h, const char *key, char *out, size_t max)
{
    size_t len = max;
    if (nvs_get_str(h, key, out, &len) != ESP_OK) {
        out[0] = '\0';
    }
}

/* ── Public API ── */

void init_nvs_config(void)
{
    /* Runs before mesh_master_init() (which needs g_cfg.mesh_channel), so it
     * owns NVS init; a later nvs_flash_init() there is a no-op (ESP_OK). */
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    nvs_handle_t h;
    err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &h);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS open failed — using Kconfig defaults");
        goto use_defaults;
    }

    uint8_t init_done = 0;
    err = nvs_get_u8(h, NVS_KEY_INIT, &init_done);
    if (err != ESP_OK || !init_done) {
        ESP_LOGI(TAG, "First boot — writing Kconfig defaults to NVS");
        nvs_close(h);
        /* Write defaults */
        err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h);
        if (err != ESP_OK) goto use_defaults;

        nvs_set_str(h, "wifi_ssid",    CONFIG_WIFI_SSID);
        nvs_set_str(h, "wifi_pass",    CONFIG_WIFI_PASSWORD);
        nvs_set_str(h, "backend_host", CONFIG_BACKEND_HOST);
        nvs_set_i32(h, "backend_port", CONFIG_BACKEND_PORT);
        nvs_set_str(h, "api_key",      CONFIG_DEVICE_API_KEY);
        nvs_set_i32(h, "class_id",     0);
        nvs_set_u8(h,  NVS_KEY_INIT,  1);
        nvs_commit(h);
        /* Re-read */
        nvs_close(h);
        err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &h);
        if (err != ESP_OK) goto use_defaults;
    }

    /* Populate g_cfg from NVS */
    _nvs_read_str(h, "wifi_ssid",    g_cfg.wifi_ssid,    NVS_KEY_SSID_LEN);
    _nvs_read_str(h, "wifi_pass",    g_cfg.wifi_pass,    NVS_KEY_PASS_LEN);
    _nvs_read_str(h, "backend_host", g_cfg.backend_host, NVS_KEY_HOST_LEN);
    _nvs_read_str(h, "api_key",      g_cfg.api_key,      NVS_KEY_KEY_LEN);
    snprintf(g_cfg.prov_key, sizeof(g_cfg.prov_key), "%s", g_cfg.api_key);
    {
        char dev_key[NVS_KEY_KEY_LEN] = "";
        _nvs_read_str(h, "dev_key", dev_key, NVS_KEY_KEY_LEN);
        if (dev_key[0]) snprintf(g_cfg.api_key, sizeof(g_cfg.api_key), "%s", dev_key);
    }

    int32_t port = CONFIG_BACKEND_PORT;
    nvs_get_i32(h, "backend_port", &port);
    g_cfg.backend_port = (uint16_t)port;

    int32_t cid = 0;
    nvs_get_i32(h, "class_id", &cid);
    g_cfg.class_id = cid;

    nvs_close(h);
    ESP_LOGI(TAG, "NVS config loaded: host=%s:%d class_id=%ld",
             g_cfg.backend_host, g_cfg.backend_port, (long)g_cfg.class_id);
    goto apply_kconfig;

use_defaults:
    snprintf(g_cfg.wifi_ssid,    sizeof(g_cfg.wifi_ssid),    "%s", CONFIG_WIFI_SSID);
    snprintf(g_cfg.wifi_pass,    sizeof(g_cfg.wifi_pass),    "%s", CONFIG_WIFI_PASSWORD);
    snprintf(g_cfg.backend_host, sizeof(g_cfg.backend_host), "%s", CONFIG_BACKEND_HOST);
    g_cfg.backend_port = CONFIG_BACKEND_PORT;
    snprintf(g_cfg.api_key,      sizeof(g_cfg.api_key),      "%s", CONFIG_DEVICE_API_KEY);
    snprintf(g_cfg.prov_key,     sizeof(g_cfg.prov_key),     "%s", CONFIG_DEVICE_API_KEY);
    g_cfg.class_id = 0;

apply_kconfig:
    /* Timing always comes from Kconfig (no NVS override) */
    g_cfg.hb_interval_ms      = CONFIG_HEARTBEAT_INTERVAL_MS;
    g_cfg.student_timeout_ms  = CONFIG_STUDENT_TIMEOUT_MS;
    g_cfg.spi_poll_interval_ms = CONFIG_SPI_POLL_INTERVAL_MS;
    g_cfg.mesh_channel        = CONFIG_MESH_WIFI_CHANNEL;
}

void nvs_save_class_id(int32_t class_id)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        return;
    }
    nvs_set_i32(h, "class_id", class_id);
    nvs_commit(h);
    nvs_close(h);
    g_cfg.class_id = class_id;
    ESP_LOGI(TAG, "Class ID saved to NVS: %ld", (long)class_id);
}

/* ── Per-device key (#66) ───────────────────────────────────────────── */

static void _store_dev_key(const char *key)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) return;
    nvs_set_str(h, "dev_key", key);
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

