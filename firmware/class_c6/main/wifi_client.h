/**
 * @file wifi_client.h
 * @brief WiFi + HTTP client for C6 gateway (production).
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize and connect WiFi using g_cfg credentials.
 * @return 0 on success (init issued), -1 on failure
 */
int wifi_client_init(void);

/**
 * @brief Wait up to timeout_ms for a WiFi connection.
 * @return true if connected
 */
bool wifi_client_wait_connected(uint32_t timeout_ms);

/**
 * @brief Check current WiFi connectivity state.
 */
bool wifi_client_is_connected(void);

/**
 * @brief Get the current STA IP address ("" if none).
 */
const char *wifi_client_get_ip(void);

/**
 * @brief Low-level POST of arbitrary JSON to an absolute URL.
 * @return HTTP status code (200 = OK, 0 = network failure)
 */
int http_post_json(const char *url, const char *json);

/**
 * @brief Register this gateway with the backend.
 * @return HTTP status code (200 = OK, 0 = failure)
 */
int http_register_device(const char *mac_address, const char *device_type);

/**
 * @brief Send a heartbeat with real telemetry (RSSI/heap/flash/battery).
 * @param mac           This gateway's MAC address
 * @param student_count Number of mesh students currently linked
 * @return HTTP status code
 */
int http_send_heartbeat(const char *mac, int student_count, bool s3_link_ok, uint32_t s3_uptime_s);

/**
 * @brief Send the 2-minute classroom status ping (student count, class_id,
 *        uptime, RSSI). Keeps live presence + student_count fresh without
 *        spamming the liveness heartbeat path.
 * @param mac           This gateway's MAC address
 * @param class_id      Linked class session id (0 = unlinked)
 * @param student_count Current mesh student population
 * @return HTTP status code
 */
int http_send_status_ping(const char *mac, int32_t class_id, int student_count);

/**
 * @brief Check a student in by ENROLLMENT NUMBER (identity, no MAC tracking).
 * @param enrollment  10-char alphanumeric enrollment number
 * @param class_code  Active class session join code
 * @return HTTP status code
 */
int http_send_attendance(const char *enrollment, const char *class_code);

/**
 * @brief Send batched student messages to the backend.
 * @param json  JSON array of student message dicts
 * @return HTTP status code
 */
int http_send_batch(const char *json);

/**
 * @brief POST JSON to a backend API path (e.g. "/api/device/firmware/check").
 * @param out       response body (NUL-terminated, truncated to out_size), may be NULL
 * @return HTTP status, 0 on a transport error
 */
int http_post_api(const char *path, const char *json, char *out, size_t out_size);

/** @brief Full backend URL for an API path. */
void http_api_url(char *buf, size_t sz, const char *path);

#ifdef __cplusplus
}
#endif