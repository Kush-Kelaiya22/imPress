/**
 * @file ws_command.h
 * @brief Backend WebSocket command (JSON) → mesh protocol frame.
 *
 * Pure translation, no I/O, so it is host-testable. The JSON contract is
 * pinned in firmware/contract/device_ws_frames.json (generated/checked by
 * backend/tests/test_device_ws_contract.py).
 */

#pragma once

#include <stddef.h>
#include <stdint.h>
#include "cJSON.h"
#include "protocol.h"

/**
 * @brief Translate quiz_question / quiz_end / poll_start / poll_end.
 * @return frame length (> 0), 0 if the event is not a mesh command,
 *         -1 if it is one but required fields are missing.
 */
int ws_command_to_frame(const cJSON *msg, uint8_t *out, size_t out_size);
