/**
 * @file mesh_espnow.h
 * @brief ESP-NOW mesh layer for student module.
 *
 * Handles:
 *  - Receiving broadcast/unicast messages from S3
 *  - Relaying messages from other students toward S3
 *  - Sending data (answers, votes, heartbeats) to S3
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "protocol.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize ESP-NOW mesh on the student module.
 * @param device_id  This device's unique ID
 * @return ESP_OK on success
 */
int mesh_init(uint32_t device_id);

/**
 * @brief Send a message into the mesh (toward S3 root).
 * @param type       Message type
 * @param payload    Payload data
 * @param length     Payload length
 * @return ESP_OK on success
 */
int mesh_send(msg_type_t type, const uint8_t *payload, uint16_t length);

/** As mesh_send(); *msg_id (if not NULL) receives the frame's mesh message
 *  id, which the hub's MSG_ACK names (#181). Set even if sending failed. */
int mesh_send_id(msg_type_t type, const uint8_t *payload, uint16_t length, uint32_t *msg_id);

/**
 * @brief Set callback for incoming messages (from S3, e.g., quiz questions).
 * @param callback   void (*cb)(const msg_t *msg)
 */
typedef void (*mesh_recv_cb_t)(const msg_t *msg);
void mesh_on_receive(mesh_recv_cb_t callback);

/**
 * @brief Check if device is connected to mesh.
 */
bool mesh_is_connected(void);

/**
 * @brief Get number of hops to root (S3).
 */
int mesh_get_hop_count(void);

#ifdef __cplusplus
}
#endif
