/**
 * @file mesh_master.h
 * @brief ESP-NOW mesh master (root node) for S3 class module.
 *
 * This is the root of the mesh tree. All student messages converge here.
 * The S3 receives student data and forwards it via SPI to the C6.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "protocol.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Student routing info */
typedef struct {
    char     enrollment[11];   /* 10-char enrollment number + NUL (primary identity) */
    uint32_t device_id;        /* optional, 0 = unknown — ESP-NOW routing only */
    uint8_t  mac[6];           /* ESP-NOW peer address — routing only */
    uint8_t  hops;             /* hops to reach this student */
    int8_t   rssi;
    uint32_t last_seen_ms;     /* timestamp of last message */
    bool     is_active;
} student_entry_t;

/**
 * @brief Initialize ESP-NOW mesh master on S3.
 * @return ESP_OK on success
 */
int mesh_master_init(void);

/**
 * @brief Send a broadcast message to ALL students in the mesh.
 * @param type       Message type
 * @param payload    Payload data
 * @param length     Payload length
 * @return ESP_OK on success
 */
int mesh_master_broadcast(msg_type_t type, const uint8_t *payload, uint16_t length);

/**
 * @brief Send a unicast message to a specific student by device ID.
 * @param device_id  Target student's device ID
 * @param type       Message type
 * @param payload    Payload data
 * @param length     Payload length
 * @return 0 on success, -1 if student not found
 */
int mesh_master_unicast(uint32_t device_id, msg_type_t type,
                        const uint8_t *payload, uint16_t length);

/**
 * @brief Send a unicast message to a specific student by enrollment number.
 * @param enrollment 10-char enrollment number
 * @param type       Message type
 * @param payload    Payload data
 * @param length     Payload length
 * @return 0 on success, -1 if student not found
 */
int mesh_master_unicast_by_enrollment(const char *enrollment, msg_type_t type,
                                      const uint8_t *payload, uint16_t length);

/**
 * @brief Get the number of active students in the mesh.
 */
int mesh_master_get_student_count(void);

/**
 * @brief Get student entry by index.
 */
const student_entry_t *mesh_master_get_student(int index);

/**
 * @brief Get all active students (for device tree).
 * @param out_students Array to fill with student entries
 * @param max_students Maximum number of entries in out_students
 * @return Number of students copied
 */
int mesh_master_get_all_students(student_entry_t *out_students, int max_students);

/**
 * @brief Mark students inactive if no message received for timeout_ms.
 *        Call periodically from the heartbeat task.
 */
void mesh_master_sweep_timeouts(uint32_t timeout_ms);

/**
 * @brief Set callback for messages received from students.
 */
typedef void (*mesh_master_recv_cb_t)(const msg_t *msg, uint32_t sender_id);
void mesh_master_on_receive(mesh_master_recv_cb_t callback);

/**
 * @brief Batch student messages for SPI transfer to C6.
 * @param buf       Output buffer for batched messages
 * @param buf_size  Size of output buffer
 * @return Number of bytes written
 */
int mesh_master_flush_to_spi(uint8_t *buf, size_t buf_size);

#ifdef __cplusplus
}
#endif
