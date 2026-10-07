/**
 * @file spi_slave.h
 * @brief SPI slave driver for C6 ← S3 communication.
 */

#pragma once

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize SPI slave peripheral.
 * @return 0 on success
 */
int spi_slave_init(void);

/**
 * @brief Check if new data is available from S3.
 */
bool spi_slave_has_data(void);

/**
 * @brief Read data received from S3.
 * @param buf        Output buffer
 * @param buf_size   Buffer size
 * @return Number of bytes received, 0 if nothing
 */
int spi_slave_read(uint8_t *buf, size_t buf_size);

/**
 * @brief Send data to S3 (next time S3 polls).
 * @param data   Data to send
 * @param len    Data length
 * @return 0 on success
 */
int spi_slave_send(const uint8_t *data, size_t len);

#ifdef __cplusplus
}
#endif
