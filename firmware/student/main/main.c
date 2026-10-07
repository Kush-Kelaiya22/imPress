/**
 * @file main.c
 * @brief Student module entry point — imPress class participation system.
 *
 * Flow:
 *   1. Init display, input, mesh
 *   2. Join mesh network (find S3 root)
 *   3. Send heartbeat periodically
 *   4. Receive quiz/poll from S3 → display on OLED
 *   5. Button press → send answer/vote through mesh → back to S3
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_random.h"
#include "esp_efuse.h"
#include "esp_mac.h"

#include "config.h"
#include "protocol.h"
#include "mesh_espnow.h"
#include "display.h"
#include "input.h"
#include "enroll.h"

static const char *TAG = "student_main";

/* ── State ─────────────────────────────────────────────────────────── */

typedef enum {
    STATE_INIT,
    STATE_PROVISIONING,  /* waiting for a valid enrollment number */
    STATE_CONNECTING,
    STATE_IDLE,
    STATE_QUIZ_ACTIVE,
    STATE_POLL_ACTIVE,
    STATE_ANSWERED,
} student_state_t;

static student_state_t s_state = STATE_INIT;
static uint32_t s_device_id;
static int s_selected_option = -1;

/* Current quiz/poll context */
static uint16_t s_current_quiz_id;
static uint8_t s_current_question;
static uint16_t s_current_poll_id;

/* ── Mesh Receive Handler ──────────────────────────────────────────── */

static void on_mesh_message(const msg_t *msg)
{
    ESP_LOGI(TAG, "Received: %s (len=%d)", msg_type_name(msg->type), msg->length);

    /* Still listening to the mesh while unprovisioned, but don't act on
     * session traffic — there is no identity to attribute it to yet. */
    if (s_state == STATE_PROVISIONING) {
        ESP_LOGI(TAG, "Ignoring %s while unprovisioned",
                 msg_type_name(msg->type));
        return;
    }

    switch (msg->type) {
        case MSG_QUIZ_QUESTION: {
            if (msg->length >= sizeof(payload_quiz_question_t)) {
                payload_quiz_question_t *q = (payload_quiz_question_t *)msg->payload;
                s_current_quiz_id = q->quiz_id;
                s_current_question = q->question_num;
                s_selected_option = -1;
                s_state = STATE_QUIZ_ACTIVE;

                /* Display question on OLED */
                const char *opts[4];
                for (int i = 0; i < q->num_options && i < 4; i++) {
                    opts[i] = q->options[i];
                }
                display_show_question(q->question_text, opts, q->num_options, -1);

                ESP_LOGI(TAG, "Quiz Q%d: %s", q->question_num, q->question_text);
            }
            break;
        }

        case MSG_POLL_START:      /* what the C6 sends (see ws_command.c) */
        case MSG_POLL_OPTIONS: {
            if (msg->length >= 3) {  /* min: poll_id(2) + num_options(1) */
                const payload_poll_start_t *p = (const payload_poll_start_t *)msg->payload;
                s_current_poll_id = p->poll_id;
                s_selected_option = -1;
                s_state = STATE_POLL_ACTIVE;

                /* Title only when the full struct arrived (NUL-terminated). */
                bool has_title = msg->length >= sizeof(payload_poll_start_t) && p->title[0];
                display_show_waiting(has_title ? p->title : "POLL: Select option");
                ESP_LOGI(TAG, "Poll %d active", s_current_poll_id);
            }
            break;
        }

        case MSG_QUIZ_END:
        case MSG_POLL_END: {
            s_state = STATE_IDLE;
            s_selected_option = -1;
            display_show_result("Session ended");
            break;
        }

        case MSG_STUDENT_JOIN: {
            /* Another student joining — update display */
            ESP_LOGI(TAG, "Student joined mesh");
            break;
        }

        default:
            break;
    }
}

/* ── Button Handler ────────────────────────────────────────────────── */

static void on_button_press(int button)
{
    ESP_LOGI(TAG, "Button pressed: %d", button);

    /* Toggle LED to give feedback */
    gpio_set_level(PIN_LED_STATUS, 0);
    vTaskDelay(pdMS_TO_TICKS(50));
    gpio_set_level(PIN_LED_STATUS, 1);

    if (s_state == STATE_QUIZ_ACTIVE) {
        if (button >= 0 && button <= 3) {
            s_selected_option = button;
            display_show_question("Answer selected", NULL, 0, button);

            /* Build and send answer — enrollment number is the identity */
            payload_quiz_answer_t answer = {0};
            answer.quiz_id = s_current_quiz_id;
            answer.question_num = s_current_question;
            answer.selected_option = (uint8_t)button;
            answer.response_time_ms = 0;  /* TODO: track actual time */
            strncpy(answer.enrollment, g_student.enrollment,
                    sizeof(answer.enrollment) - 1);
            answer.device_id = s_device_id;   /* routing-only diagnostic */
            mesh_send(MSG_QUIZ_ANSWER, (uint8_t *)&answer, sizeof(answer));
            s_state = STATE_ANSWERED;
            ESP_LOGI(TAG, "Answer sent: option %d", button);
        }
    }
    else if (s_state == STATE_POLL_ACTIVE) {
        if (button >= 0 && button <= 3) {
            s_selected_option = button;

            payload_poll_vote_t vote = {0};
                vote.poll_id = s_current_poll_id;
                vote.selected_option = (uint8_t)button;
                strncpy(vote.enrollment, g_student.enrollment,
                        sizeof(vote.enrollment) - 1);
                vote.device_id = s_device_id;   /* routing-only diagnostic */
                mesh_send(MSG_POLL_VOTE, (uint8_t *)&vote, sizeof(vote));
            s_state = STATE_ANSWERED;
            display_show_result("Vote sent!");
            ESP_LOGI(TAG, "Vote sent: option %d", button);
        }
    }
}

/* ── Heartbeat Task ────────────────────────────────────────────────── */

static void heartbeat_task(void *arg)
{
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(HEARTBEAT_INTERVAL_MS));

        payload_heartbeat_t hb = {
            .device_id = s_device_id,
            .battery_pct = 100,  /* TODO: read ADC */
            .rssi = 0,           /* TODO: read RSSI */
            .uptime_s = xTaskGetTickCount() * portTICK_PERIOD_MS / 1000,
        };

        if (mesh_send(MSG_HEARTBEAT, (uint8_t *)&hb, sizeof(hb)) == 0) {
            ESP_LOGD(TAG, "Heartbeat sent");
        }
    }
}

/* ── Entry Point ───────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "=== imPress Student Module v%s ===", FIRMWARE_VERSION);

    /* Load enrollment + profile from NVS (survives OTA) */
    init_student_profile();
    ESP_LOGI(TAG, "Enrollment: %s  provisioned=%d",
             g_student.enrollment, (int)g_student.provisioned);

    /* Generate device ID from MAC — used ONLY internally for ESP-NOW
     * routing; the backend's identity for this student is the enrollment. */
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);
    s_device_id = ((uint32_t)mac[3] << 24) | ((uint32_t)mac[4] << 16) |
                  ((uint32_t)mac[5] << 8) | mac[2];
    ESP_LOGI(TAG, "Device ID: 0x%08lX (routing only)", (unsigned long)s_device_id);

    /* Init subsystems */
    display_init();
    display_show_text("imPress", "Student Module", "Starting...");

    input_init(on_button_press);

    /* Identity reset: hold CONFIRM + C (backspace) for 2 s at boot to
     * wipe the stored enrollment and re-enter provisioning. */
    if (enroll_reset_requested()) {
        student_clear_enrollment();
        display_show_text("imPress", "ID CLEARED", "Set ID again");
        vTaskDelay(pdMS_TO_TICKS(1500));
    }

    /* Listen on the mesh in every state. An unprovisioned device MAY receive
     * (e.g. a server profile push) but MUST NOT join until identity is set,
     * so MSG_STUDENT_JOIN/answers are only sent after the gate below. */
    mesh_init(s_device_id);
    mesh_on_receive(on_mesh_message);

    /* Provisioning gate: no enrollment, no mesh enrollment. */
    if (!student_has_identity()) {
        s_state = STATE_PROVISIONING;
        display_show_text("imPress", "NO ID", "Set ID");
        ESP_LOGW(TAG, "No identity set — running on-device provisioning");
        if (enroll_run() != ESP_OK) {
            ESP_LOGE(TAG, "Provisioning failed — only display available");
        }
        s_state = STATE_CONNECTING;
        display_clear();
    }

    s_state = STATE_CONNECTING;
    display_show_waiting("Connecting to mesh...");

    /* Send join notification immediately — root will reply with heartbeat
     * (TTL=MAX) which flips IS_CONNECTED in mesh_espnow.c:112.
     * Re-send every 2s while still unconnected: esp_now_send can transiently
     * fail at boot (e.g. ESP_ERR_ESPNOW_NOT_FOUND) before the radio/peer
     * table has settled, so a single send is not reliable. */
    payload_student_join_t join = {0};
    strncpy(join.enrollment, g_student.enrollment,
            sizeof(join.enrollment) - 1);
    join.device_id = s_device_id;

    /* Wait for mesh connection (max 30s), re-sending JOIN on failure */
    int timeout = 30;
    while (!mesh_is_connected() && timeout > 0) {
        int ret = mesh_send(MSG_STUDENT_JOIN, (uint8_t *)&join, sizeof(join));
        if (ret == 0) {
            ESP_LOGI(TAG, "JOIN sent, waiting for mesh... (%ds)", timeout);
        } else {
            ESP_LOGW(TAG, "JOIN send failed (%d), retrying... (%ds)", ret, timeout);
        }

        /* Wait up to 2s, checking connection, before next send */
        for (int wait = 0; wait < 2 && !mesh_is_connected() && timeout > 0; wait++) {
            vTaskDelay(pdMS_TO_TICKS(1000));
            timeout--;
        }
    }

    if (mesh_is_connected()) {
        s_state = STATE_IDLE;
        display_show_status("Connected!", 100);
        ESP_LOGI(TAG, "Connected to mesh, hop count: %d", mesh_get_hop_count());

        /* Start heartbeat task */
        xTaskCreate(heartbeat_task, "heartbeat", 2048, NULL, 3, NULL);
    } else {
        display_show_text("ERROR", "No mesh found", "Check S3 module");
        ESP_LOGE(TAG, "Failed to connect to mesh");
    }

    /* Main loop: nothing to do, events handled by callbacks */
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
