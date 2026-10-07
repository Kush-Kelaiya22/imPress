/**
 * @file spi_master.h
 * @brief SPI master driver for S3 → C6 communication (fixed 4096-byte slot).
 *
 * High-speed SPI bus at up to 40 MHz, full duplex.
 * Slot format (identical both directions):
 *   [LEN:2 BE][PAYLOAD:LEN][CRC16:2 over PAYLOAD only][zero pad to SPI_SLOT_BYTES]
 * LEN=0  =>  "no payload" (all zeros).
 * Ready handshake (active high): S3 drives PIN_READY_S3_TO_C6 when it queues
 * a frame; C6 drives PIN_READY_C6_TO_S3 when IT queues a frame.
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
 * @brief Queue a payload for C6, newest wins (latest-wins single slot).
 *        Fills the S3 TX slot [LEN][PAYLOAD][CRC][pad], asserts R_S3 and
 *        wakes the SPI link task. Non-blocking; caller data is copied.
 * @param data  Payload (a msg_encode() frame). len <= SPI_SLOT_BYTES - 4.
 * @param len   Payload length
 * @return 0 on success, -1 if too large
 */
int spi_master_send(const uint8_t *data, size_t len);

/**
 * @brief Run ONE full-duplex SPI_SLOT_BYTES slot transfer: sends the queued
 *        S3 slot (all-zero if none) and receives the C6 slot. Clears the S3
 *        slot and de-asserts R_S3 once sent.
 * @return true if C6 slot carried a valid payload (LEN>0, CRC ok); payload
 *         available via spi_master_rx_copy()
 */
bool spi_master_poll(void);

/**
 * @brief Sample whether C6 has a frame queued (reads PIN_READY_C6_TO_S3).
 * @return true if C6 ready line is high
 */
bool spi_master_c6_has_data(void);

/**
 * @brief True while S3 has queued (unsent) TX in its slot.
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
 * @brief Binary semaphore the SPI link task waits on; given when S3 queues
 *        TX (spi_master_send) or when C6 raises its ready line (ISR).
 */
SemaphoreHandle_t spi_master_link_signal(void);

#ifdef __cplusplus
}
#endif