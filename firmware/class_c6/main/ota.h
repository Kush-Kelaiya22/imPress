/**
 * @file ota.h
 * @brief OTA client for the C6 gateway (#34).
 *
 * The C6 is always on Wi-Fi, so it updates itself directly:
 *   check (firmware/check: version, SHA-256, size) → download into the
 *   inactive slot while hashing → verify SHA-256 + esp_ota_end → set boot
 *   partition → reboot → health check → mark valid → report success.
 * Every step is reported to POST /api/device/ota/status. With app rollback
 * enabled, an image that never passes the health check is reverted by the
 * bootloader, and the old image reports rolled_back.
 */
#pragma once

#include <stdbool.h>

/** The MAC this gateway registered with (used in every report). Call first. */
void ota_c6_set_mac(const char *mac);

/** Start an update check + install in its own task (no-op if one runs). */
bool ota_c6_start(void);

/** After boot, once Wi-Fi and the backend registration succeeded: finish a
 *  pending-verify image (health check, mark valid, report) or report a
 *  rollback. Also arms the health watchdog. */
void ota_c6_boot_check(bool healthy);

/** true while an update is in progress. */
bool ota_c6_in_progress(void);
