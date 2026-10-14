/**
 * @file spi_master.c
 * @brief SPI master driver for S3 <-> C6 communication (fixed 4096-byte slots).
 *
 *   - Standard full-duplex SPI, mode 0, clock CONFIG_SPI_CLOCK_MHZ (default
 *     10 MHz). One transfer moves one slot each way; slot format and the
 *     outgoing FIFO are shared with the C6 (protocol.h).
 *   - The link task clocks a slot on every poll interval, and immediately
 *     when spi_master_send() queues something, so it never depends on
 *     catching a ready-line edge.
 *   - Ready lines, active high:
 *       R_S3 (PIN_READY_S3_TO_C6, output): high while our FIFO holds payloads.
 *       R_C6 (PIN_READY_C6_TO_S3, input, pull-down): informational.
 *   - A queued payload leaves the FIFO only after a transfer succeeded.
 */

#include "spi_master.h"
#include "config.h"
#include "protocol.h"
#include "spi_link.h"

#include <string.h>
#include "esp_log.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_random.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "spi_master";

static spi_device_handle_t s_spi_handle;
static SemaphoreHandle_t s_spi_mutex;     /* guards s_txq */
static SemaphoreHandle_t s_link_signal;   /* given when a payload is queued */

/* DMA buffers: only touched by the link task around a transfer. */
static uint8_t s_tx_slot[SPI_SLOT_BYTES] __attribute__((aligned(4)));
static uint8_t s_rx_slot[SPI_SLOT_BYTES] __attribute__((aligned(4)));

static spi_slot_fifo_t s_txq;             /* S3 -> C6 payloads */
static uint8_t s_rx_payload[SPI_SLOT_PAYLOAD_MAX];
static size_t  s_rx_payload_len;
static uint32_t s_rx_errors;

/* Acknowledged slots (#182): the hub always sends the trailer; a gateway
 * that answers with one acknowledges, an old one simply ignores it. */
static spi_link_t s_link;
static uint8_t s_head_slot[SPI_SLOT_BYTES];          /* FIFO head, encoded */
static uint8_t s_head[SPI_SLOT_PAYLOAD_MAX];
static uint8_t s_out[SPI_SLOT_PAYLOAD_MAX];

static void ready_update(void)
{
    gpio_set_level(PIN_READY_S3_TO_C6, spi_slot_fifo_count(&s_txq) ? 1 : 0);
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
    spi_slot_fifo_init(&s_txq);
    s_rx_payload_len = 0;
    spi_link_init(&s_link, (uint8_t)(1 + esp_random() % 255), true);

    gpio_config_t s3_out = {
        .pin_bit_mask = (1ULL << PIN_READY_S3_TO_C6),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&s3_out);
    gpio_set_level(PIN_READY_S3_TO_C6, 0);

    gpio_config_t c6_in = {
        .pin_bit_mask = (1ULL << PIN_READY_C6_TO_S3),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&c6_in);

    spi_bus_config_t bus_cfg = {
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .sclk_io_num = PIN_SPI_SCLK,
        .quadwp_io_num = -1,             /* standard SPI: WP/HD unused */
        .quadhd_io_num = -1,
        .max_transfer_sz = SPI_SLOT_BYTES,
        .flags = 0,
    };
    spi_device_interface_config_t dev_cfg = {
        .clock_speed_hz = SPI_CLOCK_HZ,
        .mode = 0,                       /* CPOL=0, CPHA=0 */
        .spics_io_num = PIN_SPI_CS,
        .queue_size = 1,
        .flags = 0,                      /* full duplex */
    };

    esp_err_t ret = spi_bus_initialize(SPI_HOST, &bus_cfg, SPI_DMA_CHAN);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI bus init failed: %d", ret);
        return -1;
    }
    ret = spi_bus_add_device(SPI_HOST, &dev_cfg, &s_spi_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI add device failed: %d", ret);
        return -1;
    }

    ESP_LOGI(TAG, "SPI master initialized, clock: %lu Hz, slot: %d bytes, TX FIFO: %d",
             (unsigned long)SPI_CLOCK_HZ, SPI_SLOT_BYTES, SPI_SLOT_FIFO_DEPTH);
    return 0;
}

/* ── Send (queue a payload, non-blocking) ──────────────────────────── */

int spi_master_send(const uint8_t *data, size_t len)
{
    if (len > SPI_SLOT_PAYLOAD_MAX - SPI_LINK_TRAILER) {   /* room for the link trailer (#182) */
        ESP_LOGE(TAG, "Send too large: %u bytes (max %u)",
                 (unsigned)len, (unsigned)(SPI_SLOT_PAYLOAD_MAX - SPI_LINK_TRAILER));
        return SPI_SLOT_ERR_LEN;
    }
    xSemaphoreTake(s_spi_mutex, portMAX_DELAY);
    int rc = spi_slot_fifo_push(&s_txq, data, len);
    ready_update();
    xSemaphoreGive(s_spi_mutex);

    if (rc == SPI_SLOT_ERR_LEN) {
        ESP_LOGE(TAG, "Send too large: %u bytes (max %u)",
                 (unsigned)len, (unsigned)SPI_SLOT_PAYLOAD_MAX);
        return rc;
    }
    if (rc != 0) {
        ESP_LOGW(TAG, "SPI TX FIFO full, dropped %u-byte frame", (unsigned)len);
        return rc;
    }
    xSemaphoreGive(s_link_signal);       /* wake the link task now */
    return 0;
}

bool spi_master_c6_has_data(void)
{
    return gpio_get_level(PIN_READY_C6_TO_S3) != 0;
}

bool spi_master_tx_pending(void)
{
    return spi_slot_fifo_count(&s_txq) > 0;
}

SemaphoreHandle_t spi_master_link_signal(void)
{
    return s_link_signal;
}

/* ── Poll (one fixed-slot full-duplex transfer) ────────────────────── */

bool spi_master_poll(void)
{
    xSemaphoreTake(s_spi_mutex, portMAX_DELAY);
    bool sending = spi_slot_fifo_peek(&s_txq, s_head_slot);   /* zero slot if empty */
    xSemaphoreGive(s_spi_mutex);
    int head_len = sending ? spi_slot_decode(s_head_slot, s_head, sizeof s_head) : 0;
    if (head_len < 0) {                                       /* our own queue: cannot happen */
        sending = false;
        head_len = 0;
    }
    /* The FIFO head (kept until the C6 acknowledges it) plus the trailer. */
    int out_len = spi_link_tx(&s_link, sending ? s_head : NULL, (size_t)head_len, s_out, sizeof s_out);
    if (out_len < 0) {                                        /* refused at send time; never too large */
        out_len = 0;
        sending = false;
    }
    spi_slot_encode(s_tx_slot, s_out, (size_t)out_len);
    memset(s_rx_slot, 0, sizeof(s_rx_slot));

    spi_transaction_t t = {
        .length = SPI_SLOT_BYTES * 8,
        .tx_buffer = s_tx_slot,
        .rx_buffer = s_rx_slot,
    };
    esp_err_t ret = spi_device_polling_transmit(s_spi_handle, &t);
    s_rx_payload_len = 0;
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "SPI slot transfer failed: %d (payload kept for retry)", ret);
        return false;
    }

    int n = spi_slot_decode(s_rx_slot, s_rx_payload, sizeof(s_rx_payload));
    bool acked = false;
    if (n < 0) {
        s_rx_errors++;
        ESP_LOGW(TAG, "Dropped C6 slot (error %d, %lu total)%s", n, (unsigned long)s_rx_errors,
                 s_link.peer ? ": the C6 resends it" : "");
    } else {
        n = (int)spi_link_rx(&s_link, s_rx_payload, (size_t)n, &acked);   /* strips the trailer, drops repeats */
    }

    /* Leave the FIFO only once delivered: acknowledged by a C6 that does so
     * (#182), or clocked out to one that doesn't. */
    if (spi_link_drop_head(&s_link, sending, acked)) {
        xSemaphoreTake(s_spi_mutex, portMAX_DELAY);
        spi_slot_fifo_drop(&s_txq);
        ready_update();
        xSemaphoreGive(s_spi_mutex);
    }
    if (n <= 0) {
        return false;
    }
    s_rx_payload_len = (size_t)n;
    return true;
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
    s_rx_payload_len = 0;
    return (int)n;
}
