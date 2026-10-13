/**
 * @file device_caps.h
 * @brief What this board is, for the server's compatibility checks (#129).
 *
 * Sent with the registration of the gateway and the hub as
 *   "caps":{"chip_rev":<n>,"flash_mb":<n>,"psram_mb":<n>,"slot_kb":<n>,"rollback":<true|false>}
 * so the TrustedInstaller can refuse an image built for a larger flash (the
 * 32 MB octal hub image on an 8 MB quad hub aborts at boot), an image larger
 * than this board's OTA slot, and the UI never claims automatic rollback on
 * a board whose bootloader can't do it.
 * ESP-IDF only (not part of the host-tested protocol code).
 */
#pragma once

#include <stdio.h>
#include "sdkconfig.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_ota_ops.h"
#if CONFIG_SPIRAM
#include "esp_psram.h"
#endif

/** Append `,"caps":{…}` to buf at offset len; returns the new length (unchanged if it doesn't fit). */
static inline int device_caps_append(char *buf, size_t size, int len)
{
    esp_chip_info_t chip;
    esp_chip_info(&chip);
    uint32_t flash = 0;
    esp_flash_get_size(NULL, &flash);
    size_t psram = 0;
#if CONFIG_SPIRAM
    psram = esp_psram_get_size();
#endif
    const esp_partition_t *slot = esp_ota_get_next_update_partition(NULL);
#if CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE
    const char *rollback = "true";
#else
    const char *rollback = "false";
#endif
    int n = snprintf(buf + len, size - (size_t)len,
                     ",\"caps\":{\"chip_rev\":%u,\"flash_mb\":%lu,\"psram_mb\":%u,\"slot_kb\":%lu,\"rollback\":%s}",
                     (unsigned)chip.revision, (unsigned long)(flash >> 20), (unsigned)(psram >> 20),
                     (unsigned long)(slot ? slot->size >> 10 : 0), rollback);
    return (n > 0 && (size_t)(len + n) < size) ? len + n : len;
}
