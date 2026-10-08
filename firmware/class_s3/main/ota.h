/**
 * @file ota.h
 * @brief OTA module for the S3 class hub.
 *
 * The S3 normally runs ESP-NOW mesh + SPI master and is OFF WiFi.
 * When the server pushes an S3 update, the C6 relays a MSG_OTA_PROMPT
 * over SPI.  The S3 then temporarily:
 *   1. connects to the classroom WiFi as a STA,
 *   2. registers/heartbeats with the backend,
 *   3. polls /api/device/firmware/check,
 *   4. downloads the pending .bin and applies it via esp_ota,
 *   5. reboots back into its mesh + SPI master role.
 * Settings persist in NVS across the update.
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Start the OTA update flow.
 *
 * Returns immediately to caller (handshake runs in its own task).  The
 * mesh + SPI master keep running during handshake, then WiFi attach
 * happens once handshake confirms an update is pending.
 *
 * @param version  Target version string (may be "" = "whatever server has").
 * @param token    One-time download token (may be "").
 * @return true if OTA flow was kicked off, false if already running.
 */
bool ota_start(const char *version, const char *token);

/** @brief true while an OTA flow is in progress (mesh/SPI still running). */
bool ota_in_progress(void);

/** @brief Called by SPI RX when the C6 ACKs our firmware/applied report. */
void ota_mark_ackd(void);

/**
 * @brief After boot: if an OTA was started before the last reboot, report
 *        whether the target version is now running (APPLIED) or the
 *        bootloader rolled back (ROLLED_BACK). Call once the image has been
 *        marked valid and the SPI link is up.
 */
void ota_report_boot_result(void);

#ifdef __cplusplus
}
#endif