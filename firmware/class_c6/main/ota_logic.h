/**
 * @file ota_logic.h
 * @brief Pure decisions for the C6 OTA client (host-tested, no ESP-IDF).
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "cJSON.h"

/** What POST /api/device/firmware/check offered. */
typedef struct {
    bool     available;
    char     version[32];
    char     sha256[65];      /* hex, lower case */
    uint32_t size;
    int      deployment_id;
} ota_offer_t;

/** @return 0 if parsed (available may be false), -1 if the JSON is unusable
 *  or an offered update lacks a well-formed version / sha256 / size. */
int ota_parse_check(const char *json, ota_offer_t *out);

/** True if digest (32 bytes) equals the 64-hex string (case-insensitive). */
bool ota_digest_matches(const uint8_t digest[32], const char *hex);

typedef enum { OTA_PROMPT_SELF, OTA_PROMPT_S3, OTA_PROMPT_OTHER } ota_prompt_target_t;

/** Who a backend `ota_update` command payload is for: this C6 (device_type
 *  "c6" and our MAC), the S3 behind it (device_type "s3", or no type: pre-v2.1
 *  backends only ever sent S3 prompts), or another device. */
ota_prompt_target_t ota_prompt_target(const cJSON *payload, const char *my_mac);
