/**
 * @file spi_master.c
 * @brief ESP32-S3 SPI master for S3 <-> C6 communication.
 *
 * Fixed 4096-byte full-duplex SPI slots.
 *
 * Slot format:
 *   [0..1]       LEN, big-endian uint16
 *   [2..2+LEN)   PAYLOAD
 *   [2+LEN..]    CRC16/XMODEM, big-endian
 *   remaining    zero padding
 *
 * S3 is always the SPI master and therefore provides the clock.
 *
 * READY lines:
 *
 *   PIN_READY_S3_TO_C6:
 *       S3 -> C6
 *       HIGH means S3 has one or more frames waiting.
 *
 *   PIN_READY_C6_TO_S3:
 *       C6 -> S3
 *       HIGH means C6 has a frame waiting.
 *
 * The READY lines are only used as availability indicators.
 * SPI itself is always controlled by the S3 master.
 */

#include "spi_master.h"
#include "config.h"

#include <string.h>
#include <stdbool.h>
#include <stdint.h>

#include "esp_log.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "spi_master";

/* --------------------------------------------------------------------------
 * Configuration
 * -------------------------------------------------------------------------- */

#define SPI_TX_QUEUE_DEPTH 8

/* --------------------------------------------------------------------------
 * SPI handles / synchronization
 * -------------------------------------------------------------------------- */

static spi_device_handle_t s_spi_handle;
static SemaphoreHandle_t s_spi_mutex;
static SemaphoreHandle_t s_link_signal;

/* --------------------------------------------------------------------------
 * Active SPI buffers
 *
 * These buffers must not be modified while spi_device_polling_transmit()
 * owns them.
 * -------------------------------------------------------------------------- */

static uint8_t s_tx_slot[SPI_SLOT_BYTES]
    __attribute__((aligned(4)));

static uint8_t s_rx_slot[SPI_SLOT_BYTES]
    __attribute__((aligned(4)));

/* --------------------------------------------------------------------------
 * S3 -> C6 software TX queue
 * -------------------------------------------------------------------------- */

static uint8_t s_tx_queue[SPI_TX_QUEUE_DEPTH][SPI_SLOT_BYTES]
    __attribute__((aligned(4)));

static size_t s_tx_queue_len[SPI_TX_QUEUE_DEPTH];

static volatile uint8_t s_tx_head = 0;
static volatile uint8_t s_tx_tail = 0;
static volatile uint8_t s_tx_count = 0;

/* --------------------------------------------------------------------------
 * Received C6 payload
 * -------------------------------------------------------------------------- */

static uint8_t s_rx_payload[SPI_SLOT_BYTES - 4]
    __attribute__((aligned(4)));

static size_t s_rx_payload_len = 0;

/* --------------------------------------------------------------------------
 * CRC-16/XMODEM
 *
 * Polynomial: 0x1021
 * Initial value: 0xFFFF
 * Wire order: big endian
 * -------------------------------------------------------------------------- */

static uint16_t crc16_local(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;

    for (size_t i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i] << 8);

        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (uint16_t)((crc << 1) ^ 0x1021);
            } else {
                crc <<= 1;
            }
        }
    }

    return crc;
}

/* --------------------------------------------------------------------------
 * READY signal
 * -------------------------------------------------------------------------- */

static void update_s3_ready(void)
{
    gpio_set_level(
        PIN_READY_S3_TO_C6,
        (s_tx_count > 0) ? 1 : 0
    );
}

/* --------------------------------------------------------------------------
 * Init
 * -------------------------------------------------------------------------- */

int spi_master_init(void)
{
    s_spi_mutex = xSemaphoreCreateMutex();
    s_link_signal = xSemaphoreCreateBinary();

    if (s_spi_mutex == NULL || s_link_signal == NULL) {
        ESP_LOGE(TAG, "Failed to create SPI synchronization objects");
        return -1;
    }

    memset(s_tx_slot, 0, sizeof(s_tx_slot));
    memset(s_rx_slot, 0, sizeof(s_rx_slot));
    memset(s_rx_payload, 0, sizeof(s_rx_payload));

    s_tx_head = 0;
    s_tx_tail = 0;
    s_tx_count = 0;
    s_rx_payload_len = 0;

    /* --------------------------------------------------------------
     * S3 -> C6 READY
     * -------------------------------------------------------------- */

    gpio_config_t s3_out = {
        .pin_bit_mask = (1ULL << PIN_READY_S3_TO_C6),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };

    gpio_config(&s3_out);

    gpio_set_level(PIN_READY_S3_TO_C6, 0);

    /* --------------------------------------------------------------
     * C6 -> S3 READY
     * -------------------------------------------------------------- */

    gpio_config_t c6_in = {
        .pin_bit_mask = (1ULL << PIN_READY_C6_TO_S3),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };

    gpio_config(&c6_in);

    /* --------------------------------------------------------------
     * SPI bus
     * -------------------------------------------------------------- */

    spi_bus_config_t bus_cfg = {
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .sclk_io_num = PIN_SPI_SCLK,

        .quadwp_io_num = -1,
        .quadhd_io_num = -1,

        .max_transfer_sz = SPI_SLOT_BYTES,

        .flags = 0,
    };

    spi_device_interface_config_t dev_cfg = {
        .clock_speed_hz = SPI_CLOCK_HZ,
        .mode = 0,
        .spics_io_num = PIN_SPI_CS,
        .queue_size = 1,
        .flags = 0,
    };

    esp_err_t ret;

    ret = spi_bus_initialize(
        SPI_HOST,
        &bus_cfg,
        SPI_DMA_CHAN
    );

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI bus init failed: %d", ret);
        return -1;
    }

    ret = spi_bus_add_device(
        SPI_HOST,
        &dev_cfg,
        &s_spi_handle
    );

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI add device failed: %d", ret);
        return -1;
    }

    ESP_LOGI(
        TAG,
        "SPI master initialized, clock: %lu Hz, slot: %d bytes",
        (unsigned long)SPI_CLOCK_HZ,
        SPI_SLOT_BYTES
    );

    return 0;
}

/* --------------------------------------------------------------------------
 * Queue S3 -> C6 frame
 * -------------------------------------------------------------------------- */

int spi_master_send(const uint8_t *data, size_t len)
{
    if (len > SPI_SLOT_BYTES - 4) {
        ESP_LOGE(
            TAG,
            "Send too large: %u bytes (max %u)",
            (unsigned)len,
            (unsigned)(SPI_SLOT_BYTES - 4)
        );

        return -1;
    }

    if (data == NULL && len > 0) {
        return -1;
    }

    xSemaphoreTake(s_spi_mutex, portMAX_DELAY);

    if (s_tx_count >= SPI_TX_QUEUE_DEPTH) {
        xSemaphoreGive(s_spi_mutex);

        ESP_LOGW(
            TAG,
            "SPI TX queue full, dropping frame (%u bytes)",
            (unsigned)len
        );

        return -2;
    }

    uint8_t slot = s_tx_tail;

    memset(
        s_tx_queue[slot],
        0,
        SPI_SLOT_BYTES
    );

    /* LEN */
    s_tx_queue[slot][0] =
        (uint8_t)((len >> 8) & 0xFF);

    s_tx_queue[slot][1] =
        (uint8_t)(len & 0xFF);

    /* PAYLOAD */
    if (len > 0) {
        memcpy(
            &s_tx_queue[slot][2],
            data,
            len
        );
    }

    /* CRC */
    uint16_t crc = crc16_local(data, len);

    s_tx_queue[slot][2 + len] =
        (uint8_t)((crc >> 8) & 0xFF);

    s_tx_queue[slot][3 + len] =
        (uint8_t)(crc & 0xFF);

    s_tx_queue_len[slot] = len;

    s_tx_tail =
        (uint8_t)((s_tx_tail + 1) % SPI_TX_QUEUE_DEPTH);

    s_tx_count++;

    update_s3_ready();

    xSemaphoreGive(s_spi_mutex);

    /* Wake the SPI link task if it is waiting. */
    xSemaphoreGive(s_link_signal);

    ESP_LOGD(
        TAG,
        "SPI TX queued: %u bytes, queue=%u",
        (unsigned)len,
        (unsigned)s_tx_count
    );

    return 0;
}

/* --------------------------------------------------------------------------
 * C6 READY state
 * -------------------------------------------------------------------------- */

bool spi_master_c6_has_data(void)
{
    return gpio_get_level(PIN_READY_C6_TO_S3) != 0;
}

/* --------------------------------------------------------------------------
 * S3 TX pending
 * -------------------------------------------------------------------------- */

bool spi_master_tx_pending(void)
{
    return s_tx_count > 0;
}

/* --------------------------------------------------------------------------
 * Link semaphore
 * -------------------------------------------------------------------------- */

SemaphoreHandle_t spi_master_link_signal(void)
{
    return s_link_signal;
}

/* --------------------------------------------------------------------------
 * One full-duplex SPI transaction
 * -------------------------------------------------------------------------- */

bool spi_master_poll(void)
{
    xSemaphoreTake(s_spi_mutex, portMAX_DELAY);

    /*
     * Select the next S3 -> C6 packet.
     *
     * If nothing is queued, transmit an empty slot.
     */
    if (s_tx_count > 0) {
        memcpy(
            s_tx_slot,
            s_tx_queue[s_tx_head],
            SPI_SLOT_BYTES
        );
    } else {
        memset(
            s_tx_slot,
            0,
            SPI_SLOT_BYTES
        );
    }

    memset(
        s_rx_slot,
        0,
        SPI_SLOT_BYTES
    );

    /*
     * Once copied into s_tx_slot, the queue entry is no longer needed
     * for this transaction.
     */
    if (s_tx_count > 0) {
        s_tx_head =
            (uint8_t)((s_tx_head + 1) % SPI_TX_QUEUE_DEPTH);

        s_tx_count--;

        update_s3_ready();
    }

    xSemaphoreGive(s_spi_mutex);

    /* --------------------------------------------------------------
     * Full-duplex transfer
     * -------------------------------------------------------------- */

    spi_transaction_t t = {
        .length = SPI_SLOT_BYTES * 8,
        .tx_buffer = s_tx_slot,
        .rx_buffer = s_rx_slot,
    };

    esp_err_t ret =
        spi_device_polling_transmit(
            s_spi_handle,
            &t
        );

    if (ret != ESP_OK) {
        ESP_LOGE(
            TAG,
            "SPI slot transfer failed: %d",
            ret
        );

        memset(s_tx_slot, 0, sizeof(s_tx_slot));

        return false;
    }

    memset(
        s_tx_slot,
        0,
        sizeof(s_tx_slot)
    );

    /* --------------------------------------------------------------
     * Validate C6 response
     * -------------------------------------------------------------- */

    s_rx_payload_len = 0;

    uint16_t rx_len =
        ((uint16_t)s_rx_slot[0] << 8) |
        s_rx_slot[1];

    if (rx_len == 0) {
        return false;
    }

    if (rx_len > SPI_SLOT_BYTES - 4) {
        ESP_LOGW(
            TAG,
            "Invalid C6 RX length: %u",
            (unsigned)rx_len
        );

        return false;
    }

    uint16_t got_crc =
        ((uint16_t)s_rx_slot[2 + rx_len] << 8) |
        s_rx_slot[3 + rx_len];

    uint16_t calc_crc =
        crc16_local(
            &s_rx_slot[2],
            rx_len
        );

    if (got_crc != calc_crc) {
        ESP_LOGW(
            TAG,
            "C6 slot CRC mismatch: expected 0x%04X, got 0x%04X",
            (unsigned)calc_crc,
            (unsigned)got_crc
        );

        return false;
    }

    memcpy(
        s_rx_payload,
        &s_rx_slot[2],
        rx_len
    );

    s_rx_payload_len = rx_len;

    return true;
}

/* --------------------------------------------------------------------------
 * Copy received C6 payload
 * -------------------------------------------------------------------------- */

int spi_master_rx_copy(
    uint8_t *buf,
    size_t buf_size
)
{
    if (buf == NULL || buf_size == 0) {
        return 0;
    }

    size_t n = s_rx_payload_len;

    if (n > buf_size) {
        n = buf_size;
    }

    if (n > 0) {
        memcpy(
            buf,
            s_rx_payload,
            n
        );

        s_rx_payload_len = 0;
    }

    return (int)n;
}