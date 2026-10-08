/**
 * @file config.h
 * @brief S3 class module configuration — Kconfig defaults + NVS runtime overlay.
 *
 * Compile-time defaults come from Kconfig.projbuild menuconfig.
 * At boot, init_nvs_config() loads persistent overrides from NVS so
 * credentials and class_id survive OTA reboots.
 *
 * WiFi is used ONLY during OTA updates; normally the S3 is off-WiFi and
 * runs ESP-NOW mesh + SPI master.
 */

#pragma once

#include "esp_app_desc.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_bit_defs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"

/* ── Device Identity ── */
#define DEVICE_TYPE         "s3"
/* The version is the image's own (esp_app_desc_t), set from version.txt in
 * the project root by the build. It is what the backend and OTA compare, so it
 * can't drift from the binary the way a hand-edited #define did. */
#define FIRMWARE_VERSION    (esp_app_get_description()->version)

/* ── NVS Namespace & Keys ── */
#define NVS_NAMESPACE       "s3_cfg"
#define NVS_KEY_SSID_LEN    33
#define NVS_KEY_PASS_LEN    65
#define NVS_KEY_HOST_LEN    64
#define NVS_KEY_KEY_LEN     65
#define NVS_KEY_INIT        "init"

/* ── SPI Bus Configuration (S3 = master, standard full-duplex SPI) ── */
#define SPI_HOST            SPI2_HOST
#define PIN_SPI_MOSI        GPIO_NUM_11
#define PIN_SPI_MISO        GPIO_NUM_13
#define PIN_SPI_SCLK        GPIO_NUM_12
#define PIN_SPI_CS          GPIO_NUM_10
#define SPI_CLOCK_HZ        (CONFIG_SPI_CLOCK_MHZ * 1000 * 1000)  /* Kconfig, default 10 MHz */
#define SPI_DMA_CHAN         SPI_DMA_CH_AUTO

/* ── SPI slot ready lines (slot format: SPI_SLOT_BYTES in protocol.h) ── */
/* Ready lines, ACTIVE HIGH, idle LOW */
#define PIN_READY_S3_TO_C6  GPIO_NUM_16  /* S3 drives (output): "S3 frame queued push" */
#define PIN_READY_C6_TO_S3  GPIO_NUM_15  /* S3 reads (input, pull-down): "C6 frame queued" */

/* ── Mesh Defaults (overridable via Kconfig) ── */
#ifndef MESH_MAX_STUDENTS
#define MESH_MAX_STUDENTS   300
#endif
#ifndef MESH_RELAY_TTL
#define MESH_RELAY_TTL      5
#endif

/* ── WiFi Event Bits (for OTA connection) ── */
#define WIFI_CONNECTED_BIT  BIT0
#define WIFI_FAIL_BIT       BIT1

/* ── Runtime Config Structure ── */
typedef struct {
    char     wifi_ssid[NVS_KEY_SSID_LEN];
    char     wifi_pass[NVS_KEY_PASS_LEN];
    char     backend_host[NVS_KEY_HOST_LEN];
    uint16_t backend_port;
    char     api_key[NVS_KEY_KEY_LEN];   /* sent on every request: dev_key if issued, else prov_key */
    char     prov_key[NVS_KEY_KEY_LEN];  /* the site's shared key, used to register (#66) */
    int32_t  class_id;
    /* Mesh (from Kconfig, no NVS override needed) */
    uint32_t hb_interval_ms;
    uint32_t student_timeout_ms;
    uint32_t spi_poll_interval_ms;
    uint8_t  mesh_channel;
} s3_config_t;

/* ── Global Runtime Config ── */
extern s3_config_t g_cfg;

/* Per-device key (#66): issued by /register, then sent instead of the shared
 * key. Cleared when the backend answers 401 (an admin reset it). */
void cfg_set_device_key(const char *key);
void cfg_clear_device_key(void);
bool cfg_has_device_key(void);

/**
 * @brief Load persisted config from NVS, falling back to Kconfig defaults.
 *        First boot writes Kconfig values into NVS; subsequent boots read them.
 *        Requires esp_netif_init() and esp_event_loop_create_default() to be
 *        called first (for WiFi STA init during OTA later).
 */
void init_nvs_config(void);

/**
 * @brief Persist a backend-assigned class ID and update g_cfg.
 */
void nvs_save_class_id(int32_t class_id);
