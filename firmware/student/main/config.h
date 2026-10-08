/**
 * @file config.h
 * @brief Student module configuration.
 *
 * Student identity = ENROLLMENT NUMBER (10 chars), stored in NVS so it
 * survives OTA. The full student profile (name/program/…) is also cached
 * in NVS but is NEVER transmitted over the mesh air — only the enrollment
 * number is sent (primary identity).
 */

#pragma once

#include "esp_app_desc.h"
#include <stdbool.h>
#include "driver/gpio.h"

/* ── Device Identity ── */
#define DEVICE_TYPE         "student"
/* The version is the image's own (esp_app_desc_t), set from version.txt in
 * the project root by the build. It is what the backend and OTA compare, so it
 * can't drift from the binary the way a hand-edited #define did. */
#define FIRMWARE_VERSION    (esp_app_get_description()->version)
#define NVS_NAMESPACE       "impress"
#define NVS_KEY_INIT        "init_done"      /* u8: 1 = provisioned */
#define NVS_KEY_ENROLL      "enroll"         /* str 11 (10 + NUL) */
#define NVS_KEY_NAME        "s_name"         /* str 65 profile cache */
#define NVS_KEY_PROGRAM     "s_program"      /* str 65 profile cache */
#define NVS_KEY_EMAIL       "s_email"        /* str 65 profile cache */
#define NVS_ENROLL_LEN      11
#define NVS_NAME_LEN        65
#define NVS_PROGRAM_LEN     65
#define NVS_EMAIL_LEN       65
/* Placeholder enrollment written on first boot — REPLACE at provisioning.
 * Exactly 10 alphanumeric chars (matches backend ENROLL_RE). */
#define DEFAULT_ENROLLMENT  "0000000000"

/* ── Mesh Configuration ── */
#define MESH_WIFI_CHANNEL   1       /* must match S3 */
#define MESH_GROUP_ID       0x1234  /* shared mesh group identifier */
#define MESH_MAX_PEERS      6       /* ESP-NOW peer limit per device */
#define MESH_RELAY_TTL      5       /* max hops before message dies */
#define MESH_RELAY_COOLDOWN_MS  100 /* min time between relays */

/* ── Pin Definitions (adjust for your board) ── */
/* Buttons-only student board: NO OLED, NO LED, only the 5 buttons (pulled up). */
#define STUDENT_HAS_DISPLAY 0   /* 1 = SSD1306 fitted on PIN_I2C_SDA/SCL */
#define STUDENT_HAS_LED     0   /* 1 = status LED on PIN_LED_STATUS */
#define PIN_BTN_1           GPIO_NUM_4   /* option A */
#define PIN_BTN_2           GPIO_NUM_16  /* option B (UART2 RX) */
#define PIN_BTN_3           GPIO_NUM_18  /* option C */
#define PIN_BTN_4           GPIO_NUM_22  /* option D */
#define PIN_BTN_CONFIRM     GPIO_NUM_23  /* confirm selection */
#define PIN_LED_STATUS      GPIO_NUM_2   /* onboard LED */

/* ── OLED Display (I2C) ── */
#define PIN_I2C_SDA         GPIO_NUM_8
#define PIN_I2C_SCL         GPIO_NUM_9
#define I2C_FREQ_HZ         400000

/* ── Timing ── */
#define HEARTBEAT_INTERVAL_MS   30000   /* send heartbeat every 30s */
#define DEBOUNCE_MS             50      /* button debounce */
#define ANSWER_TIMEOUT_MS       30000   /* default answer timeout */

/* ── Runtime student identity (filled by init_student_profile) ── */
typedef struct {
    char enrollment[NVS_ENROLL_LEN];   /* primary identity — transmitted */
    char name[NVS_NAME_LEN];           /* local profile cache — NOT transmitted */
    char program[NVS_PROGRAM_LEN];     /* local profile cache */
    char email[NVS_EMAIL_LEN];         /* local profile cache */
    bool provisioned;                  /* whether server data has been pushed */
} student_profile_t;

/** Runtime identity/profile (global). Populate before use. */
extern student_profile_t g_student;

/**
 * @brief Load the student profile from NVS (enrollment + local cache).
 *        First boot writes DEFAULT_ENROLLMENT placeholder.
 */
void init_student_profile(void);

/**
 * @brief Update the locally cached student profile (server push).
 *        Enrollment may be updated here but NEVER transmitted as identity
 *        beyond the enrollment number itself.
 */
void student_update_profile(const char *enroll, const char *name,
                            const char *program, const char *email);

/**
 * @brief True when a REAL (non-placeholder) 10-char alphanumeric enrollment
 *        is stored. The device refuses to join the mesh while this is false.
 */
bool student_has_identity(void);

/**
 * @brief Persist a new enrollment number.
 *
 *        Enforces the exact on-wire format (10 alphanumeric chars, and must
 *        not be the DEFAULT_ENROLLMENT placeholder) and refuses to overwrite
 *        an already-provisioned identity (set-once semantics — re-provision
 *        explicitly via student_clear_enrollment()).
 *
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if the string does not match
 *         the 10-char alphanumeric format, ESP_ERR_INVALID_STATE if a different
 *         valid identity is already stored, ESP_FAIL on NVS failure.
 */
int student_set_enrollment(const char *enroll);

/**
 * @brief Delete the stored enrollment (factory reset of identity). The device
 *        falls back to the "NO ID" provisioning state on next boot.
 */
void student_clear_enrollment(void);