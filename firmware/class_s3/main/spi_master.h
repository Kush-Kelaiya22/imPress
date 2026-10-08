/**
 * @file spi_master.h
 * @brief SPI master driver for S3 <-> C6 communication (fixed 4096-byte slots).
 *
 * Standard full-duplex SPI at CONFIG_SPI_CLOCK_MHZ. Slot format and the
 * outgoing FIFO are shared with the C6 (see protocol.h, "SPI slot").
 */

#pragma once

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize SPI master peripheral + ready-line GPIOs.
 * @return 0 on success
 */
int spi_master_init(void);

/**
 * @brief Queue a payload for the C6 (FIFO, SPI_SLOT_FIFO_DEPTH deep), assert
 *        R_S3 and wake the link task. Non-blocking; caller data is copied.
 * @param data  Payload. len <= SPI_SLOT_PAYLOAD_MAX.
 * @return 0, SPI_SLOT_ERR_LEN if too large, or -4 if the FIFO is full
 */
int spi_master_send(const uint8_t *data, size_t len);

/**
 * @brief Run ONE full-duplex slot transfer: sends the oldest queued payload
 *        (an all-zero slot if none) and receives the C6 slot. The payload
 *        leaves the FIFO only if the transfer succeeded.
 * @return true if the C6 slot carried a valid payload (LEN>0, CRC ok);
 *         available via spi_master_rx_copy()
 */
bool spi_master_poll(void);

/**
 * @brief Sample whether C6 has a frame queued (reads PIN_READY_C6_TO_S3).
 * @return true if C6 ready line is high
 */
bool spi_master_c6_has_data(void);

/**
 * @brief True while the S3 FIFO holds unsent payloads.
 */
bool spi_master_tx_pending(void);

/**
 * @brief Copy the last valid C6 payload received by spi_master_poll().
 * @param buf       Output buffer
 * @param buf_size  Buffer size
 * @return Number of bytes copied, 0 if none
 */
int spi_master_rx_copy(uint8_t *buf, size_t buf_size);

/**
 * @brief Binary semaphore the SPI link task waits on (with the poll interval
 *        as timeout); given by spi_master_send().
 */
SemaphoreHandle_t spi_master_link_signal(void);

#ifdef __cplusplus
}
#endif