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

static void _nvs_write_str(nvs_handle_t h, const char *key, const char *val)
{
    if (val && val[0]) {
        nvs_set_str(h, key, val);
    }
}

/* ── Public API ── */

void init_nvs_config(void)
{
    /* NVS is already initialised by mesh_master_init(); we just open it. */
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &h);
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
