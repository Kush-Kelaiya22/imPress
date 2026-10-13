/**
 * @file ota_chunk.h
 * @brief Student-module OTA over ESP-NOW: chunking, reassembly and resume (#130).
 *
 * Pure C, no ESP-IDF: host-tested in test_host/test_ota_chunk.c with packet
 * loss, duplicates, reordering and interruptions. The hub (sender) and the
 * module (receiver) wrap these functions around the radio and the flash
 * (esp_ota_write at the returned offset). Design: docs/design/student-ota.md.
 *
 * Selective repeat: the module reports the first chunk it is missing and a
 * bitmap of the next OTA_WINDOW chunks; the hub resends only those.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#define OTA_CHUNK_BYTES   192u      /* 5 + 192 B payload, 209 B on air with mesh + frame headers (<= 250) */
#define OTA_WINDOW        64u       /* chunks covered by one status report */
#define OTA_MAX_CHUNKS    12288u    /* 2.25 MB at 192 B: above the 1.75 MB student slot */

/** One chunk on the air (MSG_OTA_CHUNK payload header). */
typedef struct __attribute__((packed)) {
    uint16_t session;   /* the transfer it belongs to; anything else is ignored */
    uint16_t seq;       /* chunk number, 0-based */
    uint8_t  len;       /* data bytes that follow, 1..OTA_CHUNK_BYTES */
} ota_chunk_hdr_t;

/** The module's progress report (MSG_OTA_STATUS payload). */
typedef struct __attribute__((packed)) {
    uint16_t session;
    uint16_t next_missing;              /* first chunk not yet received; == total when complete */
    uint64_t window;                    /* bit i set: chunk next_missing+i received */
} ota_status_t;

typedef enum {
    OTA_RX_NEW = 0,         /* store the data at *offset */
    OTA_RX_DUPLICATE,       /* already have it: ignore */
    OTA_RX_WRONG_SESSION,
    OTA_RX_BAD_SEQ,         /* beyond the image */
    OTA_RX_BAD_LEN,         /* length doesn't match the chunk's position */
} ota_rx_result_t;

typedef struct {
    uint16_t session;
    uint32_t size;              /* image bytes */
    uint16_t total;             /* chunks */
    uint16_t received;          /* distinct chunks received */
    uint16_t next_missing;
    uint8_t  bitmap[OTA_MAX_CHUNKS / 8];
} ota_rx_t;

/** Chunks needed for `size` bytes. */
uint16_t ota_chunk_count(uint32_t size);

/** Bytes in chunk `seq` of an image of `size` bytes (0 if out of range). */
uint8_t ota_chunk_len(uint32_t size, uint16_t seq);

/** Start receiving. -1 if the image is empty or larger than `slot_bytes` or OTA_MAX_CHUNKS. */
int ota_rx_init(ota_rx_t *rx, uint16_t session, uint32_t size, uint32_t slot_bytes);

/** Resume after a reboot: chunks [0, contiguous) are already in flash. */
void ota_rx_resume(ota_rx_t *rx, uint16_t contiguous);

/** Classify a received chunk; on OTA_RX_NEW *offset is where its data goes. */
ota_rx_result_t ota_rx_accept(ota_rx_t *rx, const ota_chunk_hdr_t *hdr, uint32_t *offset);

/** Fill a status report for the hub. */
void ota_rx_status(const ota_rx_t *rx, ota_status_t *out);

bool ota_rx_complete(const ota_rx_t *rx);

/** The hub's side: the chunks to (re)send after a status report, in order, at most `max`. */
size_t ota_tx_wanted(const ota_status_t *st, uint16_t total, uint16_t *out, size_t max);

/** Why a module must not start an update now; OTA_OK means it may. */
typedef enum {
    OTA_OK = 0,
    OTA_BUSY_SESSION,       /* a quiz or poll is live on the module */
    OTA_LOW_BATTERY,        /* below the minimum: a flash write must not brown out */
    OTA_SAME_VERSION,
    OTA_TOO_LARGE,
    OTA_NOT_AUTHORISED,     /* the classroom has not authorised a maintenance period */
} ota_decline_t;

ota_decline_t ota_should_accept(bool session_live, uint8_t battery_pct, uint8_t min_battery_pct,
                                bool same_version, uint32_t size, uint32_t slot_bytes, bool authorised);
