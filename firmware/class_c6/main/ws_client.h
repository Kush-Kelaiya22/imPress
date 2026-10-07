/**
 * @file ws_client.h
 * @brief WebSocket client for C6 — real-time command channel from backend.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Connect WebSocket to backend class room.
 * @param class_id  Class session ID from backend
 * @param callback  Message receive callback (void (*cb)(const char *json))
 */
typedef void (*ws_recv_cb_t)(const char *json);
int ws_client_start(int class_id, ws_recv_cb_t callback);

/**
 * @brief Check if WebSocket is connected.
 */
bool ws_client_is_connected(void);

/**
 * @brief Force a WebSocket reconnect (used after class re-assignment).
 */
void ws_client_reconnect(void);

/**
 * @brief Send a JSON message over WebSocket.
 * @param json  JSON string
 * @return 0 on success
 */
int ws_client_send(const char *json);

/**
 * @brief Stop WebSocket client.
 */
void ws_client_stop(void);

#ifdef __cplusplus
}
#endif