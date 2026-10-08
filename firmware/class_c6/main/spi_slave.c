/**
 * @file spi_slave.c
 * @brief ESP32-C6 SPI slave for S3 <-> C6 communication.
 *
 * Fixed 4096-byte full-duplex SPI slots.
 *
 * Slot format:
 *   [0..1]       LEN, big-endian uint16
 *   [2..2+LEN)   PAYLOAD
 *   [2+LEN..]    CRC16/XMODEM, big-endian
 *   remaining    zero padding
 *
 * S3 is the SPI master and always provides the clock.
 *
 * READY lines:
 *
 *   PIN_READY_S3_TO_C6:
 *       S3 -> C6
 *       HIGH means S3 has data waiting.
 *
 *   PIN_READY_C6_TO_S3:
 *       C6 -> S3
 *       HIGH means C6 has one or more frames waiting.
 */

#include "spi_slave.h"
#include "config.h"

#include <string.h>
#include <stdbool.h>
#include <stdint.h>

#include "esp_log.h"
#include "driver/spi_slave.h"
#include "driver/gpio.h"

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const char *TAG = "spi_slave";

/* --------------------------------------------------------------------------
 * Configuration
 * -------------------------------------------------------------------------- */

#define SPI_TX_QUEUE_DEPTH 8

/* --------------------------------------------------------------------------
 * Active DMA buffers
 *
 * These buffers MUST NOT be modified while the SPI transaction is queued.
 * -------------------------------------------------------------------------- */

static uint8_t s_slot_rx[SPI_SLOT_BYTES]
    __attribute__((aligned(4)));

static uint8_t s_slot_tx[SPI_SLOT_BYTES]
    __attribute__((aligned(4)));

/* --------------------------------------------------------------------------
 * C6 -> S3 software TX queue
 * -------------------------------------------------------------------------- */

static uint8_t s_tx_queue[SPI_TX_QUEUE_DEPTH][SPI_SLOT_BYTES]
    __attribute__((aligned(4)));

static size_t s_tx_queue_len[SPI_TX_QUEUE_DEPTH];

static volatile uint8_t s_tx_head = 0;
static volatile uint8_t s_tx_tail = 0;
static volatile uint8_t s_tx_count = 0;

/* --------------------------------------------------------------------------
 * Synchronization
 * -------------------------------------------------------------------------- */

static SemaphoreHandle_t s_rx_sem;
static SemaphoreHandle_t s_tx_mutex;

/* --------------------------------------------------------------------------
 * Received data state
 * -------------------------------------------------------------------------- */

static volatile bool s_has_data = false;

/* --------------------------------------------------------------------------
 * Persistent SPI transaction
 * -------------------------------------------------------------------------- */

static spi_slave_transaction_t s_trans;

/* --------------------------------------------------------------------------
 * CRC-16/XMODEM
 * -------------------------------------------------------------------------- */

static uint16_t crc16_local(
    const uint8_t *data,
    size_t len
)
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
 * READY line
 * -------------------------------------------------------------------------- */

static void update_c6_ready(void)
{
    gpio_set_level(
        PIN_READY_C6_TO_S3,
        (s_tx_count > 0) ? 1 : 0
    );
}

/* --------------------------------------------------------------------------
 * Queue one SPI transaction
 * -------------------------------------------------------------------------- */

static void queue_slot(void)
{
    s_trans = (spi_slave_transaction_t) {
        .length = SPI_SLOT_BYTES * 8,
        .rx_buffer = s_slot_rx,
        .tx_buffer = s_slot_tx,
    };

    esp_err_t ret =
        spi_slave_queue_trans(
            SPI_HOST,
            &s_trans,
            portMAX_DELAY
        );

    if (ret != ESP_OK) {
        ESP_LOGE(
            TAG,
            "Failed to queue SPI transaction: %d",
            ret
        );
    }
}

/* --------------------------------------------------------------------------
 * SPI setup callback
 *
 * Nothing complicated should happen here.
 * -------------------------------------------------------------------------- */

static void IRAM_ATTR spi_post_setup_cb(
    spi_slave_transaction_t *trans
)
{
    (void)trans;
}

/* --------------------------------------------------------------------------
 * SPI transaction callback
 *
 * Only signal that a transaction completed.
 * All buffer manipulation is done from the normal task context.
 * -------------------------------------------------------------------------- */

static void IRAM_ATTR spi_post_trans_cb(
    spi_slave_transaction_t *trans
)
{
    (void)trans;

    BaseType_t hp_task_woken = pdFALSE;

    s_has_data = true;

    if (s_rx_sem != NULL) {
        xSemaphoreGiveFromISR(
            s_rx_sem,
            &hp_task_woken
        );
    }

    if (hp_task_woken) {
        portYIELD_FROM_ISR();
    }
}

/* --------------------------------------------------------------------------
 * Init
 * -------------------------------------------------------------------------- */

int spi_slave_init(void)
{
    s_rx_sem = xSemaphoreCreateBinary();
    s_tx_mutex = xSemaphoreCreateMutex();

    if (s_rx_sem == NULL || s_tx_mutex == NULL) {
        ESP_LOGE(
            TAG,
            "Failed to create SPI synchronization objects"
        );

        return -1;
    }

    memset(
        s_slot_rx,
        0,
        sizeof(s_slot_rx)
    );

    memset(
        s_slot_tx,
        0,
        sizeof(s_slot_tx)
    );

    memset(
        s_tx_queue,
        0,
        sizeof(s_tx_queue)
    );

    s_tx_head = 0;
    s_tx_tail = 0;
    s_tx_count = 0;
    s_has_data = false;

    /* --------------------------------------------------------------
     * READY: S3 -> C6
     * -------------------------------------------------------------- */

    gpio_config_t in_cfg = {
        .pin_bit_mask =
            (1ULL << PIN_READY_S3_TO_C6),

        .mode = GPIO_MODE_INPUT,

        .pull_up_en =
            GPIO_PULLUP_DISABLE,

        .pull_down_en =
            GPIO_PULLDOWN_DISABLE,

        .intr_type =
            GPIO_INTR_DISABLE,
    };

    gpio_config(&in_cfg);

    /* --------------------------------------------------------------
     * READY: C6 -> S3
     * -------------------------------------------------------------- */

    gpio_config_t out_cfg = {
        .pin_bit_mask =
            (1ULL << PIN_READY_C6_TO_S3),

        .mode = GPIO_MODE_OUTPUT,

        .pull_up_en =
            GPIO_PULLUP_DISABLE,

        .pull_down_en =
            GPIO_PULLDOWN_DISABLE,

        .intr_type =
            GPIO_INTR_DISABLE,
    };

    gpio_config(&out_cfg);

    gpio_set_level(
        PIN_READY_C6_TO_S3,
        0
    );

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

    spi_slave_interface_config_t slave_cfg = {
        .spics_io_num = PIN_SPI_CS,

        .queue_size = 1,

        .mode = 0,

        .post_setup_cb =
            spi_post_setup_cb,

        .post_trans_cb =
            spi_post_trans_cb,
    };

    esp_err_t ret =
        spi_slave_initialize(
            SPI_HOST,
            &bus_cfg,
            &slave_cfg,
            SPI_DMA_CHAN
        );

    if (ret != ESP_OK) {
        ESP_LOGE(
            TAG,
            "SPI slave init failed: %d",
            ret
        );

        return -1;
    }

    /*
     * Queue the first empty transaction.
     *
     * S3 can immediately clock this slot.
     */
    queue_slot();

    ESP_LOGI(
        TAG,
        "SPI slave initialized (%u-byte full-duplex slot)",
        (unsigned)SPI_SLOT_BYTES
    );

    return 0;
}

/* --------------------------------------------------------------------------
 * Has received data?
 * -------------------------------------------------------------------------- */

bool spi_slave_has_data(void)
{
    return s_has_data;
}

/* --------------------------------------------------------------------------
 * Read one completed SPI transaction
 *
 * This function:
 *
 * 1. Reaps the completed transaction.
 * 2. Validates the received C6/S3 payload.
 * 3. Copies received payload to caller.
 * 4. Loads the next C6 -> S3 packet into the DMA TX buffer.
 * 5. Requeues the next transaction.
 * -------------------------------------------------------------------------- */

int spi_slave_read(
    uint8_t *buf,
    size_t buf_size
)
{
    spi_slave_transaction_t *done = NULL;

    /*
     * Do not block here.
     *
     * The C6 main task calls this repeatedly.
     */
    esp_err_t ret =
        spi_slave_get_trans_result(
            SPI_HOST,
            &done,
            0
        );

    if (ret != ESP_OK) {
        return 0;
    }

    int n = 0;

    /* --------------------------------------------------------------
     * Process received S3 -> C6 payload
     * -------------------------------------------------------------- */

    if (s_has_data && buf != NULL && buf_size > 0) {

        uint8_t *rx = s_slot_rx;

        uint16_t len =
            ((uint16_t)rx[0] << 8) |
            rx[1];

        if (len > 0 &&
            len <= SPI_SLOT_BYTES - 4) {

            n =
                (len < buf_size)
                ? len
                : buf_size;

            memcpy(
                buf,
                rx + 2,
                n
            );
        }

        s_has_data = false;
    }

    /*
     * Clear the RX buffer after the completed transaction has been
     * safely reaped.
     */
    memset(
        s_slot_rx,
        0,
        sizeof(s_slot_rx)
    );

    /* --------------------------------------------------------------
     * Load next C6 -> S3 TX packet
     * -------------------------------------------------------------- */

    xSemaphoreTake(
        s_tx_mutex,
        portMAX_DELAY
    );

    if (s_tx_count > 0) {

        uint8_t slot = s_tx_head;

        memcpy(
            s_slot_tx,
            s_tx_queue[slot],
            SPI_SLOT_BYTES
        );

        memset(
            s_tx_queue[slot],
            0,
            SPI_SLOT_BYTES
        );

        s_tx_queue_len[slot] = 0;

        s_tx_head =
            (uint8_t)(
                (s_tx_head + 1) %
                SPI_TX_QUEUE_DEPTH
            );

        s_tx_count--;

        update_c6_ready();

    } else {

        /*
         * Nothing waiting.
         *
         * Send an empty slot during the next S3 transaction.
         */
        memset(
            s_slot_tx,
            0,
            sizeof(s_slot_tx)
        );

        update_c6_ready();
    }

    xSemaphoreGive(
        s_tx_mutex
    );

    /*
     * Re-arm SPI.
     *
     * At this point s_slot_tx is no longer owned by the completed
     * transaction, so changing it is safe.
     */
    queue_slot();

    return n;
}

/* --------------------------------------------------------------------------
 * Queue C6 -> S3 packet
 * -------------------------------------------------------------------------- */

int spi_slave_send(
    const uint8_t *data,
    size_t len
)
{
    if (len > SPI_SLOT_BYTES - 4) {
        ESP_LOGE(
            TAG,
            "Send too large: %d bytes (max %d)",
            (int)len,
            (int)(SPI_SLOT_BYTES - 4)
        );

        return -1;
    }

    if (data == NULL && len > 0) {
        return -1;
    }

    xSemaphoreTake(
        s_tx_mutex,
        portMAX_DELAY
    );

    if (s_tx_count >= SPI_TX_QUEUE_DEPTH) {

        xSemaphoreGive(
            s_tx_mutex
        );

        ESP_LOGW(
            TAG,
            "SPI TX queue full, dropping frame: %d bytes",
            (int)len
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
    uint16_t crc =
        crc16_local(
            data,
            len
        );

    s_tx_queue[slot][2 + len] =
        (uint8_t)((crc >> 8) & 0xFF);

    s_tx_queue[slot][3 + len] =
        (uint8_t)(crc & 0xFF);

    s_tx_queue_len[slot] = len;

    s_tx_tail =
        (uint8_t)(
            (s_tx_tail + 1) %
            SPI_TX_QUEUE_DEPTH
        );

    s_tx_count++;

    /*
     * Tell S3 that C6 has something waiting.
     */
    update_c6_ready();

    xSemaphoreGive(
        s_tx_mutex
    );

    ESP_LOGD(
        TAG,
        "SPI TX queued for S3: %d bytes, queue=%u",
        (int)len,
        (unsigned)s_tx_count
    );

    return 0;
}