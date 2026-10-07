/**
 * @file protocol.c
 * @brief Message protocol implementation for imPress.
 */

#include "protocol.h"
#include <string.h>

/* ── CRC-16/CCITT ─────────────────────────────────────────────────── */

uint16_t crc16_ccitt(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;  /* initial value */
    for (size_t i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000)
                crc = (crc << 1) ^ 0x1021;
            else
                crc <<= 1;
        }
    }
    return crc;
}

/* ── Encode ────────────────────────────────────────────────────────── */

int msg_encode(msg_type_t type, const uint8_t *payload, uint16_t length,
               uint8_t *out_buf, size_t out_size)
{
    if (!out_buf || length > MSG_MAX_PAYLOAD) {
        return -1;
    }
    size_t total = MSG_OVERHEAD + length;
    if (total > out_size) {
        return -1;
    }

    size_t pos = 0;

    /* Start byte */
    out_buf[pos++] = MSG_START_BYTE;

    /* Type */
    out_buf[pos++] = (uint8_t)type;

    /* Length (big-endian) */
    out_buf[pos++] = (length >> 8) & 0xFF;
    out_buf[pos++] = length & 0xFF;

    /* Payload */
    if (payload && length > 0) {
        memcpy(&out_buf[pos], payload, length);
        pos += length;
    }

    /* CRC over type + length + payload */
    uint16_t crc = crc16_ccitt(&out_buf[1], 3 + length);
    out_buf[pos++] = (crc >> 8) & 0xFF;
    out_buf[pos++] = crc & 0xFF;

    return (int)pos;
}

/* ── Decode ────────────────────────────────────────────────────────── */

int msg_decode(const uint8_t *data, size_t data_len, msg_t *out_msg)
{
    if (!data || !out_msg || data_len < MSG_OVERHEAD) {
        return 0;  /* not enough data */
    }

    /* Check start byte */
    if (data[0] != MSG_START_BYTE) {
        return -1;  /* invalid frame */
    }

    /* Parse header */
    out_msg->type   = (msg_type_t)data[1];
    out_msg->length = ((uint16_t)data[2] << 8) | data[3];

    /* Sanity check */
    if (out_msg->length > MSG_MAX_PAYLOAD) {
        return -1;  /* payload too large */
    }

    size_t total = MSG_OVERHEAD + out_msg->length;
    if (data_len < total) {
        return 0;  /* incomplete message, need more data */
    }

    /* Copy payload */
    if (out_msg->length > 0) {
        memcpy(out_msg->payload, &data[4], out_msg->length);
    }

    /* CRC */
    out_msg->crc = ((uint16_t)data[4 + out_msg->length] << 8) |
                   data[5 + out_msg->length];

    return (int)total;
}

/* ── CRC Verification ──────────────────────────────────────────────── */

bool msg_verify_crc(const msg_t *msg)
{
    if (!msg) return false;

    /* Reconstruct what was CRC'd: type(1) + length(2) + payload(N) */
    uint8_t buf[3 + MSG_MAX_PAYLOAD];
    buf[0] = (uint8_t)msg->type;
    buf[1] = (msg->length >> 8) & 0xFF;
    buf[2] = msg->length & 0xFF;
    if (msg->length > 0) {
        memcpy(&buf[3], msg->payload, msg->length);
    }

    uint16_t computed = crc16_ccitt(buf, 3 + msg->length);
    return computed == msg->crc;
}

/* ── Type Name ─────────────────────────────────────────────────────── */

const char *msg_type_name(msg_type_t type)
{
    switch (type) {
        case MSG_HEARTBEAT:       return "HEARTBEAT";
        case MSG_STUDENT_JOIN:    return "STUDENT_JOIN";
        case MSG_STUDENT_LEAVE:   return "STUDENT_LEAVE";
        case MSG_ATTENDANCE:      return "ATTENDANCE";
        case MSG_QUIZ_START:      return "QUIZ_START";
        case MSG_QUIZ_QUESTION:   return "QUIZ_QUESTION";
        case MSG_QUIZ_ANSWER:     return "QUIZ_ANSWER";
        case MSG_QUIZ_END:        return "QUIZ_END";
        case MSG_POLL_START:      return "POLL_START";
        case MSG_POLL_OPTIONS:    return "POLL_OPTIONS";
        case MSG_POLL_VOTE:       return "POLL_VOTE";
        case MSG_POLL_END:        return "POLL_END";
        case MSG_ACK:             return "ACK";
        case MSG_NACK:            return "NACK";
        case MSG_SPI_AGGREGATE:   return "SPI_AGGREGATE";
        case MSG_SPI_COMMAND:     return "SPI_COMMAND";
        case MSG_SPI_STATUS:      return "SPI_STATUS";
        case MSG_OTA_PROMPT:      return "OTA_PROMPT";
        case MSG_OTA_APPLIED:     return "OTA_APPLIED";
        default:                  return "UNKNOWN";
    }
}

/* ── Mesh de-duplication ───────────────────────────────────────────── */

uint32_t mesh_msg_id(uint32_t sender_id, const uint8_t *frame, size_t frame_len)
{
    uint32_t h = 2166136261u;                 /* FNV-1a */
    for (int i = 0; i < 4; i++) {
        h ^= (uint8_t)(sender_id >> (8 * i));
        h *= 16777619u;
    }
    for (size_t i = 0; i < frame_len; i++) {
        h ^= frame[i];
        h *= 16777619u;
    }
    return h;
}

bool mesh_dedup_check(mesh_dedup_t *d, uint32_t id, uint32_t now_ms)
{
    for (int i = 0; i < MESH_DEDUP_SLOTS; i++) {
        if (d->used[i] && d->id[i] == id) {
            if ((uint32_t)(now_ms - d->seen_ms[i]) < MESH_DEDUP_WINDOW_MS) {
                return true;
            }
            d->seen_ms[i] = now_ms;           /* expired: treat as new */
            return false;
        }
    }
    d->id[d->next] = id;
    d->seen_ms[d->next] = now_ms;
    d->used[d->next] = 1;
    d->next = (d->next + 1) % MESH_DEDUP_SLOTS;
    return false;
}
