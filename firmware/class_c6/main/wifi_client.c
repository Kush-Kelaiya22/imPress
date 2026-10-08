/**
 * @file wifi_client.c
 * @brief WiFi + HTTP client for the C6 gateway (production).
 *
 * Credentials and backend addressing come from g_cfg (Kconfig + NVS override).
 * Telemetry in heartbeats is real: RSSI, free heap, total flash, battery ADC.
 */

#include "wifi_client.h"
#include "config.h"
#include "backend_tls.h"   /* http(s)/ws(s) and the server certificate (#66) */
#include "protocol.h"     /* json_get_string */
#include "esp_adc/adc_oneshot.h"

#include <string.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "esp_system.h"
#if CONFIG_BATTERY_ADC_EN
#include "esp_adc/adc_oneshot.h"
#endif
#include "nvs_flash.h"

static const char *TAG = "wifi";

static EventGroupHandle_t s_wifi_events;
static char s_ip_str[16] = "";

/* ── WiFi Event Handlers ───────────────────────────────────────────── */

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    (void)arg;
    if (event_base == WIFI_EVENT) {
        switch (event_id) {
        case WIFI_EVENT_STA_START:
            esp_wifi_connect();
            break;
        case WIFI_EVENT_STA_DISCONNECTED:
            ESP_LOGW(TAG, "WiFi disconnected — retrying");
            xEventGroupClearBits(s_wifi_events, WIFI_CONNECTED_BIT);
            esp_wifi_connect();
            break;
        default:
            break;
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *e = (ip_event_got_ip_t *)event_data;
        snprintf(s_ip_str, sizeof(s_ip_str), IPSTR, IP2STR(&e->ip_info.ip));
        ESP_LOGI(TAG, "Got IP: %s", s_ip_str);
        xEventGroupSetBits(s_wifi_events, WIFI_CONNECTED_BIT);
        xEventGroupClearBits(s_wifi_events, WIFI_FAIL_BIT);
    }
}

int wifi_client_init(void)
{
    s_wifi_events = xEventGroupCreate();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t err;

    err = esp_netif_init();
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) return -1;
    err = esp_event_loop_create_default();
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) return -1;

    esp_netif_create_default_wifi_sta();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL, NULL));

    wifi_config_t wifi_config = {
        .sta = {
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    /* Bounded copy — SSID max is 32 bytes, password up to 63. */
    strlcpy((char *)wifi_config.sta.ssid, g_cfg.wifi_ssid,
            sizeof(wifi_config.sta.ssid));
    strlcpy((char *)wifi_config.sta.password, g_cfg.wifi_pass,
            sizeof(wifi_config.sta.password));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "WiFi connecting to %s ...", g_cfg.wifi_ssid);
    return 0;
}

bool wifi_client_wait_connected(uint32_t timeout_ms)
{
    EventBits_t bits = xEventGroupWaitBits(s_wifi_events,
                                           WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(timeout_ms));
    return (bits & WIFI_CONNECTED_BIT) != 0;
}

bool wifi_client_is_connected(void)
{
    return (xEventGroupGetBits(s_wifi_events) & WIFI_CONNECTED_BIT) != 0;
}

const char *wifi_client_get_ip(void)
{
    return s_ip_str;
}

/* ── Backend URL builders ──────────────────────────────────────────── */

static void _url(char *buf, size_t sz, const char *path)
{
    snprintf(buf, sz, BACKEND_HTTP_SCHEME "://%s:%u%s", g_cfg.backend_host, g_cfg.backend_port, path);
}

/* ── Real telemetry ────────────────────────────────────────────────── */

static int s_adc_ready = 0;
static adc_oneshot_unit_handle_t s_adc;

static int _battery_pct(void)
{
#if CONFIG_BATTERY_ADC_EN
    if (!s_adc_ready) {
        adc_oneshot_unit_init_cfg_t init = {
            .unit_id = ADC_UNIT_1,
            .ulp_mode = ADC_ULP_MODE_DISABLE,
        };
        if (adc_oneshot_new_unit(&init, &s_adc) == ESP_OK) {
            adc_oneshot_chan_cfg_t c = {
                .atten = ADC_ATTEN_DB_11,
                .bitwidth = ADC_BITWIDTH_12,
            };
            adc_oneshot_config_channel(s_adc, CONFIG_BATTERY_ADC_GPIO, &c);
            s_adc_ready = 1;
        }
    }
    if (s_adc_ready) {
        int raw = 0;
        if (adc_oneshot_read(s_adc, CONFIG_BATTERY_ADC_GPIO, &raw) == ESP_OK) {
            /* Map raw ADC (12-bit) to a 0-100% estimate. Calibrate per board. */
            int pct = (raw * 100) / 4095;
            if (pct < 0) pct = 0;
            if (pct > 100) pct = 100;
            return pct;
        }
    }
#endif
    return 100; /* no battery monitor wired — report full */
}

/* ── HTTP Helper ───────────────────────────────────────────────────── */

/* Set when the backend refused this device's own key (#66): it was reset by
 * an admin. The key is dropped at once; the heartbeat task re-registers. */
static volatile bool s_reregister;

bool http_reregister_pending(void)
{
    return s_reregister;
}

static void _check_auth(int status)
{
    if (status == 401 && cfg_has_device_key()) {
        cfg_clear_device_key();
        s_reregister = true;
    }
}

static int _http_post_body(const char *url, const char *json,
                           char *out, size_t out_size)
{
    /* Read buffer; body copied into out when requested, else drained. */
    char resp_buf[256];
    size_t out_len = 0;
    int r = 0;
    if (out && out_size > 0) out[0] = '\0';

    esp_http_client_config_t config = {
        .url = url,
        .method = HTTP_METHOD_POST,
        .timeout_ms = 10000,
    };

    BACKEND_TLS_APPLY(config);

    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) return 0;

    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_header(client, "X-API-Key", g_cfg.api_key);

    int status = 0;
    esp_err_t err = esp_http_client_open(client, strlen(json));
    if (err == ESP_OK) {
        int wlen = esp_http_client_write(client, json, strlen(json));
        if (wlen > 0) {
            /* Force the response through so the status code becomes valid. */
            esp_http_client_fetch_headers(client);
            while ((r = esp_http_client_read(client, resp_buf, sizeof(resp_buf) - 1)) > 0) {
                if (out && out_size > 0) {
                    for (int i = 0; i < r && out_len + 1 < out_size; i++) {
                        out[out_len++] = resp_buf[i];
                    }
                    out[out_len] = '\0';
                }
            }
            status = esp_http_client_get_status_code(client);
        } else {
            ESP_LOGW(TAG, "HTTP write failed (wlen=%d)", wlen);
        }
        esp_http_client_close(client);
    } else {
        ESP_LOGW(TAG, "HTTP POST failed: %s", esp_err_to_name(err));
    }
    esp_http_client_cleanup(client);
    _check_auth(status);
    return status;
}

static int _http_post(const char *url, const char *json)
{
    return _http_post_body(url, json, NULL, 0);
}

/* ── HTTP API Calls ────────────────────────────────────────────────── */

int http_post_json(const char *url, const char *json)
{
    return _http_post(url, json);
}

int http_register_device(const char *mac_address, const char *device_type)
{
    char url[256];
    _url(url, sizeof(url), "/api/device/register");
    char json[256];
    snprintf(json, sizeof(json),
             "{\"mac_address\":\"%s\",\"device_type\":\"%s\","
             "\"device_name\":\"imPress C6\",\"firmware_version\":\"%s\"}",
             mac_address, device_type, FIRMWARE_VERSION);

    char resp[320];
    int status = _http_post_body(url, json, resp, sizeof(resp));
    if (status == 401 && !cfg_has_device_key()) {
        /* _check_auth just dropped a reset device key: register with the
         * shared key now, which issues a new one. */
        status = _http_post_body(url, json, resp, sizeof(resp));
    }

    /* The backend auto-links this gateway to a class (R6) and returns
     * {"device_id":N,"status":"registered","class_id":N|null}. Adopt the
     * class_id so the WebSocket can open. */
    if (status == 200) {
        s_reregister = false;
        /* Registering with the shared key issues this device its own key
         * (#66); from now on every request sends it instead. */
        char key[sizeof(g_cfg.api_key)];
        if (json_get_string(resp, "device_key", key, sizeof(key)) > 0) {
            cfg_set_device_key(key);
        }
        char *p = strstr(resp, "\"class_id\"");
        if (p) {
            p = strchr(p, ':');
            if (p) {
                long cid = strtol(p + 1, NULL, 10);  /* "null" → 0 */
                if (cid > 0 && cid != (long)g_cfg.class_id) {
                    g_cfg.class_id = (int32_t)cid;
                    nvs_save_class_id(g_cfg.class_id);
                    ESP_LOGI(TAG, "Adopted class_id %ld from register", cid);
                }
            }
        }
    }
    return status;
}

/* esp_reset_reason() as the backend's health rules name it (#39). */
static const char *_reset_reason(void)
{
    switch (esp_reset_reason()) {
    case ESP_RST_POWERON:   return "poweron";
    case ESP_RST_EXT:       return "external";
    case ESP_RST_SW:        return "software";      /* esp_restart(): OTA, config change */
    case ESP_RST_PANIC:     return "panic";
    case ESP_RST_INT_WDT:   return "int_wdt";
    case ESP_RST_TASK_WDT:  return "task_wdt";
    case ESP_RST_WDT:       return "wdt";
    case ESP_RST_DEEPSLEEP: return "deepsleep";
    case ESP_RST_BROWNOUT:  return "brownout";
    default:                return "other";
    }
}

int http_send_heartbeat(const char *mac, int student_count, bool s3_link_ok, uint32_t s3_uptime_s)
{
    char url[256];
    _url(url, sizeof(url), "/api/device/heartbeat");
    char json[512];
    /* Real telemetry: RSSI from WiFi, free heap, total flash, battery ADC. */
    int rssi = 0;
    wifi_ap_record_t ap;
    if (esp_wifi_sta_get_ap_info(&ap) == ESP_OK) {
        rssi = ap.rssi;
    }
    size_t free_heap = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    size_t total_heap = heap_caps_get_total_size(MALLOC_CAP_8BIT);
    int battery = _battery_pct();

    /* Diagnostics (#39) */
    uint32_t uptime_s = (uint32_t)(esp_timer_get_time() / 1000000ULL);
    size_t min_free = heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT);

    snprintf(json, sizeof(json),
             "{\"mac_address\":\"%s\",\"battery_pct\":%d,\"rssi\":%d,"
             "\"firmware_version\":\"%s\",\"student_count\":%d,"
             "\"free_heap\":%u,\"total_flash\":%u,"
             "\"uptime_s\":%u,\"reset_reason\":\"%s\",\"boot_count\":%u,"
             "\"min_free_heap\":%u,\"s3_link_ok\":%s,\"s3_uptime_s\":%u}",
             mac, battery, rssi, FIRMWARE_VERSION, student_count,
             (unsigned)free_heap, (unsigned)total_heap,
             (unsigned)uptime_s, _reset_reason(), (unsigned)g_cfg.boot_count,
             (unsigned)min_free, s3_link_ok ? "true" : "false", (unsigned)s3_uptime_s);
    return _http_post(url, json);
}

int http_send_status_ping(const char *mac, int32_t class_id, int student_count)
{
    char url[256];
    _url(url, sizeof(url), "/api/device/ping");
    char json[320];

    int rssi = 0;
    wifi_ap_record_t ap;
    if (esp_wifi_sta_get_ap_info(&ap) == ESP_OK) {
        rssi = ap.rssi;
    }
    size_t free_heap = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    uint32_t uptime_s = (uint32_t)(esp_timer_get_time() / 1000000ULL);

    snprintf(json, sizeof(json),
             "{\"mac_address\":\"%s\",\"class_id\":%ld,\"student_count\":%d,"
             "\"uptime_s\":%u,\"rssi\":%d,\"free_heap\":%u}",
             mac, (long)class_id, student_count,
             (unsigned)uptime_s, rssi, (unsigned)free_heap);
    return _http_post(url, json);
}

int http_send_attendance(const char *enrollment, const char *class_code)
{
    char url[256];
    _url(url, sizeof(url), "/api/device/attendance");
    char json[256];
    snprintf(json, sizeof(json),
             "{\"enrollment_number\":\"%s\",\"class_code\":\"%s\"}",
             enrollment, class_code);
    return _http_post(url, json);
}

int http_post_api(const char *path, const char *json, char *out, size_t out_size)
{
    char url[256];
    _url(url, sizeof(url), path);
    return _http_post_body(url, json, out, out_size);
}

void http_api_url(char *buf, size_t sz, const char *path)
{
    _url(buf, sz, path);
}

int http_send_batch(const char *json)
{
    char url[256];
    _url(url, sizeof(url), "/api/device/batch");
    char buf[HTTP_BUF_SIZE];
    snprintf(buf, sizeof(buf),
             "{\"device_type\":\"c6\",\"messages\":%s}",
             json);
    return _http_post(url, buf);
}