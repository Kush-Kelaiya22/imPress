/**
 * @file main.c
 * @brief C6 class gateway entry point — imPress (production).
 *
 * Boot sequence:
 *   1. NVS config (Kconfig defaults, then NVS overlay)
 *   2. MAC address
 *   3. SPI slave (S3 can begin sending immediately)
 *   4. WiFi connect (exponential backoff)
 *   5. HTTP register, WS connect (?role=device&api_key=...)
 *   6. Steady-state:
 *       - SPI → JSON batch → HTTP POST (student data from S3/mesh)
 *       - WebSocket ↔ SPI (backend commands → SPI → S3 → mesh students)
 *       - Heartbeat with real telemetry
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "driver/gpio.h"
#include "cJSON.h"

#include "config.h"
#include "protocol.h"
#include "spi_slave.h"
#include "wifi_client.h"
#include "ws_client.h"
#include "esp_efuse.h"
#include "esp_mac.h"

static const char *TAG = "c6_main";

/* ── Runtime State ──────────────────────────────────────────────────── */

static char s_mac_str[DEVICE_MAC_STR_LEN] = "";
static volatile bool s_gateway_ready = false;
static volatile int64_t s_boot_time_us = 0;
static volatile int s_student_count = 0;  /* updated from S3 heartbeats */

/* ── Batch Accumulator ──────────────────────────────────────────────── */

#define BATCH_BUF_SIZE  (HTTP_BUF_SIZE - 128)

typedef struct {
    cJSON *items;    /* JSON array being accumulated */
    int64_t last_add_us;
} batch_acc_t;

static batch_acc_t s_batch = {0};

static void batch_init(void)
{
    s_batch.items = cJSON_CreateArray();
    s_batch.last_add_us = esp_timer_get_time();
}

static void batch_add(cJSON *item)
{
    if (!item) return;
    cJSON_AddItemToArray(s_batch.items, item);
    s_batch.last_add_us = esp_timer_get_time();
}

static bool batch_flush_needed(void)
{
    int64_t now = esp_timer_get_time();
    int count = cJSON_GetArraySize(s_batch.items);
    int64_t elapsed_ms = (now - s_batch.last_add_us) / 1000;
    return (count >= (int)g_cfg.batch_max) ||
           (count > 0 && elapsed_ms >= (int64_t)g_cfg.spi_batch_max_ms);
}

static void batch_flush(void)
{
    int count = cJSON_GetArraySize(s_batch.items);
    if (count == 0) return;

    char *json = cJSON_PrintUnformatted(s_batch.items);
    if (json) {
        ESP_LOGI(TAG, "Batch flush %d items → /api/device/batch", count);
        http_send_batch(json);
        free(json);
    }
    cJSON_Delete(s_batch.items);
    s_batch.items = cJSON_CreateArray();
    s_batch.last_add_us = esp_timer_get_time();
}

/* ── Protocol → JSON Conversion ─────────────────────────────────────── */

static cJSON *msg_to_json(msg_type_t type, const uint8_t *payload, uint16_t len,
                          uint32_t sender_device_id)
{
    cJSON *j = NULL;

    switch (type) {
    case MSG_HEARTBEAT: {
        if (len < sizeof(payload_heartbeat_t)) break;
        const payload_heartbeat_t *p = (const payload_heartbeat_t *)payload;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "heartbeat");
        cJSON_AddStringToObject(j, "device_mac", s_mac_str);  /* relay C6 MAC */
        cJSON_AddNumberToObject(j, "device_id", p->device_id);
        cJSON_AddNumberToObject(j, "battery_pct", p->battery_pct);
        cJSON_AddNumberToObject(j, "rssi", p->rssi);
        /* Update student count from S3's reported value */
        s_student_count++;
        break;
    }
    case MSG_STUDENT_JOIN: {
        if (len < sizeof(payload_student_join_t)) break;
        const payload_student_join_t *p = (const payload_student_join_t *)payload;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "student_join");
        /* Enrollment number is the primary identity */
        cJSON_AddStringToObject(j, "enrollment_number", p->enrollment);
        /* This gateway relays the mesh event — used for attribution/student_count */
        cJSON_AddStringToObject(j, "device_mac", s_mac_str);
        cJSON_AddStringToObject(j, "class_code",
            /* class_code will be injected by the batch POST helper */
            "");
        /* Legacy fields kept for diagnostics */
        cJSON_AddNumberToObject(j, "device_id", p->device_id);
        break;
    }
    case MSG_STUDENT_LEAVE: {
        /* Student module went offline (timeout / explicit leave / shutdown).
         * Enrollment number is the primary identity. */
        if (len < sizeof(payload_student_leave_t)) break;
        const payload_student_leave_t *p = (const payload_student_leave_t *)payload;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "student_leave");
        cJSON_AddStringToObject(j, "enrollment_number", p->enrollment);
        cJSON_AddStringToObject(j, "device_mac", s_mac_str);
        cJSON_AddNumberToObject(j, "device_id", p->device_id);
        cJSON_AddNumberToObject(j, "reason", p->reason);
        /* Track mesh population (heartbeat increments per peer) */
        if (s_student_count > 0) s_student_count--;
        break;
    }
    case MSG_QUIZ_ANSWER: {
        if (len < sizeof(payload_quiz_answer_t)) break;
        const payload_quiz_answer_t *p = (const payload_quiz_answer_t *)payload;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "quiz_answer");
        cJSON_AddNumberToObject(j, "quiz_id", p->quiz_id);
        cJSON_AddNumberToObject(j, "question_order", p->question_num);
        /* Primary identity: enrollment number */
        cJSON_AddStringToObject(j, "enrollment_number", p->enrollment);
        cJSON_AddNumberToObject(j, "selected_option", p->selected_option);
        cJSON_AddNumberToObject(j, "response_time_ms", p->response_time_ms);
        cJSON_AddNumberToObject(j, "device_id", p->device_id);  /* diagnostics */
        break;
    }
    case MSG_POLL_VOTE: {
        if (len < sizeof(payload_poll_vote_t)) break;
        const payload_poll_vote_t *p = (const payload_poll_vote_t *)payload;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "poll_vote");
        cJSON_AddNumberToObject(j, "poll_id", p->poll_id);
        /* Primary identity: enrollment number */
        cJSON_AddStringToObject(j, "enrollment_number", p->enrollment);
        cJSON_AddNumberToObject(j, "selected_option", p->selected_option);
        cJSON_AddNumberToObject(j, "device_id", p->device_id);  /* diagnostics */
        break;
    }
    case MSG_ATTENDANCE: {
        /* Attendance check-in: forward enrollment_number to backend */
        /* Payload: 10-byte enrollment string (NUL-padded) */
        if (len < 11) break;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "attendance");
        cJSON_AddStringToObject(j, "enrollment_number", (const char *)payload);
        break;
    }
    case MSG_SPI_STATUS: {
        if (len < 2) break;
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "device_status");
        cJSON_AddNumberToObject(j, "device_id", sender_device_id);
        cJSON_AddNumberToObject(j, "status", payload[0]);
        break;
    }
    default:
        ESP_LOGD(TAG, "Unhandled msg type 0x%02X, skipping", type);
        break;
    }
    return j;
}

/* ── SPI → JSON → Backend Batch ─────────────────────────────────────── */

/**
 * Process a raw SPI payload from the S3.
 *
 * S3 flush format: a sequence of spi_record_* records (see protocol.h),
 *   [FRAME_LEN:2BE][DEVICE_ID:4LE][PROTOCOL_FRAME:FRAME_LEN]
 *
 * Each PROTOCOL_FRAME is a standard binary frame:
 *   [START:0xAA][TYPE:1][LENGTH:2BE][PAYLOAD:N][CRC16:2]
 */
static void process_spi_payload(const uint8_t *buf, int buf_len)
{
    int offset = 0;
    for (;;) {
        uint32_t device_id;
        const uint8_t *frame;
        uint16_t frame_len;
        int n = spi_record_read(buf + offset, buf_len - offset,
                                &device_id, &frame, &frame_len);
        if (n <= 0) break;
        offset += n;

        /* Decode the protocol frame inside */
        msg_t msg;
        int consumed = msg_decode(frame, frame_len, &msg);

        if (consumed <= 0 || consumed > frame_len) continue;

        /* Convert to JSON and add to batch */
        cJSON *j = msg_to_json(msg.type, msg.payload, msg.length, device_id);
        if (j) {
            batch_add(j);
        }
    }

    /* Flush when ready */
    if (batch_flush_needed()) {
        batch_flush();
    }
}

static void spi_to_http_task(void *arg)
{
    (void)arg;
    uint8_t buf[SPI_RX_BUF_SIZE];
    batch_init();

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(50));

        if (!wifi_client_is_connected()) {
            continue;
        }

        int len = spi_slave_read(buf, sizeof(buf));
        if (len > 0) {
            ESP_LOGD(TAG, "SPI data (%d bytes) → batch", len);
            process_spi_payload(buf, len);
        }

        /* Periodic flush check */
        if (batch_flush_needed()) {
            batch_flush();
        }
    }
}

/* ── Heartbeat Task ─────────────────────────────────────────────────── */

static void heartbeat_task(void *arg)
{
    (void)arg;

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(g_cfg.hb_interval_s * 1000));

        if (!wifi_client_is_connected()) continue;

        /* Send heartbeat to backend with real telemetry */
        http_send_heartbeat(s_mac_str, s_student_count);

        /* Send C6's own status to backend */
        cJSON *j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "heartbeat");
        cJSON_AddStringToObject(j, "device_mac", s_mac_str);
        cJSON_AddNumberToObject(j, "battery_pct", 100);  /* C6 is mains-powered */
        batch_add(j);
        if (batch_flush_needed()) {
            batch_flush();
        }
    }
}

/* ── 2-Minute Classroom Status Ping ──────────────────────────────────── */

static void status_ping_task(void *arg)
{
    (void)arg;
    const TickType_t interval = pdMS_TO_TICKS(g_cfg.ping_interval_s * 1000);

    ESP_LOGI(TAG, "Status ping task started (every %u s)",
             (unsigned)g_cfg.ping_interval_s);

    while (1) {
        vTaskDelay(interval);

        if (!wifi_client_is_connected()) continue;

        /* "Give updates every 2 minutes": student count, class_id, uptime,
         * RSSI → backend records a class.status_update + refreshes last_seen. */
        int rc = http_send_status_ping(s_mac_str, g_cfg.class_id, s_student_count);
        ESP_LOGI(TAG, "Status ping → class %ld, %d students, HTTP %d%s",
                 (long)g_cfg.class_id, s_student_count, rc,
                 (rc == 200) ? " OK" : " — retry next interval");
    }
}

/* ── Backend Assigns Class ID ───────────────────────────────────────── */

/* Forward declarations */
static void handle_class_assignment(const cJSON *msg);
static void on_ws_command(const char *json);

static void handle_class_assignment(const cJSON *msg)
{
    const cJSON *cid = cJSON_GetObjectItem(msg, "class_id");
    if (cid && cJSON_IsNumber(cid)) {
        int32_t new_id = (int32_t)cid->valuedouble;
        if (new_id != g_cfg.class_id) {
            ESP_LOGI(TAG, "Backend assigned class_id %ld → saving to NVS", (long)new_id);
            nvs_save_class_id(new_id);
            /* Restart the WS client so it connects to the NEW class URI. */
            ws_client_stop();
            if (new_id > 0) {
                ws_client_start(new_id, on_ws_command);
            }
        }
    }
}

/* ── WebSocket Command Handler ──────────────────────────────────────── */

/**
 * Handles commands from the backend (quiz_question, poll_start, device_command).
 * Parses JSON, forwards as a protocol-encoded frame to S3 via SPI.
 */
static void on_ws_command(const char *json)
{
    ESP_LOGI(TAG, "WS cmd: %s", json);

    cJSON *msg = cJSON_Parse(json);
    if (!msg) {
        ESP_LOGE(TAG, "Bad JSON from WS");
        return;
    }

    const cJSON *event = cJSON_GetObjectItem(msg, "event");
    const char *evt = cJSON_IsString(event) ? event->valuestring : "";

    if (strcmp(evt, "quiz_question") == 0) {
        /* Extract question data and forward as MSG_QUIZ_QUESTION to S3 */
        const cJSON *quiz_id  = cJSON_GetObjectItem(msg, "quiz_id");
        const cJSON *q_num    = cJSON_GetObjectItem(msg, "question_order");
        const cJSON *q_text   = cJSON_GetObjectItem(msg, "question_text");
        const cJSON *options  = cJSON_GetObjectItem(msg, "options");
        const cJSON *time_lim = cJSON_GetObjectItem(msg, "time_limit_s");

        if (quiz_id && q_text && options) {
            payload_quiz_question_t pq = {0};
            pq.quiz_id = (uint16_t)quiz_id->valueint;
            pq.question_num = q_num ? q_num->valueint : 0;
            pq.num_options = cJSON_GetArraySize(options);
            pq.time_limit_s = time_lim ? (uint32_t)time_lim->valueint : 0;

            const char *qt = q_text->valuestring;
            strncpy(pq.question_text, qt, sizeof(pq.question_text) - 1);
            for (int i = 0; i < pq.num_options && i < 4; i++) {
                const cJSON *opt = cJSON_GetArrayItem(options, i);
                if (opt && cJSON_IsString(opt)) {
                    strncpy(pq.options[i], opt->valuestring, sizeof(pq.options[i]) - 1);
                }
            }

            uint8_t spi_buf[MSG_MAX_SIZE];
            int n = msg_encode(MSG_QUIZ_QUESTION, (const uint8_t *)&pq, sizeof(pq),
                               spi_buf, sizeof(spi_buf));
            if (n > 0) {
                spi_slave_send(spi_buf, n);
            }
        }

    } else if (strcmp(evt, "poll_start") == 0) {
        const cJSON *poll_id = cJSON_GetObjectItem(msg, "poll_id");
        const cJSON *title   = cJSON_GetObjectItem(msg, "title");
        const cJSON *options = cJSON_GetObjectItem(msg, "options");

        if (poll_id && options) {
            /* Build MSG_POLL_START payload: poll_id(2) + num_options(1) + question_text */
            uint8_t payload_buf[128] = {0};
            int off = 0;
            uint16_t pid = (uint16_t)poll_id->valueint;
            payload_buf[off++] = (pid >> 8) & 0xFF;
            payload_buf[off++] = pid & 0xFF;
            int n_opts = cJSON_GetArraySize(options);
            payload_buf[off++] = (uint8_t)n_opts;
            /* Poll title as UTF-8 text */
            const char *t = title ? title->valuestring : "";
            int tlen = strlen(t);
            if (tlen > (int)sizeof(payload_buf) - off - 1) tlen = sizeof(payload_buf) - off - 1;
            memcpy(payload_buf + off, t, tlen);
            off += tlen;

            uint8_t spi_buf[MSG_MAX_SIZE];
            int n = msg_encode(MSG_POLL_START, payload_buf, off, spi_buf, sizeof(spi_buf));
            if (n > 0) {
                spi_slave_send(spi_buf, n);
            }
        }

    } else if (strcmp(evt, "device_command") == 0) {
        const cJSON *cmd = cJSON_GetObjectItem(msg, "command");
        const cJSON *pld = cJSON_GetObjectItem(msg, "payload");
        if (cmd && cJSON_IsString(cmd)) {
            ESP_LOGI(TAG, "Device command: %s", cmd->valuestring);

            /* OTA prompt for the S3 hub: translate to MSG_OTA_PROMPT → SPI.
             * The S3 then temporarily attaches to WiFi, applies the update,
             * and returns to mesh duty. */
            if (strcmp(cmd->valuestring, "ota_update") == 0 &&
                pld && cJSON_IsObject(pld)) {
                const cJSON *version = cJSON_GetObjectItem(pld, "version");
                if (version && cJSON_IsString(version)) {
                    payload_ota_prompt_t prompt = {0};
                    strncpy(prompt.version, version->valuestring,
                            sizeof(prompt.version) - 1);
                    uint8_t spi_buf[MSG_MAX_SIZE];
                    int n = msg_encode(MSG_OTA_PROMPT,
                                       (const uint8_t *)&prompt, sizeof(prompt),
                                       spi_buf, sizeof(spi_buf));
                    if (n > 0) {
                        spi_slave_send(spi_buf, n);
                        ESP_LOGI(TAG, "Relayed OTA prompt v%s to S3",
                                 prompt.version);
                    }
                }
            }

            /* Forward raw command JSON via SPI as MSG_SPI_COMMAND */
            cJSON *pld_owned = NULL;
            if (!pld) {
                pld_owned = cJSON_CreateObject();
                pld = pld_owned;
            }
            char *cmd_json = cJSON_PrintUnformatted(pld);
            if (cmd_json) {
                uint8_t spi_buf[MSG_MAX_SIZE];
                int n = msg_encode(MSG_SPI_COMMAND, (const uint8_t *)cmd_json,
                                   strlen(cmd_json), spi_buf, sizeof(spi_buf));
                cJSON_free(cmd_json);
                if (n > 0) {
                    spi_slave_send(spi_buf, n);
                }
            }
            if (pld_owned) cJSON_Delete(pld_owned);
        }

    } else if (strcmp(evt, "connected") == 0) {
        /* WS handshake — extract class_id if present */
        const cJSON *cid = cJSON_GetObjectItem(msg, "class_id");
        if (cid && cJSON_IsNumber(cid)) {
            handle_class_assignment(msg);
        }

    } else if (strcmp(evt, "connect_to_class") == 0) {
        handle_class_assignment(msg);
    }

    cJSON_Delete(msg);
}

/* ── WiFi Connect with Exponential Backoff ──────────────────────────── */

static bool wifi_connect_with_backoff(void)
{
    uint32_t delay_ms = 2000;
    const uint32_t max_delay_ms = 30000;

    for (int attempt = 0; attempt < g_cfg.hb_interval_s * 10; attempt++) {
        ESP_LOGI(TAG, "WiFi connect attempt %d (backoff %lu ms)", attempt + 1, (unsigned long)delay_ms);
        if (wifi_client_wait_connected(delay_ms)) {
            ESP_LOGI(TAG, "WiFi connected!");
            return true;
        }
        delay_ms = (delay_ms * 3) / 2;
        if (delay_ms > max_delay_ms) delay_ms = max_delay_ms;
    }
    return false;
}

/* ── App Entry ──────────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "=== imPress C6 Gateway v%s ===", FIRMWARE_VERSION);
    s_boot_time_us = esp_timer_get_time();

    /* 1. NVS + runtime config */
    init_nvs_config();

    /* 2. MAC address */
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);
    snprintf(s_mac_str, sizeof(s_mac_str), "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    ESP_LOGI(TAG, "MAC: %s  class_id: %ld", s_mac_str, (long)g_cfg.class_id);

    /* 3. SPI slave — S3 can begin sending immediately */
    ESP_ERROR_CHECK(spi_slave_init());

    /* 4. WiFi with backoff */
    ESP_ERROR_CHECK(wifi_client_init());
    if (!wifi_connect_with_backoff()) {
        ESP_LOGE(TAG, "WiFi failed — will retry in background");
    }

    /* 5. Register with backend + open WebSocket (if WiFi is up) */
    if (wifi_client_is_connected()) {
        ESP_LOGI(TAG, "Registering with backend...");
        http_register_device(s_mac_str, DEVICE_TYPE);
        s_gateway_ready = true;

        if (g_cfg.class_id > 0) {
            ESP_LOGI(TAG, "Connecting WS to class %ld", (long)g_cfg.class_id);
            ws_client_start(g_cfg.class_id, on_ws_command);
        }
    }

    /* 6. Start persistent tasks — larger stacks to avoid canary overflow with cJSON+HTTP */
    xTaskCreate(spi_to_http_task, "spi2http", 12288, NULL, 5, NULL);
    xTaskCreate(heartbeat_task, "heartbeat", 6144, NULL, 3, NULL);
    xTaskCreate(status_ping_task, "status_ping", 6144, NULL, 2, NULL);

    /* Log stack watermarks periodically for debugging */
    vTaskDelay(pdMS_TO_TICKS(5000));
    ESP_LOGI(TAG, "spi2http HWM: %d", uxTaskGetStackHighWaterMark(NULL));

    /* 7. Main loop: WiFi/WS reconnect with exponential backoff */
    uint32_t wifi_delay_ms = 2000;
    uint32_t ws_delay_ms   = 5000;
    const uint32_t max_wifi_delay = 60000;
    const uint32_t max_ws_delay   = 120000;

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(5000));

        /* WiFi reconnection */
        if (!wifi_client_is_connected()) {
            s_gateway_ready = false;
            if (wifi_client_wait_connected(wifi_delay_ms)) {
                ESP_LOGI(TAG, "WiFi reconnected");
                wifi_delay_ms = 2000;
                s_gateway_ready = true;
                http_register_device(s_mac_str, DEVICE_TYPE);
            } else {
                wifi_delay_ms = (wifi_delay_ms * 3) / 2;
                if (wifi_delay_ms > max_wifi_delay) wifi_delay_ms = max_wifi_delay;
            }
            continue;
        }

        /* WebSocket reconnection (only if we have a class ID) */
        if (g_cfg.class_id > 0 && !ws_client_is_connected()) {
            if (wifi_client_wait_connected(ws_delay_ms)) {
                ESP_LOGI(TAG, "WS reconnecting to class %ld", (long)g_cfg.class_id);
                ws_client_start(g_cfg.class_id, on_ws_command);
                ws_delay_ms = 5000;
            } else {
                ws_delay_ms = (ws_delay_ms * 3) / 2;
                if (ws_delay_ms > max_ws_delay) ws_delay_ms = max_ws_delay;
            }
        }
    }
}