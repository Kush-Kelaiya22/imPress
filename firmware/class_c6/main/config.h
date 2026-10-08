/**
 * @file config.h
 * @brief C6 class gateway configuration — Kconfig defaults + NVS runtime overlay.
 *
 * Compile-time defaults come from Kconfig.projbuild menuconfig.
 * At boot, init_nvs_config() loads persistent overrides from NVS so
 * credentials and class_id can be changed at runtime without reflashing.
 */

#pragma once

#include "driver/gpio.h"
#include "driver/spi_slave.h"

/* ── Device Identity ── */
#define DEVICE_TYPE         "c6"
#define FIRMWARE_VERSION    "1.0.0"
#define DEVICE_MAC_STR_LEN  18
#define NVS_NAMESPACE       "impress"
#define NVS_KEY_INIT        "init_done"   /* u8: 1 = NVS already written */
#define NVS_KEY_WIFI_SSID   "wifi_ssid"   /* str  33 */
#define NVS_KEY_WIFI_PASS   "wifi_pass"   /* str  65 */
#define NVS_KEY_BACKEND_H   "backend_h"   /* str 128 */
#define NVS_KEY_BACKEND_P   "backend_p"   /* u16 */
#define NVS_KEY_API_KEY     "api_key"     /* str 128 */
#define NVS_KEY_CLASS_ID    "class_id"    /* i32 */
#define NVS_KEY_SSID_LEN    33
#define NVS_KEY_PASS_LEN    65
#define NVS_KEY_HOST_LEN    128
#define NVS_KEY_KEY_LEN     128

/* ── Compile-time defaults (from Kconfig) ── */
#define CFG_WIFI_SSID       CONFIG_WIFI_SSID
#define CFG_WIFI_PASS       CONFIG_WIFI_PASSWORD
#define CFG_WIFI_RETRY      CONFIG_WIFI_MAX_RETRY
#define CFG_BACKEND_HOST    CONFIG_BACKEND_HOST
#define CFG_BACKEND_PORT    CONFIG_BACKEND_PORT
#define CFG_API_KEY         CONFIG_DEVICE_API_KEY
#define CFG_CLASS_ID        CONFIG_CLASS_SESSION_ID
#define CFG_HB_INTERVAL_S   CONFIG_HEARTBEAT_INTERVAL_S
#define CFG_WS_PING_S       CONFIG_WS_PING_INTERVAL_S
#define CFG_PING_INTERVAL_S CONFIG_STATUS_PING_INTERVAL_S
#define CFG_SPI_BATCH_MAX   CONFIG_SPI_BATCH_MAX_WAIT_MS
#define CFG_BATCH_MAX       CONFIG_BATCH_MAX_SIZE

/* ── WiFi Event Bits ── */
#define WIFI_CONNECTED_BIT  BIT0
#define WIFI_FAIL_BIT       BIT1

/* ── SPI Slave Configuration (C6 = slave, standard full-duplex SPI; S3 sets the clock) ── */
#define SPI_HOST            SPI2_HOST
#define PIN_SPI_MOSI        GPIO_NUM_7
#define PIN_SPI_MISO        GPIO_NUM_6
#define PIN_SPI_SCLK        GPIO_NUM_2
#define PIN_SPI_CS          GPIO_NUM_10
#define SPI_DMA_CHAN         SPI_DMA_CH_AUTO
#define SPI_RX_BUF_SIZE     (1024 * 4)

/* ── SPI slot ready lines (slot format: SPI_SLOT_BYTES in protocol.h) ── */
/* Mirror of the S3 master's ready lines. ACTIVE HIGH, idle LOW. */
#define PIN_READY_S3_TO_C6  GPIO_NUM_12  /* INPUT:  S3 asserts→frame queued for us */
#define PIN_READY_C6_TO_S3  GPIO_NUM_13  /* OUTPUT: we assert→frame queued for S3 */

/* ── HTTP payload sizes ── */
#define HTTP_BUF_SIZE       4096

/* ── Runtime config struct (filled by init_nvs_config) ── */
typedef struct {
    char     wifi_ssid[NVS_KEY_SSID_LEN];
    char     wifi_pass[NVS_KEY_PASS_LEN];
    char     backend_host[NVS_KEY_HOST_LEN];
    uint16_t backend_port;
    char     api_key[NVS_KEY_KEY_LEN];
    int32_t  class_id;
    /* Timing (seconds, from Kconfig — no NVS override needed) */
    uint32_t hb_interval_s;
    uint32_t ws_ping_s;
    uint32_t ping_interval_s;
    uint32_t spi_batch_max_ms;
    uint32_t batch_max;
} c6_config_t;

/**
 * @brief Runtime configuration (global, set once at boot).
 *        Populate with init_nvs_config() before using any subsystem.
 */
extern c6_config_t g_cfg;

/**
 * @brief Load persisted config from NVS, falling back to Kconfig defaults.
 *        First boot writes Kconfig values into NVS; subsequent boots read them.
 */
void init_nvs_config(void);

/**
 * @brief Persist a backend-assigned class ID and update g_cfg.
 */
void nvs_save_class_id(int32_t class_id);

/* ── Derived macros (built after g_cfg is populated) ── */

/* Backend base URL: http://<host>:<port>  (use snprintf with g_cfg) */
/* WebSocket base:  ws://<host>:<port>/ws/class/<id>  */
