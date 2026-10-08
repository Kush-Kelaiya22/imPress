/**
 * @file spi_slave.c
 * @brief SPI slave driver for C6 <-> S3 communication (fixed 4096-byte slots).
 *
 * Protocol (mirror of the S3 master; slot format in protocol.h):
 *   - Standard full-duplex SPI, mode 0, S3 = master and always clocks. The
 *     GPSPI slave driver only supports this mode; v2's quad/half-duplex master
 *     could never exchange slots with it (see docs/engineering).
 *   - Exactly one transaction is armed at a time (rx_slot + tx_slot). The
 *     DMA owns both buffers until spi_slave_read() reaps the result, so the
 *     tx slot is only rewritten between transactions.
 *   - Outgoing payloads wait in a FIFO (spi_slot_fifo_t): back-to-back sends
 *     are queued, never overwritten.
 *   - Ready lines, active high:
 *       PIN_READY_S3_TO_C6  INPUT : informational (the S3 clocks regardless).
 *       PIN_READY_C6_TO_S3  OUTPUT: high while our FIFO holds payloads.
 */

#include "spi_slave.h"
#include "config.h"
#include "protocol.h"

#include <string.h>
#include "esp_log.h"
#include "driver/spi_slave.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "spi_slave";

/* ── DMA buffers: owned by the driver while a transaction is armed ─── */
static uint8_t s_slot_rx[SPI_SLOT_BYTES] __attribute__((aligned(4)));
static uint8_t s_slot_tx[SPI_SLOT_BYTES] __attribute__((aligned(4)));

/* The driver keeps this POINTER until the S3 clocks the slot, reads it from
 * the ISR and writes trans_len back into it, so it must not live on a stack. */
static spi_slave_transaction_t s_trans;

static spi_slot_fifo_t s_txq;        /* C6 -> S3 payloads (guarded by s_tx_mutex) */
static bool s_tx_loaded = false;     /* s_slot_tx holds the FIFO head */
static SemaphoreHandle_t s_tx_mutex;
static SemaphoreHandle_t s_rx_sem;
static volatile bool s_has_data = false;
static uint32_t s_rx_errors = 0;

static void ready_update(void)
{
    gpio_set_level(PIN_READY_C6_TO_S3, spi_slot_fifo_count(&s_txq) ? 1 : 0);
}

static void queue_slot(void)
{
    s_trans = (spi_slave_transaction_t){
        .length = SPI_SLOT_BYTES * 8,
        .rx_buffer = s_slot_rx,
        .tx_buffer = s_slot_tx,
    };
    esp_err_t ret = spi_slave_queue_trans(SPI_HOST, &s_trans, portMAX_DELAY);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to arm SPI slot: %d", ret);
    }
}

/* ISR: only signal. Validation and copying happen in task context. */
static void IRAM_ATTR spi_post_trans_cb(spi_slave_transaction_t *trans)
{
    (void)trans;
    BaseType_t woken = pdFALSE;
    s_has_data = true;
    xSemaphoreGiveFromISR(s_rx_sem, &woken);
    if (woken) {
        portYIELD_FROM_ISR();
    }
}

/* ── Init ──────────────────────────────────────────────────────────── */

int spi_slave_init(void)
{
    s_rx_sem = xSemaphoreCreateBinary();
    s_tx_mutex = xSemaphoreCreateMutex();
    if (!s_rx_sem || !s_tx_mutex) {
        ESP_LOGE(TAG, "semaphore alloc failed");
        return -1;
    }

    memset(s_slot_rx, 0, sizeof(s_slot_rx));
    memset(s_slot_tx, 0, sizeof(s_slot_tx));
    spi_slot_fifo_init(&s_txq);
    s_tx_loaded = false;

    gpio_config_t in_cfg = {
        .pin_bit_mask = BIT(PIN_READY_S3_TO_C6),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&in_cfg);
    gpio_config_t out_cfg = {
        .pin_bit_mask = BIT(PIN_READY_C6_TO_S3),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&out_cfg);
    gpio_set_level(PIN_READY_C6_TO_S3, 0);

    spi_bus_config_t bus_cfg = {
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .sclk_io_num = PIN_SPI_SCLK,
        .quadwp_io_num = -1,             /* standard SPI: WP/HD unused */
        .quadhd_io_num = -1,
        .max_transfer_sz = SPI_SLOT_BYTES,
        .flags = 0,
    };
    spi_slave_interface_config_t slave_cfg = {
        .spics_io_num = PIN_SPI_CS,
        .queue_size = 1,                 /* one armed slot, never more */
        .mode = 0,
        .post_trans_cb = spi_post_trans_cb,
    };

    esp_err_t ret = spi_slave_initialize(SPI_HOST, &bus_cfg, &slave_cfg, SPI_DMA_CHAN);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI slave init failed: %d", ret);
        return -1;
    }

    queue_slot();
    ESP_LOGI(TAG, "SPI slave initialized (%u-byte full-duplex slot, %d-deep TX FIFO)",
             (unsigned)SPI_SLOT_BYTES, SPI_SLOT_FIFO_DEPTH);
    return 0;
}

bool spi_slave_has_data(void)
{
    return s_has_data;
}

/* ── Read: reap the armed slot, validate it, re-arm with the next TX ─── */

int spi_slave_read(uint8_t *buf, size_t buf_size)
{
    /* Re-arm only after the armed slot completed (reaping it is mandatory).
     * Re-queueing on every poll piled stale descriptors into the queue and
     * then blocked forever while the S3 was idle. */
    spi_slave_transaction_t *done;
    if (spi_slave_get_trans_result(SPI_HOST, &done, 0) != ESP_OK) {
        return 0;
    }
    s_has_data = false;

    int n = spi_slot_decode(s_slot_rx, buf, buf_size);
    if (n < 0) {
        s_rx_errors++;
        ESP_LOGW(TAG, "Dropped S3 slot (error %d, %lu total)", n, (unsigned long)s_rx_errors);
        n = 0;
    }

    /* The slot just clocked carried the FIFO head: it is delivered. */
    xSemaphoreTake(s_tx_mutex, portMAX_DELAY);
    if (s_tx_loaded) {
        spi_slot_fifo_drop(&s_txq);
    }
    s_tx_loaded = spi_slot_fifo_peek(&s_txq, s_slot_tx);
    ready_update();
    xSemaphoreGive(s_tx_mutex);

    queue_slot();
    return n;
}

/* ── Send: queue a payload for the S3 to clock ─────────────────────── */

int spi_slave_send(const uint8_t *data, size_t len)
{
    xSemaphoreTake(s_tx_mutex, portMAX_DELAY);
    int rc = spi_slot_fifo_push(&s_txq, data, len);
    ready_update();
    unsigned depth = spi_slot_fifo_count(&s_txq);
    xSemaphoreGive(s_tx_mutex);

    if (rc == SPI_SLOT_ERR_LEN) {
        ESP_LOGE(TAG, "Send too large: %d bytes (max %d)", (int)len, SPI_SLOT_PAYLOAD_MAX);
    } else if (rc != 0) {
        ESP_LOGW(TAG, "SPI TX FIFO full, dropped %d-byte frame", (int)len);
    } else {
        ESP_LOGD(TAG, "SPI TX queued: %d bytes, depth %u", (int)len, depth);
    }
    (void)depth;   /* only used by the debug log */
    return rc;
}
