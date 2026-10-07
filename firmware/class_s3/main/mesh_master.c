/**
 * @file mesh_master.c
 * @brief ESP-NOW mesh master implementation for S3.
 *
 * The S3 acts as the root node of the mesh:
 *  - Receives broadcast messages from students (direct or relayed)
 *  - Maintains a routing table keyed on ENROLLMENT NUMBER (student identity)
 *  - Broadcasts commands (quiz questions, polls) to all students
 *  - Batches student responses for SPI transfer to C6
 *
 * IMPORTANT: The student's identity is the ENROLLMENT NUMBER (10 chars).
 * MAC address and device_id are used ONLY for ESP-NOW routing and are
 * NEVER reported to the backend.
 */

#include "mesh_master.h"
#include "config.h"

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "nvs_flash.h"

static const char *TAG = "mesh_master";

/* ── Student Routing Table ─────────────────────────────────────────── */

static student_entry_t s_students[MESH_MAX_STUDENTS];
static int s_student_count = 0;
static SemaphoreHandle_t s_student_mutex;

/* Message buffer for flush_to_spi */
#define MSG_QUEUE_SIZE  64
static struct {
    uint8_t  data[MSG_MAX_SIZE + 16];
    uint16_t length;
} s_msg_queue[MSG_QUEUE_SIZE];
static volatile int s_msg_queue_head = 0;
static volatile int s_msg_queue_tail = 0;
static SemaphoreHandle_t s_queue_mutex;

static mesh_master_recv_cb_t s_recv_callback;

/* Each student message reaches the root once per relay path; forward it to
 * the C6 once. Only touched from on_espnow_recv (Wi-Fi task). */
static mesh_dedup_t s_seen;

/* ── Mesh Header (must match student module) ──────────────────────── */

typedef struct __attribute__((packed)) {
    uint8_t  ttl;
    uint32_t sender_id;
    uint8_t  hops;
} mesh_header_t;

#define MESH_HEADER_SIZE sizeof(mesh_header_t)

/* ── Helpers ──────────────────────────────────────────────────────── */

/** Extract enrollment from a protocol payload if the type carries one.
 *  Returns pointer to enrollment string or NULL if not applicable. */
static const char *extract_enrollment(msg_type_t type, const uint8_t *payload)
{
    switch (type) {
        case MSG_STUDENT_JOIN: {
            const payload_student_join_t *p = (const payload_student_join_t *)payload;
            if (p->enrollment[0]) return p->enrollment;
            return NULL;
        }
        case MSG_QUIZ_ANSWER: {
            const payload_quiz_answer_t *p = (const payload_quiz_answer_t *)payload;
            if (p->enrollment[0]) return p->enrollment;
            return NULL;
        }
        case MSG_POLL_VOTE: {
            const payload_poll_vote_t *p = (const payload_poll_vote_t *)payload;
            if (p->enrollment[0]) return p->enrollment;
            return NULL;
        }
        default:
            return NULL;
    }
}

/* ── Student Table Management ─────────────────────────────────────── */

/**
 * Find or create a student entry.  Priority:
 *  1. Match by enrollment (if the payload carried one — student_join)
 *  2. Match by device_id (ESP-NOW routing — older students without enrollment)
 *  3. Create new entry (enrollment will be filled in on student_join)
 */
static student_entry_t *find_or_create_student(uint32_t sender_id,
                                                const uint8_t *mac,
                                                const char *enrollment)
{
    /* 1. Try enrollment match (primary identity) */
    if (enrollment && enrollment[0]) {
        for (int i = 0; i < s_student_count; i++) {
            if (strncmp(s_students[i].enrollment, enrollment, 11) == 0) {
                s_students[i].device_id    = sender_id;
                s_students[i].last_seen_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
                s_students[i].is_active    = true;
                return &s_students[i];
            }
        }
    }

    /* 2. Fallback: match by sender_id (for heartbeats/answers before join) */
    for (int i = 0; i < s_student_count; i++) {
        if (s_students[i].device_id == sender_id) {
            /* If we just learned the enrollment, fill it in */
            if (enrollment && enrollment[0] && !s_students[i].enrollment[0]) {
                strncpy(s_students[i].enrollment, enrollment, 11);
            }
            s_students[i].last_seen_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
            s_students[i].is_active    = true;
            return &s_students[i];
        }
    }

    /* 3. New student — add to table */
    if (s_student_count < MESH_MAX_STUDENTS) {
        student_entry_t *s = &s_students[s_student_count];
        memset(s, 0, sizeof(*s));
        if (enrollment && enrollment[0]) {
            strncpy(s->enrollment, enrollment, 11);
        }
        s->device_id     = sender_id;
        memcpy(s->mac, mac, 6);
        s->hops          = 0;
        s->rssi          = 0;
        s->last_seen_ms  = xTaskGetTickCount() * portTICK_PERIOD_MS;
        s->is_active     = true;
        s_student_count++;

        ESP_LOGI(TAG, "New student: enroll='%s' id=0x%08lX total=%d",
                 s->enrollment[0] ? s->enrollment : "???",
                 (unsigned long)sender_id, s_student_count);
        return s;
    }

    ESP_LOGW(TAG, "Student table full! Cannot add 0x%08lX",
             (unsigned long)sender_id);
    return NULL;
}

/* ── ESP-NOW Receive Callback ─────────────────────────────────────── */

static void on_espnow_recv(const esp_now_recv_info_t *info,
                           const uint8_t *data, int len)
{
    if (!info || !data || len < (int)MESH_HEADER_SIZE) return;

    const mesh_header_t *hdr = (const mesh_header_t *)data;

    /* Ignore messages that originated at the root itself (sender_id == 0).
     * Discriminating by ttl==MAX && hops==0 is wrong: students send direct
     * frames exactly like that, so that check silently dropped every JOIN. */
    if (hdr->sender_id == 0) {
        return;
    }

    /* Parse inner protocol message to extract enrollment early */
    const uint8_t *msg_data = data + MESH_HEADER_SIZE;
    int msg_len = len - MESH_HEADER_SIZE;
    msg_t msg;
    int consumed = msg_decode(msg_data, msg_len, &msg);

    const char *enrollment = NULL;
    bool valid = consumed > 0 && msg_verify_crc(&msg);
    if (valid) {
        enrollment = extract_enrollment(msg.type, msg.payload);
    }
    uint32_t now_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
    bool duplicate = valid &&
        mesh_dedup_check(&s_seen, mesh_msg_id(hdr->sender_id, msg_data, consumed), now_ms);

    /* Update student routing table */
    xSemaphoreTake(s_student_mutex, portMAX_DELAY);
    student_entry_t *student = find_or_create_student(
        hdr->sender_id, info->src_addr, enrollment);
    if (student) {
        student->hops = hdr->hops;
        if (info->rx_ctrl) {
            student->rssi = info->rx_ctrl->rssi;
        }
    }
    xSemaphoreGive(s_student_mutex);

    /* Queue message for SPI transfer to C6 — once, however many relay
     * copies arrive. (The routing-table refresh above still counts them.) */
    if (valid && !duplicate) {
        xSemaphoreTake(s_queue_mutex, portMAX_DELAY);
        int next = (s_msg_queue_tail + 1) % MSG_QUEUE_SIZE;
        if (next != s_msg_queue_head) {
            s_msg_queue[s_msg_queue_tail].length = consumed + 4;
            /* Prepend sender_id so C6 can identify the relay node */
            memcpy(s_msg_queue[s_msg_queue_tail].data, &hdr->sender_id, 4);
            memcpy(s_msg_queue[s_msg_queue_tail].data + 4, msg_data, consumed);
            s_msg_queue_tail = next;
        } else {
            ESP_LOGW(TAG, "Message queue full, dropping message");
        }
        xSemaphoreGive(s_queue_mutex);

        /* Invoke callback */
        if (s_recv_callback) {
            s_recv_callback(&msg, hdr->sender_id);
        }
    }

    /* If this was a JOIN, broadcast a heartbeat (TTL=MAX) so the student
     * hears it and flips IS_CONNECTED (student mesh_espnow.c:112). */
    if (valid && msg.type == MSG_STUDENT_JOIN) {   /* reply even to a retried JOIN */
        payload_heartbeat_t hb = {
            .device_id   = hdr->sender_id,
            .battery_pct = 100,
            .rssi        = info->rx_ctrl ? info->rx_ctrl->rssi : 0,
            .uptime_s    = (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS / 1000),
        };
        uint8_t hb_buf[MSG_MAX_SIZE];
        int hb_len = msg_encode(MSG_HEARTBEAT, (const uint8_t *)&hb,
                                sizeof(hb), hb_buf, sizeof(hb_buf));
        if (hb_len > 0) {
            mesh_master_broadcast(MSG_HEARTBEAT, hb_buf, hb_len);
        }
    }
}

/* ── Public API ───────────────────────────────────────────────────── */

int mesh_master_init(void)
{
    s_student_mutex = xSemaphoreCreateMutex();
    s_queue_mutex   = xSemaphoreCreateMutex();

    /* Init NVS */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    }

    /* Init WiFi STA (for ESP-NOW — not for internet access) */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    /* esp_wifi_set_channel() requires WiFi to be started first */
    ESP_ERROR_CHECK(esp_wifi_start());
    vTaskDelay(pdMS_TO_TICKS(100));  /* let WiFi radio settle */
    ret = esp_wifi_set_channel(g_cfg.mesh_channel, WIFI_SECOND_CHAN_NONE);
    if (ret != ESP_OK) {
        /* Don't abort (the old ESP_ERROR_CHECK here boot-looped), but say so:
         * students on the configured channel won't hear us. */
        ESP_LOGE(TAG, "esp_wifi_set_channel(%d) failed: %s",
                 g_cfg.mesh_channel, esp_err_to_name(ret));
    }

    /* Init ESP-NOW */
    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_espnow_recv));

    /* Add broadcast peer */
    esp_now_peer_info_t broadcast_peer = {
        .channel = g_cfg.mesh_channel,
        .ifidx   = WIFI_IF_STA,
    };
    memset(broadcast_peer.peer_addr, 0xFF, 6);
    ret = esp_now_add_peer(&broadcast_peer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_now_add_peer failed: %d (0x%X)", ret, ret);
    } else {
        ESP_LOGI(TAG, "Broadcast peer added successfully");
        vTaskDelay(pdMS_TO_TICKS(200));  /* let radio/peer table settle before broadcast */
    }

    ESP_LOGI(TAG, "Mesh master initialized, channel=%d, max=%d students",
             g_cfg.mesh_channel, MESH_MAX_STUDENTS);
    return 0;
}

int mesh_master_broadcast(msg_type_t type, const uint8_t *payload, uint16_t length)
{
    /* Encode protocol message */
    uint8_t msg_buf[MSG_MAX_SIZE];
    int msg_len = msg_encode(type, payload, length, msg_buf, sizeof(msg_buf));
    if (msg_len < 0) return -1;

    /* Prepend mesh header (from root) */
    mesh_header_t hdr = {
        .ttl       = MESH_RELAY_TTL,
        .sender_id = 0,  /* root has ID 0 */
        .hops      = 0,
    };

    uint8_t send_buf[MESH_HEADER_SIZE + MSG_MAX_SIZE];
    memcpy(send_buf, &hdr, MESH_HEADER_SIZE);
    memcpy(send_buf + MESH_HEADER_SIZE, msg_buf, msg_len);

    /* Rely on the explicitly-added broadcast peer; NULL dest reports
     * ESP_ERR_ESPNOW_NOT_FOUND in this IDF fork even when the peer exists. */
    static const uint8_t bcast[6] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
    esp_err_t ret = esp_now_send(bcast, send_buf, MESH_HEADER_SIZE + msg_len);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Broadcast failed (peer_exist=%d): %d",
                 (int)esp_now_is_peer_exist(bcast), ret);
        return -1;
    }

    ESP_LOGI(TAG, "Broadcast: %s (%d bytes)", msg_type_name(type), length);
    return 0;
}

int mesh_master_unicast(uint32_t device_id, msg_type_t type,
                        const uint8_t *payload, uint16_t length)
{
    /* Find student's MAC by device_id */
    xSemaphoreTake(s_student_mutex, portMAX_DELAY);
    const student_entry_t *target = NULL;
    for (int i = 0; i < s_student_count; i++) {
        if (s_students[i].device_id == device_id) {
            target = &s_students[i];
            break;
        }
    }
    xSemaphoreGive(s_student_mutex);

    if (!target) {
        ESP_LOGW(TAG, "Student 0x%08lX not found for unicast",
                 (unsigned long)device_id);
        return -1;
    }

    /* Encode message */
    uint8_t msg_buf[MSG_MAX_SIZE];
    int msg_len = msg_encode(type, payload, length, msg_buf, sizeof(msg_buf));
    if (msg_len < 0) return -1;

    /* Add peer if needed */
    esp_now_peer_info_t peer_info = {
        .channel = g_cfg.mesh_channel,
        .ifidx   = WIFI_IF_STA,
    };
    memcpy(peer_info.peer_addr, target->mac, 6);

    if (!esp_now_is_peer_exist(target->mac)) {
        esp_now_add_peer(&peer_info);
    }

    esp_err_t ret = esp_now_send(target->mac, msg_buf, msg_len);
    return (ret == ESP_OK) ? 0 : -1;
}

int mesh_master_unicast_by_enrollment(const char *enrollment, msg_type_t type,
                                      const uint8_t *payload, uint16_t length)
{
    if (!enrollment || !enrollment[0]) return -1;

    /* Find student by enrollment */
    xSemaphoreTake(s_student_mutex, portMAX_DELAY);
    const student_entry_t *target = NULL;
    for (int i = 0; i < s_student_count; i++) {
        if (strncmp(s_students[i].enrollment, enrollment, 11) == 0) {
            target = &s_students[i];
            break;
        }
    }
    xSemaphoreGive(s_student_mutex);

    if (!target) {
        ESP_LOGW(TAG, "Student '%s' not found for unicast", enrollment);
        return -1;
    }

    return mesh_master_unicast(target->device_id, type, payload, length);
}

int mesh_master_get_student_count(void)
{
    int count = 0;
    xSemaphoreTake(s_student_mutex, portMAX_DELAY);
    for (int i = 0; i < s_student_count; i++) {
        if (s_students[i].is_active) count++;
    }
    xSemaphoreGive(s_student_mutex);
    return count;
}

const student_entry_t *mesh_master_get_student(int index)
{
    if (index < 0 || index >= s_student_count) return NULL;
    return &s_students[index];
}

int mesh_master_get_all_students(student_entry_t *out_students, int max_students)
{
    if (!out_students || max_students <= 0) return 0;
    int count = 0;
    xSemaphoreTake(s_student_mutex, portMAX_DELAY);
    for (int i = 0; i < s_student_count && count < max_students; i++) {
        if (s_students[i].is_active) {
            out_students[count] = s_students[i];
            count++;
        }
    }
    xSemaphoreGive(s_student_mutex);
    return count;
}

/**
 * @brief Check for timed-out students and mark them inactive.
 *        Called periodically from heartbeat task.
 *        Emits MSG_STUDENT_LEAVE for each timed-out student so C6/backend is notified.
 *        Leave events go through the same SPI queue as student messages, so
 *        their framing matches what C6 already parses.
 */
void mesh_master_sweep_timeouts(uint32_t timeout_ms)
{
    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    uint32_t too_old = (now >= timeout_ms) ? (now - timeout_ms) : 0;
    int swept = 0;
    uint8_t msg_buf[MSG_MAX_SIZE];

    /* Deactivate timed-out students and queue their leave events. */
    xSemaphoreTake(s_student_mutex, portMAX_DELAY);
    for (int i = 0; i < s_student_count; i++) {
        if (s_students[i].is_active && s_students[i].last_seen_ms < too_old) {
            char enrollment[11];
            uint32_t device_id = s_students[i].device_id;
            strncpy(enrollment, s_students[i].enrollment, sizeof(enrollment) - 1);
            enrollment[sizeof(enrollment) - 1] = '\0';

            s_students[i].is_active = false;
            swept++;

            payload_student_leave_t leave = {0};
            strncpy(leave.enrollment, enrollment, sizeof(leave.enrollment) - 1);
            leave.device_id = device_id;
            leave.reason = 0;  /* 0 = timeout */

            int msg_len = msg_encode(MSG_STUDENT_LEAVE, (const uint8_t *)&leave,
                                     sizeof(payload_student_leave_t),
                                     msg_buf, sizeof(msg_buf));
            if (msg_len <= 0) {
                ESP_LOGW(TAG, "Failed to encode leave event for '%s'", enrollment);
                continue;
            }

            /* Queue [sender_id:4][proto msg] — same format as on_espnow_recv */
            xSemaphoreTake(s_queue_mutex, portMAX_DELAY);
            int next = (s_msg_queue_tail + 1) % MSG_QUEUE_SIZE;
            if (next != s_msg_queue_head) {
                s_msg_queue[s_msg_queue_tail].length = 4 + msg_len;
                memcpy(s_msg_queue[s_msg_queue_tail].data, &device_id, 4);
                memcpy(s_msg_queue[s_msg_queue_tail].data + 4, msg_buf, msg_len);
                s_msg_queue_tail = next;
            } else {
                ESP_LOGW(TAG, "Message queue full, dropping leave event for '%s'",
                         enrollment);
            }
            xSemaphoreGive(s_queue_mutex);
        }
    }
    xSemaphoreGive(s_student_mutex);

    if (swept) {
        ESP_LOGI(TAG, "Swept %d timed-out students, %d still active",
                 swept, mesh_master_get_student_count());
    }
}

void mesh_master_on_receive(mesh_master_recv_cb_t callback)
{
    s_recv_callback = callback;
}

int mesh_master_flush_to_spi(uint8_t *buf, size_t buf_size)
{
    int total = 0;
    xSemaphoreTake(s_queue_mutex, portMAX_DELAY);

    /* Queue entries hold [sender_id:4 native][frame]; emit the shared
     * spi_record layout, whose length field covers the frame only. */
    while (s_msg_queue_head != s_msg_queue_tail) {
        const uint8_t *data = s_msg_queue[s_msg_queue_head].data;
        uint32_t sender_id;
        memcpy(&sender_id, data, 4);
        int n = spi_record_write(buf + total, buf_size - total, sender_id,
                                 data + 4, s_msg_queue[s_msg_queue_head].length - 4);
        if (n < 0) {
            break;  /* slot full — rest goes in the next flush */
        }
        total += n;
        s_msg_queue_head = (s_msg_queue_head + 1) % MSG_QUEUE_SIZE;
    }

    xSemaphoreGive(s_queue_mutex);
    return total;
}
