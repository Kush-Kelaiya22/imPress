/* Minimal ESP-IDF type/API declarations so main/spi_slave.c builds on a host.
 * Implementations live in the test (fake driver). Only what spi_slave.c uses. */
#pragma once

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

typedef int esp_err_t;
#define ESP_OK 0
#define ESP_ERR_TIMEOUT 0x107
#define IRAM_ATTR
#define BIT(n) (1ULL << (n))

#define ESP_LOGE(tag, fmt, ...) printf("E %s: " fmt "\n", tag, ##__VA_ARGS__)
#define ESP_LOGI(tag, fmt, ...) printf("I %s: " fmt "\n", tag, ##__VA_ARGS__)
#define ESP_LOGW(tag, fmt, ...) printf("W %s: " fmt "\n", tag, ##__VA_ARGS__)
#define ESP_LOGD(tag, fmt, ...) ((void)0)

#define ESP_FAIL                      -1
#define ESP_ERR_INVALID_ARG       0x102
#define ESP_ERR_NVS_NOT_FOUND    0x1102
#define ESP_ERR_NVS_NO_FREE_PAGES 0x110d
#define ESP_ERR_NVS_NEW_VERSION_FOUND 0x1110
#define ESP_ERROR_CHECK(x) do { esp_err_t e_ = (x); if (e_ != ESP_OK) { printf("ESP_ERROR_CHECK failed: %d\n", e_); abort(); } } while (0)

/* NVS (implemented by firmware/test_support/nvs_fake.c) */
typedef uint32_t nvs_handle_t;
typedef enum { NVS_READONLY, NVS_READWRITE } nvs_open_mode_t;
esp_err_t nvs_flash_init(void);
esp_err_t nvs_flash_erase(void);
esp_err_t nvs_open(const char *ns, nvs_open_mode_t mode, nvs_handle_t *out);
void      nvs_close(nvs_handle_t h);
esp_err_t nvs_commit(nvs_handle_t h);
esp_err_t nvs_get_str(nvs_handle_t h, const char *key, char *out, size_t *len);
esp_err_t nvs_set_str(nvs_handle_t h, const char *key, const char *value);
esp_err_t nvs_get_u8(nvs_handle_t h, const char *key, uint8_t *out);
esp_err_t nvs_set_u8(nvs_handle_t h, const char *key, uint8_t value);
esp_err_t nvs_get_u16(nvs_handle_t h, const char *key, uint16_t *out);
esp_err_t nvs_set_u16(nvs_handle_t h, const char *key, uint16_t value);
esp_err_t nvs_get_i32(nvs_handle_t h, const char *key, int32_t *out);
esp_err_t nvs_set_i32(nvs_handle_t h, const char *key, int32_t value);
esp_err_t nvs_erase_key(nvs_handle_t h, const char *key);

/* FreeRTOS */
typedef uint32_t TickType_t;
typedef int BaseType_t;
typedef void *SemaphoreHandle_t;
#define portMAX_DELAY 0xFFFFFFFFu
SemaphoreHandle_t xSemaphoreCreateBinary(void);
SemaphoreHandle_t xSemaphoreCreateMutex(void);
BaseType_t xSemaphoreTake(SemaphoreHandle_t s, TickType_t t);
BaseType_t xSemaphoreGive(SemaphoreHandle_t s);
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t s, BaseType_t *woken);

/* GPIO */
typedef int gpio_num_t;
#define GPIO_NUM_2 2
#define GPIO_NUM_3 3
#define GPIO_NUM_4 4
#define GPIO_NUM_6 6
#define GPIO_NUM_7 7
#define GPIO_NUM_10 10
#define GPIO_NUM_12 12
#define GPIO_NUM_13 13
enum { GPIO_MODE_INPUT, GPIO_MODE_OUTPUT };
enum { GPIO_PULLUP_DISABLE, GPIO_PULLDOWN_DISABLE = 0, GPIO_INTR_DISABLE = 0 };
typedef struct {
    uint64_t pin_bit_mask;
    int mode, pull_up_en, pull_down_en, intr_type;
} gpio_config_t;
esp_err_t gpio_config(const gpio_config_t *cfg);
esp_err_t gpio_set_level(gpio_num_t pin, uint32_t level);

/* SPI slave */
typedef int spi_host_device_t;
#define SPI2_HOST 1
#define SPI_DMA_CH_AUTO 3
#define SPICOMMON_BUSFLAG_QUAD (1u << 7)
typedef struct {
    size_t length;
    size_t trans_len;
    const void *tx_buffer;
    void *rx_buffer;
    void *user;
} spi_slave_transaction_t;
typedef void (*slave_transaction_cb_t)(spi_slave_transaction_t *trans);
typedef struct {
    int mosi_io_num, miso_io_num, sclk_io_num, quadwp_io_num, quadhd_io_num;
    int max_transfer_sz;
    uint32_t flags;
} spi_bus_config_t;
typedef struct {
    int spics_io_num;
    uint32_t flags;
    int queue_size;
    uint8_t mode;
    slave_transaction_cb_t post_setup_cb;
    slave_transaction_cb_t post_trans_cb;
} spi_slave_interface_config_t;
esp_err_t spi_slave_initialize(spi_host_device_t host, const spi_bus_config_t *bus,
                               const spi_slave_interface_config_t *cfg, int dma);
esp_err_t spi_slave_queue_trans(spi_host_device_t host,
                                const spi_slave_transaction_t *trans, TickType_t wait);
esp_err_t spi_slave_get_trans_result(spi_host_device_t host,
                                     spi_slave_transaction_t **trans, TickType_t wait);
