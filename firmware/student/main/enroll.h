/**
 * @file enroll.h
 * @brief On-device enrollment provisioning for the student module.
 *
 * The student identity is a 10-char alphanumeric enrollment number, stored in
 * NVS. This module provides two on-device ways to set it (buttons on the OLED
 * board, or serial line on the USB console) so devices are provisioned
 * without touching the build configuration. A batch of devices can also be
 * pre-provisioned by writing the "enroll" NVS key directly.
 */

#pragma once

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Run on-device provisioning. Blocks until a valid 10-char
 *        alphanumeric enrollment has been stored (buttons or serial).
 * @return ESP_OK when an identity is stored.
 */
int enroll_run(void);

/**
 * @brief Detect the identity-reset combo (hold CONFIRM + C for 2 s at boot).
 * @return true if the reset combo was held; caller should call
 *         student_clear_enrollment().
 */
bool enroll_reset_requested(void);

#ifdef __cplusplus
}
#endif