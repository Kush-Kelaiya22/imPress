/**
 * @file spi_master.c
 * @brief SPI master driver for S3 → C6 communication.
 *
 * Fixed 4096-byte slot, full duplex, dual-ready handshake:
 *   R_S3 (GPIO4, S3 out, active high): "S3 frame queued push"
 *   R_C6 (GPIO2, S3 in, pull-down):    "C6 frame queued"
 *
 * Slot (identical both directions):
 *   [LEN:2 BE][PAYLOAD:LEN][CRC16 over PAYLOAD only:2][zero pad to SPI_SLOT_BYTES]
 *   LEN=0 => "no payload" (all zeros).
 */

#include "spi_master.h"
#include "config.h"

#include <string.h>
#include "esp_log.h"
#include "esp_intr_alloc.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "spi_master";

static spi_device_handle_t s_spi_handle;
static SemaphoreHandle_t s_spi_mutex;
static SemaphoreHandle_t s_link_signal;   /* given on TX queued / R_C6 rise */

static uint8_t s_tx_slot[SPI_SLOT_BYTES];
static uint8_t s_rx_slot[SPI_SLOT_BYTES];
static volatile bool s_tx_pending;
static uint8_t s_rx_payload[SPI_SLOT_BYTES - 4];
static size_t  s_rx_payload_len;

/* ── CRC-16 XMODEM (poly 0x1021, init 0xFFFF), big-endian on wire ───── */

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

/* R_C6 rising edge: C6 has queued a frame → wake the link task. */
static void IRAM_ATTR ready_c6_isr(void *arg)
{
    (void)arg;
    BaseType_t woken = pdFALSE;
    xSemaphoreGiveFromISR(s_link_signal, &woken);
    if (woken) {
        portYIELD_FROM_ISR();
    }
}

/* ── Init ──────────────────────────────────────────────────────────── */

int spi_master_init(void)
{
    s_spi_mutex = xSemaphoreCreateMutex();
    s_link_signal = xSemaphoreCreateBinary();
    if (!s_spi_mutex || !s_link_signal) {
        ESP_LOGE(TAG, "semaphore alloc failed");
        return -1;
    }

    /* R_S3: S3 drives it, initial low (idle). */
    gpio_config_t s3_out = {
        .pin_bit_mask = (1ULL << PIN_READY_S3_TO_C6),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&s3_out);
    gpio_set_level(PIN_READY_S3_TO_C6, 0);

    /* R_C6: S3 reads it, pull-down, positive-edge ISR (no blind polling). */
    gpio_config_t c6_in = {
        .pin_bit_mask = (1ULL << PIN_READY_C6_TO_S3),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_POSEDGE,
    };
    gpio_config(&c6_in);

    esp_err_t ir = gpio_install_isr_service(ESP_INTR_FLAG_LEVEL1 | ESP_INTR_FLAG_IRAM);
    if (ir != ESP_OK && ir != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "GPIO ISR service install failed: %d", ir);
        return -1;
    }
    gpio_isr_handler_add(PIN_READY_C6_TO_S3, ready_c6_isr, NULL);

    spi_bus_config_t bus_cfg = {
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .sclk_io_num = PIN_SPI_SCLK,
        .quadwp_io_num = PIN_SPI_WP,
        .quadhd_io_num = PIN_SPI_HD,
        .max_transfer_sz = SPI_TX_BUF_SIZE,
        .flags = SPICOMMON_BUSFLAG_QUAD,
    };

    spi_device_interface_config_t dev_cfg = {
        .clock_speed_hz = SPI_CLOCK_HZ,
        .mode = 0,                    /* SPI mode 0: CPOL=0, CPHA=0 */
        .spics_io_num = PIN_SPI_CS,
        .queue_size = 7,
        .flags = SPI_DEVICE_HALFDUPLEX,  /* not used, but required for quad */
    };

    esp_err_t ret;
    ret = spi_bus_initialize(SPI_HOST, &bus_cfg, SPI_DMA_CHAN);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI bus init failed: %d", ret);
        return -1;
    }

    ret = spi_bus_add_device(SPI_HOST, &dev_cfg, &s_spi_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI add device failed: %d", ret);
        return -1;
    }

    ESP_LOGI(TAG, "SPI master initialized, clock: %lu Hz, slot: %d bytes",
             (unsigned long)SPI_CLOCK_HZ, SPI_SLOT_BYTES);
    return 0;
}

/* ── Send (queue S3 slot, non-blocking) ────────────────────────────── */

int spi_master_send(const uint8_t *data, size_t len)
{
    if (len > SPI_SLOT_BYTES - 4) {
        ESP_LOGE(TAG, "Send too large: %u bytes (max %u)",
                 (unsigned)len, (unsigned)(SPI_SLOT_BYTES - 4));
        return -1;
    }

    xSemaphoreTake(s_spi_mutex, portMAX_DELAY);

    memset(s_tx_slot, 0, sizeof(s_tx_slot));
    if (data && len > 0) {
        s_tx_slot[0] = (uint8_t)(len >> 8);
        s_tx_slot[1] = (uint8_t)(len & 0xFF);
        memcpy(&s_tx_slot[2], data, len);
        uint16_t crc = crc16_local(data, len);   /* CRC over PAYLOAD only */
        s_tx_slot[2 + len] = (uint8_t)(crc >> 8);
        s_tx_slot[3 + len] = (uint8_t)(crc & 0xFF);
    }
    s_tx_pending = true;
    gpio_set_level(PIN_READY_S3_TO_C6, 1);       /* keep asserted until consumed */
    xSemaphoreGive(s_spi_mutex);

    xSemaphoreGive(s_link_signal);               /* wake coordinator */
    return 0;
}

/* ── Ready / state queries ─────────────────────────────────────────── */

bool spi_master_c6_has_data(void)
{
    return gpio_get_level(PIN_READY_C6_TO_S3) != 0;
}

bool spi_master_tx_pending(void)
{
    return s_tx_pending;
}

SemaphoreHandle_t spi_master_link_signal(void)
{
    return s_link_signal;
}

/* ── Poll (one fixed-slot full-duplex transfer) ────────────────────── */

bool spi_master_poll(void)
{
    xSemaphoreTake(s_spi_mutex, portMAX_DELAY);

    if (!s_tx_pending) {
        memset(s_tx_slot, 0, sizeof(s_tx_slot));   /* send empty slot */
    }
    memset(s_rx_slot, 0, sizeof(s_rx_slot));

    spi_transaction_t t = {
        .length = SPI_SLOT_BYTES * 8,              /* full duplex, 4096 bytes */
        .tx_buffer = s_tx_slot,
        .rx_buffer = s_rx_slot,
    };

    esp_err_t ret = spi_device_polling_transmit(s_spi_handle, &t);

    /* Slot consumed: clear S3 slot and de-assert R_S3. */
    memset(s_tx_slot, 0, sizeof(s_tx_slot));
    s_tx_pending = false;
    gpio_set_level(PIN_READY_S3_TO_C6, 0);
    s_rx_payload_len = 0;

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI slot transfer failed: %d", ret);
        xSemaphoreGive(s_spi_mutex);
        return false;
    }

    uint16_t rx_len = ((uint16_t)s_rx_slot[0] << 8) | s_rx_slot[1];
    bool valid = false;
    if (rx_len > 0 && rx_len <= SPI_SLOT_BYTES - 4) {
        uint16_t got = ((uint16_t)s_rx_slot[2 + rx_len] << 8) | s_rx_slot[3 + rx_len];
        uint16_t calc = crc16_local(&s_rx_slot[2], rx_len);
        if (got == calc) {
            s_rx_payload_len = rx_len;
            memcpy(s_rx_payload, &s_rx_slot[2], rx_len);
            valid = true;
        } else {
            ESP_LOGW(TAG, "C6 slot CRC mismatch: expected 0x%04X, got 0x%04X",
                     (unsigned)calc, (unsigned)got);
        }
    }

    xSemaphoreGive(s_spi_mutex);
    return valid;
}

int spi_master_rx_copy(uint8_t *buf, size_t buf_size)
{
    size_t n = s_rx_payload_len;
    if (n > buf_size) {
        n = buf_size;
    }
    if (n > 0) {
        memcpy(buf, s_rx_payload, n);
    }
    return (int)n;
}