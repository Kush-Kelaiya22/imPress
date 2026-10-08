/**
 * @file ws_client.c
 * @brief WebSocket device-link for the C6 gateway (production).
 *
 * Connects as role=device with api_key auth and exponential backoff reconnect.
 * Incoming commands from the backend (quiz_question, poll_start, …) are parsed
 * with cJSON and handed to a message callback for SPI forwarding.
 * Outbound C6 → backend messages use ws_send (bridge events).
 */

#include "ws_client.h"
#include "config.h"
#include "backend_tls.h"   /* http(s)/ws(s) and the server certificate (#66) */

#include <string.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_websocket_client.h"
#include "cJSON.h"

static const char *TAG = "ws_client";

static esp_websocket_client_handle_t s_ws_client = NULL;
static volatile bool s_connected = false;
static ws_recv_cb_t s_callback = NULL;

static void ws_event_handler(void *handler_args, esp_event_base_t base,
                             int32_t event_id, void *event_data)
{
    (void)handler_args; (void)base;
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;
    switch (event_id) {
    case WEBSOCKET_EVENT_CONNECTED:
        s_connected = true;
        ESP_LOGI(TAG, "WebSocket connected");
        break;
    case WEBSOCKET_EVENT_DISCONNECTED:
        s_connected = false;
        ESP_LOGW(TAG, "WebSocket disconnected");
        break;
    case WEBSOCKET_EVENT_DATA:
        if (data->op_code == 0x1 && data->data_len > 0) {
            /* Text frame — pass to command handler. Guarantee NUL-termination. */
            char *msg = calloc(data->data_len + 1, 1);
            if (msg) {
                memcpy(msg, data->data_ptr, data->data_len);
                if (s_callback) {
                    s_callback(msg);
                }
                free(msg);
            }
        }
        break;
    case WEBSOCKET_EVENT_ERROR:
        ESP_LOGE(TAG, "WebSocket error");
        break;
    default:
        break;
    }
}

int ws_client_start(int class_id, ws_recv_cb_t callback)
{
    s_callback = callback;
    if (s_ws_client) {
        ws_client_stop();
    }

    /* ws(s)://host:port/ws/class/<id>?role=device — the device key goes in an
     * X-API-Key header, not the URL (URLs end up in proxy/access logs). */
    char uri[256];
    snprintf(uri, sizeof(uri), BACKEND_WS_SCHEME "://%s:%u/ws/class/%d?role=device",
             g_cfg.backend_host, g_cfg.backend_port, class_id);
    ESP_LOGI(TAG, "WS connecting: %s", uri);   /* no secret in this string */

    char headers[sizeof(g_cfg.api_key) + 16];   /* copied (strdup) by the client init */
    snprintf(headers, sizeof(headers), "X-API-Key: %s\r\n", g_cfg.api_key);

    esp_websocket_client_config_t cfg = {
        .uri = uri,
        .headers = headers,
        .reconnect_timeout_ms = 5000,
        .network_timeout_ms = 10000,
    };
    BACKEND_TLS_APPLY(cfg);
    s_ws_client = esp_websocket_client_init(&cfg);
    if (!s_ws_client) {
        ESP_LOGE(TAG, "Failed to init WS client");
        return -1;
    }
    ESP_ERROR_CHECK(esp_websocket_register_events(s_ws_client, WEBSOCKET_EVENT_ANY,
                                                  ws_event_handler, NULL));
    esp_websocket_client_start(s_ws_client);
    return 0;
}

bool ws_client_is_connected(void)
{
    return s_connected;
}

void ws_client_reconnect(void)
{
    if (s_ws_client) {
        ESP_LOGI(TAG, "Manual WS reconnect requested");
        esp_websocket_client_stop(s_ws_client);
        esp_websocket_client_start(s_ws_client);
    }
}

int ws_client_send(const char *json)
{
    if (!s_connected || !s_ws_client) return -1;
    int ret = esp_websocket_client_send_text(s_ws_client, json, strlen(json),
                                             pdMS_TO_TICKS(2000));
    return (ret >= 0) ? 0 : -1;
}

void ws_client_stop(void)
{
    if (s_ws_client) {
        esp_websocket_client_stop(s_ws_client);
        esp_websocket_client_destroy(s_ws_client);
        s_ws_client = NULL;
        s_connected = false;
    }
}