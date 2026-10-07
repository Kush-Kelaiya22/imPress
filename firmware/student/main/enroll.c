/**
 * @file enroll.c
 * @brief On-device enrollment provisioning for the student module.
 *
 * Two paths set the 10-char alphanumeric identity (both call
 * student_set_enrollment(), which enforces the format and writes NVS):
 *
 *   1. Buttons (on the OLED board):
 *        A (0)   cycle the character at the cursor UP
 *        B (1)   cycle the character at the cursor DOWN
 *        C (2)   backspace / move cursor left
 *        D (3)   clear the whole entry
 *        CONFIRM (4) commit the current character; on the 10th character
 *                   the entry is validated and stored
 *   2. Serial: type `<enrollment>` + Enter on the USB console (UART0).
 *
 * Batches of devices can alternatively be pre-provisioned by writing the
 * "enroll" NVS key directly (survives OTA).
 */

#include "enroll.h"
#include "config.h"
#include "display.h"
#include "input.h"

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "enroll";

/* Button indices — matches s_buttons[] in input.c (A-D = 0-3, confirm = 4). */
#define BTN_CHAR_UP      0
#define BTN_CHAR_DOWN    1
#define BTN_BACKSPACE    2
#define BTN_CLEAR        3
#define BTN_OK           4

/* Characters offered by on-device entry. The backend ENROLL_RE allows
 * [A-Za-z0-9]{10}; we expose digits plus uppercase letters. */
static const char s_chars[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
#define NUM_CHARS ((int)(sizeof(s_chars) - 1))

#define HINT_LINE "A:char B:prev C:del D:clr OK:ok"

static volatile bool s_serial_done;

/* ── Serial provisioning (USB console) ──────────────────────────────── */

static void serial_provision_task(void *arg)
{
    char line[16];

    /* Unbuffered so fgets() returns as soon as Enter is pressed. */
    setvbuf(stdin, NULL, _IONBF, 0);

    ESP_LOGI(TAG, "Serial provisioning ready — type a 10-char enrollment "
                  "then Enter");
    for (;;) {
        if (!fgets(line, sizeof(line), stdin)) {
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        /* Trim CR/LF. */
        size_t n = strlen(line);
        while (n && (line[n - 1] == '\n' || line[n - 1] == '\r')) {
            line[--n] = '\0';
        }
        if (student_set_enrollment(line) == ESP_OK) {
            s_serial_done = true;
            break;
        }
        ESP_LOGW(TAG, "Rejected '%s' — need exactly 10 alphanumeric "
                      "characters", line);
    }
    vTaskDelete(NULL);
}

/* ── Reset (re-provision) trigger ───────────────────────────────────── */

bool enroll_reset_requested(void)
{
    /* Hold CONFIRM + C (backspace) together for 2 s right after boot. */
    int held = 0;
    for (int i = 0; i < 40; i++) {   /* 40 x 50 ms = 2 s */
        if (input_is_button_pressed(BTN_OK) &&
            input_is_button_pressed(BTN_BACKSPACE)) {
            if (++held >= 40) {
                ESP_LOGW(TAG, "Reset combo held — wiping stored identity");
                return true;
            }
        } else {
            held = 0;
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
    return false;
}

/* ── Character wheel ────────────────────────────────────────────────── */

static char enroll_next_char(char c, int dir)
{
    int idx = 0;
    if (c) {
        for (int i = 0; i < NUM_CHARS; i++) {
            if (s_chars[i] == c) {
                idx = i;
                break;
            }
        }
    }
    idx = (idx + dir + NUM_CHARS) % NUM_CHARS;
    return s_chars[idx];
}

/* ── Provisioning loop (buttons + serial) ───────────────────────────── */

int enroll_run(void)
{
    char id[11] = { 0 };          /* 10 chars + NUL */
    int cursor = 0;
    bool prev_down[5] = { false };
    int repeat_start[5] = { 0 };
    bool dirty = true;
    int rc = ESP_FAIL;

    s_serial_done = false;
    display_show_provision_state("SET ID", id, cursor, HINT_LINE);
    xTaskCreate(serial_provision_task, "enroll_serial", 3072, NULL, 2, NULL);

    for (;;) {
        if (s_serial_done) {
            rc = ESP_OK;
            break;
        }

        int now = (int)(xTaskGetTickCount() * portTICK_PERIOD_MS);

        for (int b = 0; b < 5; b++) {
            bool down = input_is_button_pressed(b);
            bool act = false;

            if (down && !prev_down[b]) {               /* fresh press */
                act = true;
                repeat_start[b] = now;
            } else if (down && prev_down[b] &&
                       (now - repeat_start[b]) >= 350) { /* auto-repeat */
                act = true;
                repeat_start[b] = now - (350 - 150);
            } else if (!down) {
                repeat_start[b] = 0;
            }

            if (act) {
                switch (b) {
                case BTN_CHAR_UP:
                    id[cursor] = enroll_next_char(id[cursor], +1);
                    break;
                case BTN_CHAR_DOWN:
                    id[cursor] = enroll_next_char(id[cursor], -1);
                    break;
                case BTN_BACKSPACE:
                    if (cursor > 0) cursor--;
                    id[cursor] = '\0';
                    break;
                case BTN_CLEAR:
                    memset(id, 0, sizeof(id));
                    cursor = 0;
                    break;
                case BTN_OK:
                    if (cursor < 9) {                  /* commit + advance */
                        if (!id[cursor]) id[cursor] = s_chars[0];
                        cursor++;
                    } else {                           /* finalize + store */
                        if (!id[cursor]) id[cursor] = s_chars[0];
                        id[10] = '\0';
                        if (student_set_enrollment(id) == ESP_OK) {
                            rc = ESP_OK;
                        } else {
                            ESP_LOGW(TAG, "Entry rejected — restarting");
                            memset(id, 0, sizeof(id));
                            cursor = 0;
                            display_show_provision_state(
                                "BAD ID", id, cursor,
                                "10 chars  A-Z0-9   OK:retry");
                            vTaskDelay(pdMS_TO_TICKS(1200));
                        }
                    }
                    break;
                }
                dirty = true;
            }
            prev_down[b] = down;
        }

        if (dirty) {
            display_show_provision_state("SET ID", id, cursor, HINT_LINE);
            dirty = false;
        }

        if (rc == ESP_OK) break;
        vTaskDelay(pdMS_TO_TICKS(20));
    }

    display_clear();
    display_show_text("imPress", "ID SAVED", "OK");
    ESP_LOGI(TAG, "Provisioning complete: enrollment=%s", g_student.enrollment);
    return ESP_OK;
}