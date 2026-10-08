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
#include "ws_command.h"
#include "student_set.h"
#include "esp_efuse.h"
#include "esp_mac.h"

static const char *TAG = "c6_main";

/* ── Runtime State ──────────────────────────────────────────────────── */

static char s_mac_str[DEVICE_MAC_STR_LEN] = "";
static volatile bool s_gateway_ready = false;
static volatile int64_t s_boot_time_us = 0;
/* Students on the mesh, from JOIN/LEAVE (owned by spi2http). Other tasks
 * read only the mirrored count. */
static student_set_t s_students;
static volatile int s_student_count = 0;
static TaskHandle_t s_spi2http_task;

/* heartbeat_task → spi2http: "append the C6's own heartbeat to the batch".
 * s_batch (a non-thread-safe cJSON tree) is owned by spi2http alone; other
 * tasks only raise this flag. */
static volatile bool s_hb_item_pending = false;

/* Set from the WS event handler (websocket task) when the backend assigns a
 * new class; app_main's loop restarts the client. The client must never be
 * stopped/destroyed from its own task — the component frees itself under
 * its running task (use-after-free). */
static volatile bool s_ws_restart_pending = false;

/* ── Batch Accumulator ──────────────────────────────────────────────── */
/* Only ever touched from spi_to_http_task (see s_hb_item_pending). */

/* While Wi-Fi (or the backend) is down the batch keeps accumulating, so it
 * is bounded: at BATCH_MAX_BUFFERED the oldest heartbeat (else the oldest
 * item) is dropped. A flush POSTs at most batch_max items, which keeps the
 * JSON inside http_send_batch()'s HTTP_BUF_SIZE buffer. */
#define BATCH_MAX_BUFFERED   200
#define BATCH_RETRY_MS       1000

typedef struct {
    cJSON *items;    /* JSON array being accumulated */
    int64_t last_add_us;
    int64_t retry_after_us;   /* back-off after a failed POST */
    uint32_t dropped;         /* items discarded (buffer full or rejected) */
} batch_acc_t;

static batch_acc_t s_batch = {0};

static void batch_init(void)
{
    s_batch.items = cJSON_CreateArray();
    s_batch.last_add_us = esp_timer_get_time();
}

static bool item_is_heartbeat(const cJSON *item)
{
    const cJSON *t = cJSON_GetObjectItemCaseSensitive(item, "type");
    return cJSON_IsString(t) && strcmp(t->valuestring, "heartbeat") == 0;
}

static void batch_add(cJSON *item)
{
    if (!item) return;
    if (cJSON_GetArraySize(s_batch.items) >= BATCH_MAX_BUFFERED) {
        int victim = 0, i = 0;
        const cJSON *it;
        cJSON_ArrayForEach(it, s_batch.items) {
            if (item_is_heartbeat(it)) { victim = i; break; }
            i++;
        }
        cJSON_DeleteItemFromArray(s_batch.items, victim);
        if (s_batch.dropped++ % 50 == 0) {
            ESP_LOGW(TAG, "Batch buffer full (%d items, backend unreachable?): "
                     "dropped %lu so far", BATCH_MAX_BUFFERED, (unsigned long)s_batch.dropped);
        }
    }
    cJSON_AddItemToArray(s_batch.items, item);
    s_batch.last_add_us = esp_timer_get_time();
}

static bool batch_flush_needed(void)
{
    int64_t now = esp_timer_get_time();
    int count = cJSON_GetArraySize(s_batch.items);
    int64_t elapsed_ms = (now - s_batch.last_add_us) / 1000;
    if (count == 0 || now < s_batch.retry_after_us) return false;
    return (count >= (int)g_cfg.batch_max) ||
           (elapsed_ms >= (int64_t)g_cfg.spi_batch_max_ms);
}

/* POST one chunk of at most batch_max items. Kept for retry on a network
 * error or 5xx; dropped on 4xx (a malformed chunk would block the queue). */
static void batch_flush(void)
{
    cJSON *chunk = cJSON_CreateArray();
    if (!chunk) return;
    int n = 0;
    while (n < (int)g_cfg.batch_max && cJSON_GetArraySize(s_batch.items) > 0) {
        cJSON_AddItemToArray(chunk, cJSON_DetachItemFromArray(s_batch.items, 0));
        n++;
    }

    char *json = cJSON_PrintUnformatted(chunk);
    int status = 0;
    if (json) {
        status = http_send_batch(json);
        ESP_LOGI(TAG, "Batch flush %d items → /api/device/batch: HTTP %d", n, status);
        ESP_LOGD(TAG, "Batch data: %s", json);   /* enrollment numbers: debug only */
        free(json);
    }

    if (status >= 200 && status < 300) {
        s_batch.retry_after_us = 0;
    } else if (status >= 400 && status < 500) {
        s_batch.dropped += n;
        ESP_LOGW(TAG, "Backend rejected batch (HTTP %d): %d items dropped", status, n);
    } else {
        /* put the chunk back in front, in order, and back off */
        for (int i = n - 1; i >= 0; i--) {
            cJSON_InsertItemInArray(s_batch.items, 0, cJSON_DetachItemFromArray(chunk, i));
        }
        s_batch.retry_after_us = esp_timer_get_time() + BATCH_RETRY_MS * 1000LL;
    }
    cJSON_Delete(chunk);
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
        /* The S3's own heartbeat (sender 0): if its uptime went backwards it
         * rebooted without sending LEAVEs, so the online set is stale. */
        if (sender_device_id == 0 && student_set_root_uptime(&s_students, p->uptime_s)) {
            ESP_LOGW(TAG, "S3 rebooted: online-student set cleared");
            s_student_count = 0;
        }
        break;
    }
    case MSG_STUDENT_JOIN: {
        if (len < sizeof(payload_student_join_t)) break;
        const payload_student_join_t *p = (const payload_student_join_t *)payload;
        if (student_set_join(&s_students, p->enrollment)) {
            s_student_count = student_set_count(&s_students);
            ESP_LOGI(TAG, "Student online: %.10s (total=%d)", p->enrollment, s_student_count);
        }
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
        if (student_set_leave(&s_students, p->enrollment)) {
            s_student_count = student_set_count(&s_students);
            ESP_LOGI(TAG, "Student offline: %.10s (total=%d)", p->enrollment, s_student_count);
        }
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
    case MSG_OTA_APPLIED: {
        /* The S3's OTA outcome (applied after reboot / rolled back / failed).
         * It was never relayed before, so the backend never saw an S3 update
         * complete. */
        if (len < sizeof(payload_ota_result_t)) break;
        payload_ota_result_t r;
        memcpy(&r, payload, sizeof(r));
        r.version[sizeof(r.version) - 1] = '\0';
        r.mac[sizeof(r.mac) - 1] = '\0';
        static const char *const names[] = {"applied", "rolled_back", "failed"};
        j = cJSON_CreateObject();
        cJSON_AddStringToObject(j, "type", "ota_result");
        cJSON_AddStringToObject(j, "mac_address", r.mac);
        cJSON_AddStringToObject(j, "version", r.version);
        cJSON_AddStringToObject(j, "result", r.result < 3 ? names[r.result] : "failed");
        cJSON_AddNumberToObject(j, "error", r.error);
        cJSON_AddStringToObject(j, "device_mac", s_mac_str);   /* relaying gateway */
        ESP_LOGI(TAG, "S3 OTA result: %s %s (err %ld)", r.version,
                 r.result < 3 ? names[r.result] : "?", (long)r.error);
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

    /* Flush only when the backend is reachable; otherwise keep accumulating
     * (bounded, see batch_add). */
    if (wifi_client_is_connected() && batch_flush_needed()) {
        batch_flush();
    }
}

/* spi2http polls every 2 ms; with a 100 Hz tick that rounds to 0 ticks and
 * the task (priority 5) would spin, starve IDLE and trip the task watchdog. */
#if CONFIG_FREERTOS_HZ < 500
#error "spi_to_http_task's 2 ms poll needs CONFIG_FREERTOS_HZ >= 500 (sdkconfig.defaults sets 1000)"
#endif

static void spi_to_http_task(void *arg)
{
    (void)arg;
    uint8_t buf[SPI_RX_BUF_SIZE];
    batch_init();
    student_set_init(&s_students);

    while (1) {
        /* Reap and re-arm the SPI slot often, Wi-Fi or not: the S3 can only
         * clock a slot the C6 has armed. The old 50 ms + Wi-Fi gate left the
         * C6 with no armed slot, dropping commands and student events. */
        vTaskDelay(pdMS_TO_TICKS(2));

        int len = spi_slave_read(buf, sizeof(buf));
        if (len > 0) {
            ESP_LOGD(TAG, "SPI data (%d bytes) → batch", len);
            process_spi_payload(buf, len);
        }

        if (s_hb_item_pending) {
            s_hb_item_pending = false;
            cJSON *j = cJSON_CreateObject();
            cJSON_AddStringToObject(j, "type", "heartbeat");
            cJSON_AddStringToObject(j, "device_mac", s_mac_str);
            cJSON_AddNumberToObject(j, "battery_pct", 100);  /* C6 is mains-powered */
            batch_add(j);
        }

        /* Periodic flush check */
        if (wifi_client_is_connected() && batch_flush_needed()) {
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

        /* C6's own status goes in the next batch; spi2http owns s_batch. */
        s_hb_item_pending = true;
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
            /* Reconnect to the NEW class URI from app_main, not from here. */
            s_ws_restart_pending = true;
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

    /* Mesh commands (quiz/poll start + end): JSON → protocol frame → S3. */
    uint8_t frame[MSG_MAX_SIZE];
    int fn = ws_command_to_frame(msg, frame, sizeof(frame));
    if (fn > 0) {
        int rc = spi_slave_send(frame, fn);
        ESP_LOGI(TAG, "Queued %s for S3 over SPI: len=%d rc=%d", evt, fn, rc);
    } else if (fn < 0) {
        ESP_LOGW(TAG, "Malformed '%s' command — dropped", evt);
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
    xTaskCreate(spi_to_http_task, "spi2http", 12288, NULL, 5, &s_spi2http_task);
    xTaskCreate(heartbeat_task, "heartbeat", 6144, NULL, 3, NULL);
    xTaskCreate(status_ping_task, "status_ping", 6144, NULL, 2, NULL);

    /* Log stack watermarks periodically for debugging */
    vTaskDelay(pdMS_TO_TICKS(5000));
    ESP_LOGI(TAG, "spi2http HWM: %u",
             (unsigned)uxTaskGetStackHighWaterMark(s_spi2http_task));

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

        /* Deferred class reassignment (see s_ws_restart_pending). */
        if (s_ws_restart_pending) {
            s_ws_restart_pending = false;
            ws_client_stop();
            if (g_cfg.class_id > 0) {
                ESP_LOGI(TAG, "WS switching to class %ld", (long)g_cfg.class_id);
                ws_client_start(g_cfg.class_id, on_ws_command);
                ws_delay_ms = 5000;
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