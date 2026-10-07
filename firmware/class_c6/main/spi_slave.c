/**
 * @file spi_slave.c
 * @brief SPI slave driver for C6 — S3 communication (dual-ready, fixed 4096 slot).
 *
 * Protocol (mirror of S3 master, see S3 config.h):
 *   - One full-duplex 4096-byte slot exchange per transaction. C6 keeps a
 *     single 4 KB transaction queued (rx_slot + tx_slot); S3 always clocks.
 *   - Ready lines, ACTIVE HIGH, idle LOW:
 *       PIN_READY_S3_TO_C6 (GPIO4)  INPUT : S3 asserts while it holds a
 *                                          frame unconsumed; we ignore it
 *                                          (full-duplex: S3 clocks anyway).
 *       PIN_READY_C6_TO_S3 (GPIO2)  OUTPUT: WE assert while our tx slot holds
 *                                          a payload S3 has not clocked yet.
 *   - Slot format, both directions:
 *       [0..1]  LEN, big-endian uint16 (payload length 0..4092)
 *       [2..2+LEN-1]  PAYLOAD
 *       [2+LEN..3+LEN]  CRC16 over PAYLOAD ONLY, big-endian (XMODEM)
 *       [4+LEN..4095]  zero padding; an all-zero slot = no payload.
 */

#include "spi_slave.h"
#include "config.h"

#include <string.h>
#include "esp_log.h"
#include "driver/spi_slave.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "spi_slave";

/* ── DMA-capable slot buffers (4 KB each, required for SPI slave) ──── */
static uint8_t s_slot_rx[SPI_SLOT_BYTES] __attribute__((aligned(4)));
static uint8_t s_slot_tx[SPI_SLOT_BYTES] __attribute__((aligned(4)));

static SemaphoreHandle_t s_rx_sem;
static volatile bool s_has_data = false;

/* Outgoing payload: LEN + payload + CRC inside s_slot_tx[0..3+LEN]. */
static volatile size_t s_tx_len = 0;
static SemaphoreHandle_t s_tx_mutex;

/* Latest-wins tracking for the C6→S3 ready line:
 *   s_post_gen increments on every send() post.
 *   post_setup_cb snapshots the generation the DMA is about to clock.
 *   post_trans_cb compares: if nothing newer was posted mid-flight, the
 *   slot just consumed is the latest post → clear it + drop ready. */
static volatile uint32_t s_post_gen = 0;
static volatile uint32_t s_setup_gen = 0;
static volatile bool s_ready_asserted = false;

static void ready_set(bool level)
{
    gpio_set_level(PIN_READY_C6_TO_S3, level ? 1 : 0);
    s_ready_asserted = level;
}

/* ── CRC-16/XMODEM over data only ──────────────────────────────────── */

static uint16_t crc16_local(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000)
                crc = (crc << 1) ^ 0x1021;
            else
                crc <<= 1;
        }
    }
    return crc;
}

/* ── Queue the persistent full-duplex slot transaction ─────────────── */

/* The driver keeps this POINTER until the S3 clocks the slot, reads it from
 * the ISR and writes trans_len back into it, so it must not live on a stack.
 * Exactly one transaction is in flight at a time (see spi_slave_read). */
static spi_slave_transaction_t s_trans;

static void queue_slot(void)
{
    s_trans = (spi_slave_transaction_t){
        .length = SPI_SLOT_BYTES * 8,
        .rx_buffer = s_slot_rx,
        .tx_buffer = s_slot_tx,
    };
    spi_slave_queue_trans(SPI_HOST, &s_trans, portMAX_DELAY);
}

static void IRAM_ATTR spi_post_setup_cb(spi_slave_transaction_t *trans)
{
    /* S3 pulled CS low: the DMA is about to clock the current tx slot. */
    (void)trans;
    s_setup_gen = s_post_gen;
}

static void IRAM_ATTR spi_post_trans_cb(spi_slave_transaction_t *trans)
{
    /* This exchange consumed whatever s_slot_tx showed at setup time. */
    if (s_setup_gen == s_post_gen && s_tx_len > 0) {
        /* Latest post fully clocked out → clear slot, drop ready. */
        memset(s_slot_tx, 0, sizeof(s_slot_tx));
        s_tx_len = 0;
        ready_set(false);
    }

    if (trans->trans_len > 0) {
        uint8_t *rx = (uint8_t *)trans->rx_buffer;
        uint16_t len = ((uint16_t)rx[0] << 8) | rx[1];
        if (len > 0 && len <= SPI_SLOT_BYTES - 4) {
            uint16_t rx_crc = ((uint16_t)rx[2 + len] << 8) | rx[3 + len];
            uint16_t calc_crc = crc16_local(rx + 2, len);  /* payload only */
            if (rx_crc == calc_crc) {
                s_has_data = true;
                xSemaphoreGiveFromISR(s_rx_sem, NULL);
            }
        }
    }
}

/* ── Init ──────────────────────────────────────────────────────────── */

int spi_slave_init(void)
{
    s_rx_sem = xSemaphoreCreateBinary();
    s_tx_mutex = xSemaphoreCreateMutex();

    memset(s_slot_rx, 0, sizeof(s_slot_rx));
    memset(s_slot_tx, 0, sizeof(s_slot_tx));

    /* Ready lines: S3→C6 is input (informational), C6→S3 is output. */
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
        .quadwp_io_num = PIN_SPI_WP,
        .quadhd_io_num = PIN_SPI_HD,
        .max_transfer_sz = SPI_SLOT_BYTES,
        .flags = SPICOMMON_BUSFLAG_QUAD,
    };

    spi_slave_interface_config_t slave_cfg = {
        .spics_io_num = PIN_SPI_CS,
        .queue_size = 3,
        .mode = 0,
        .post_setup_cb = spi_post_setup_cb,
        .post_trans_cb = spi_post_trans_cb,
    };

    esp_err_t ret = spi_slave_initialize(SPI_HOST, &bus_cfg, &slave_cfg, SPI_DMA_CHAN);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI slave init failed: %d", ret);
        return -1;
    }

    queue_slot();

    ESP_LOGI(TAG, "SPI slave initialized (%u-byte dual-ready slot)",
             (unsigned)SPI_SLOT_BYTES);
    return 0;
}

/* ── Has Data ──────────────────────────────────────────────────────── */

bool spi_slave_has_data(void)
{
    return s_has_data;
}

/* ── Read ──────────────────────────────────────────────────────────── */

int spi_slave_read(uint8_t *buf, size_t buf_size)
{
    /* Re-arm only after the armed slot completed (reaping it is mandatory).
     * Re-queueing on every poll piled stale descriptors into the depth-3
     * queue and then blocked forever while the S3 was idle. */
    spi_slave_transaction_t *done;
    if (spi_slave_get_trans_result(SPI_HOST, &done, 0) != ESP_OK) {
        return 0;
    }

    int n = 0;
    if (s_has_data) {
        uint8_t *rx = s_slot_rx;
        uint16_t len = ((uint16_t)rx[0] << 8) | rx[1];
        n = (len < buf_size) ? len : buf_size;
        memcpy(buf, rx + 2, n);
        s_has_data = false;
    }

    /* Re-arm for the next S3 exchange (S3 bounded-wait covers the gap). */
    queue_slot();
    return n;
}

/* ── Send (post a payload slot for S3 to clock) ────────────────────── */

int spi_slave_send(const uint8_t *data, size_t len)
{
    if (len > SPI_SLOT_BYTES - 4) {
        ESP_LOGE(TAG, "Send too large: %d bytes", (int)len);
        return -1;
    }

    xSemaphoreTake(s_tx_mutex, portMAX_DELAY);

    memset(s_slot_tx, 0, sizeof(s_slot_tx));
    s_slot_tx[0] = (len >> 8) & 0xFF;
    s_slot_tx[1] = len & 0xFF;
    if (data && len > 0) {
        memcpy(s_slot_tx + 2, data, len);
    }
    uint16_t crc = crc16_local(s_slot_tx + 2, len);  /* payload only */
    s_slot_tx[2 + len] = (crc >> 8) & 0xFF;
    s_slot_tx[3 + len] = crc & 0xFF;
    s_tx_len = len;

    s_post_gen++;
    ready_set(true);

    xSemaphoreGive(s_tx_mutex);
    return 0;
}