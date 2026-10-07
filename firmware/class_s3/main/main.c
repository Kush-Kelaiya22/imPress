/**
 * @file main.c
 * @brief S3 class module entry point — imPress.
 *
 * The S3 is the mesh master and SPI master:
 *   1. Load NVS config (Kconfig defaults + runtime overrides)
 *   2. Init ESP-NOW mesh (root node, receives from all students)
 *   3. Init SPI master (high-speed link to C6)
 *   4. Main loop: batch student messages → SPI → C6
 *   5. Receive commands from C6 via SPI → broadcast to mesh
 *   6. MSG_OTA_PROMPT from C6 → temporarily attach WiFi → OTA → reboot
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_efuse.h"
#include "esp_ota_ops.h"

#include "config.h"
#include "protocol.h"
#include "mesh_master.h"
#include "spi_master.h"
#include "ota.h"

static const char *TAG = "s3_main";

/* ── Mesh Receive Handler ─────────────────────────────────────────── */

static void on_student_message(const msg_t *msg, uint32_t sender_id)
{
    ESP_LOGI(TAG, "Student 0x%08lX: %s", (unsigned long)sender_id,
             msg_type_name(msg->type));
}

/* ── SPI ← C6 Frame Dispatch (preserved verbatim from spi_rx_task) ── */

static void handle_c6_frame(const uint8_t *buf, int len)
{
    msg_t msg;
    int consumed = msg_decode(buf, (size_t)len, &msg);
    if (consumed <= 0) {
        ESP_LOGW(TAG, "Bad frame from C6 (consumed=%d)", consumed);
        return;
    }

    ESP_LOGI(TAG, "C6 command: %s", msg_type_name(msg.type));

    switch (msg.type) {
        case MSG_QUIZ_QUESTION:
        case MSG_POLL_OPTIONS:
        case MSG_QUIZ_START:
        case MSG_POLL_START:
        case MSG_QUIZ_END:
        case MSG_POLL_END:
            mesh_master_broadcast(msg.type, msg.payload, msg.length);
            ESP_LOGI(TAG, "Forwarded %s to mesh", msg_type_name(msg.type));
            break;

        case MSG_OTA_PROMPT: {
            payload_ota_prompt_t p = {0};
            memcpy(&p, msg.payload,
                   msg.length < sizeof(p) ? msg.length : sizeof(p));
            ESP_LOGI(TAG, "OTA prompt: version=%s", p.version);
            ota_start(p.version, p.token);
            break;
        }

        case MSG_ACK:
        case MSG_OTA_APPLIED:
            /* Diagnostics only */
            break;

        default:
            ESP_LOGW(TAG, "Unknown C6 command: 0x%02X", msg.type);
            break;
    }
}

/* ── SPI Link Coordinator Task (replaces spi_tx_task + spi_rx_task) ── */

static void spi_link_task(void *arg)
{
    (void)arg;
    /* Static buffers: batch and RX payload are ~SPI_SLOT_BYTES each and
     * would overflow a 4096-byte task stack, so they live in .bss. */
    static uint8_t batch[SPI_SLOT_BYTES - 4];  /* mesh batch → S3 slot payload */
    static uint8_t rx[SPI_SLOT_BYTES - 4];     /* C6 slot payload */

    while (1) {
        /* Wake on: (a) S3 queued TX via spi_master_send(), (b) R_C6 rise-
         * edge ISR. Bounded wait also keeps the old spi_tx_task cadence so
         * the mesh queue drains to C6 even without other traffic. */
        xSemaphoreTake(spi_master_link_signal(),
                       pdMS_TO_TICKS(g_cfg.spi_poll_interval_ms));

        /* Old spi_tx_task duty: drain batched student messages into slot. */
        int n = mesh_master_flush_to_spi(batch, sizeof(batch));
        if (n > 0) {
            spi_master_send(batch, n);
            ESP_LOGD(TAG, "SPI TX: %d bytes to C6", n);
        }

        /* Old spi_rx_task duty: exactly ONE full-duplex slot transfer if
         * there is anything to send or C6 signalled it has a frame. */
        if (spi_master_tx_pending() || spi_master_c6_has_data()) {
            if (spi_master_poll()) {
                int rlen = spi_master_rx_copy(rx, sizeof(rx));
                if (rlen > 0) {
                    handle_c6_frame(rx, rlen);
                }
            }
        }
    }
}

/* ── Heartbeat Task (S3 → C6 status) ─────────────────────────────── */

static void heartbeat_task(void *arg)
{
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(g_cfg.hb_interval_ms));

        /* Sweep timed-out students so routing table stays accurate */
        mesh_master_sweep_timeouts(g_cfg.student_timeout_ms);

        int student_count = mesh_master_get_student_count();
        ESP_LOGI(TAG, "Active students: %d", student_count);

        /* Send heartbeat status to C6 over SPI */
        payload_heartbeat_t status = {
            .device_id    = 0,   /* S3 root — no student identity */
            .battery_pct  = 100,
            .rssi         = 0,
            .uptime_s     = (uint32_t)(xTaskGetTickCount() *
                                       portTICK_PERIOD_MS / 1000),
        };
        static uint8_t encoded[MSG_MAX_SIZE];            /* static: 2 KB task stack can't hold these */
        int n = msg_encode(MSG_HEARTBEAT, (const uint8_t *)&status,
                           sizeof(status), encoded, sizeof(encoded));
        if (n > 0) {
            /* C6's SPI parser only understands the batch record format. */
            static uint8_t slot[SPI_RECORD_HEADER_SIZE + MSG_MAX_SIZE];
            int len = spi_record_write(slot, sizeof(slot), 0 /* S3 root id */,
                                       encoded, (uint16_t)n);
            if (len > 0) {
                spi_master_send(slot, len);
            }
        }
    }
}

/* ── Entry Point ─────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "=== imPress S3 Class Module v%s ===", FIRMWARE_VERSION);

    /* Config first: mesh_master_init() reads g_cfg.mesh_channel. */
    init_nvs_config();
    ESP_ERROR_CHECK(mesh_master_init());

    ESP_ERROR_CHECK(spi_master_init());
    mesh_master_on_receive(on_student_message);

    ESP_LOGI(TAG, "S3 ready — mesh root + SPI master active");

    /* App rollback: an image booted for the first time after OTA is
     * PENDING_VERIFY. Only keep it once mesh + SPI came up (a crash before
     * this point makes the bootloader revert to the previous image). */
    const esp_partition_t *running = esp_ota_get_running_partition();
    esp_ota_img_states_t ota_state;
    if (esp_ota_get_state_partition(running, &ota_state) == ESP_OK &&
        ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
        esp_ota_mark_app_valid_cancel_rollback();
        ESP_LOGI(TAG, "New firmware verified — rollback cancelled");
    }

    /* Start tasks */
    xTaskCreate(spi_link_task, "spi_link", 4096, NULL, 5, NULL);
    xTaskCreate(heartbeat_task, "heartbeat", 2048, NULL, 3, NULL);

    /* Main loop: periodic status logging */
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        ESP_LOGI(TAG, "Students in mesh: %d", mesh_master_get_student_count());
    }
}