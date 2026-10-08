/**
 * @file protocol.h
 * @brief Shared message protocol for imPress class participation system.
 *
 * Binary framing used across all ESP32 modules (Student, S3, C6):
 *   [START:1][TYPE:1][LENGTH:2][PAYLOAD:N][CRC16:2]
 *
 * - START:   0xAA magic byte
 * - TYPE:    Message type enum (msg_type_t)
 * - LENGTH:  Payload length in bytes (big-endian uint16)
 * - PAYLEN:  N bytes of payload (N = LENGTH)
 * - CRC16:   CRC-16/CCITT of TYPE + LENGTH + PAYLOAD
 */

#pragma once

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── Constants ─────────────────────────────────────────────────────── */

#define MSG_START_BYTE      0xAA
#define MSG_HEADER_SIZE     4       /* start(1) + type(1) + length(2) */
#define MSG_CRC_SIZE        2
#define MSG_OVERHEAD        (MSG_HEADER_SIZE + MSG_CRC_SIZE)  /* 6 bytes total overhead */
#define MSG_MAX_PAYLOAD     240     /* max payload to fit ESP-NOW 250-byte limit */
#define MSG_MAX_SIZE        (MSG_OVERHEAD + MSG_MAX_PAYLOAD)  /* 246 bytes max on wire */

/* ── Message Types ─────────────────────────────────────────────────── */

typedef enum {
    /* Device → Backend (via mesh → SPI → WiFi) */
    MSG_HEARTBEAT        = 0x01,   /* periodic alive ping */
    MSG_STUDENT_JOIN     = 0x02,   /* student module joining mesh */
    MSG_STUDENT_LEAVE    = 0x03,   /* student module leaving mesh */
    MSG_ATTENDANCE       = 0x04,   /* attendance confirmation */

    /* Quiz flow */
    MSG_QUIZ_START       = 0x10,   /* backend → students: quiz begins */
    MSG_QUIZ_QUESTION    = 0x11,   /* backend → students: question broadcast */
    MSG_QUIZ_ANSWER      = 0x12,   /* students → backend: answer submission */
    MSG_QUIZ_END         = 0x13,   /* backend → students: quiz ended */

    /* Poll flow */
    MSG_POLL_START       = 0x20,   /* backend → students: poll begins */
    MSG_POLL_OPTIONS     = 0x21,   /* backend → students: poll options */
    MSG_POLL_VOTE        = 0x22,   /* students → backend: vote submission */
    MSG_POLL_END         = 0x23,   /* backend → students: poll ended, results */

    /* Acknowledgment */
    MSG_ACK              = 0x30,   /* generic acknowledgment */
    MSG_NACK             = 0x31,   /* negative acknowledgment / error */

    /* SPI transport (internal between S3 ↔ C6) */
    MSG_SPI_AGGREGATE    = 0x40,   /* S3 → C6: batch of student data */
    MSG_SPI_COMMAND      = 0x41,   /* C6 → S3: command from backend */
    MSG_SPI_STATUS       = 0x42,   /* C6 → S3: WiFi/backend status */

    /* OTA */
    MSG_OTA_PROMPT       = 0x50,   /* C6 → S3: server says "fetch the update" */
    MSG_OTA_APPLIED      = 0x51,   /* S3 → C6: OTA finished, report to server */

    MSG_UNKNOWN          = 0xFF,
} msg_type_t;

/* ── Parsed Message ────────────────────────────────────────────────── */

typedef struct {
    msg_type_t type;
    uint16_t   length;             /* payload length */
    uint8_t    payload[MSG_MAX_PAYLOAD];
    uint16_t   crc;                /* received CRC (for verification) */
} msg_t;

/* ── Payload Structures (packed, network byte order) ───────────────── */

/** Heartbeat: device reports its status */
typedef struct __attribute__((packed)) {
    uint32_t device_id;            /* unique device identifier */
    uint8_t  battery_pct;          /* 0-100 */
    int8_t   rssi;                 /* signal strength */
    uint32_t uptime_s;             /* seconds since boot */
} payload_heartbeat_t;

/** Student join: sent when student connects to mesh */
typedef struct __attribute__((packed)) {
    char     enrollment[11];        /* 10-char enrollment number + NUL (identity) */
    uint32_t device_id;             /* optional diagnostic, 0 = unknown */
    uint16_t student_id;            /* legacy assigned student number */
    char     name[32];              /* display name (null-terminated) */
} payload_student_join_t;

/** Student leave: sent when student times out or explicitly leaves mesh */
typedef struct __attribute__((packed)) {
    char     enrollment[11];        /* 10-char enrollment number + NUL (identity) */
    uint32_t device_id;             /* optional diagnostic, 0 = unknown */
    uint8_t  reason;                /* 0=timeout, 1=explicit leave, 2=graceful shutdown */
} payload_student_leave_t;

/** Quiz question payload (max 200 bytes) */
typedef struct __attribute__((packed)) {
    uint16_t quiz_id;
    uint8_t  question_num;         /* 0-based index */
    uint8_t  num_options;          /* A/B/C/D count */
    uint32_t time_limit_s;         /* seconds to answer */
    char     question_text[140];   /* question (null-terminated) */
    char     options[4][15];       /* option texts (null-terminated) */
} payload_quiz_question_t;

/** Quiz answer: student → backend */
typedef struct __attribute__((packed)) {
    uint16_t quiz_id;
    uint8_t  question_num;
    uint8_t  selected_option;      /* 0=A, 1=B, 2=C, 3=D */
    uint32_t response_time_ms;     /* how fast they answered */
    char     enrollment[11];       /* 10-char enrollment number + NUL (identity) */
    uint32_t device_id;            /* optional diagnostic, 0 = unknown */
} payload_quiz_answer_t;

/** Poll vote: student → backend */
typedef struct __attribute__((packed)) {
    uint16_t poll_id;
    uint8_t  selected_option;
    char     enrollment[11];       /* 10-char enrollment number + NUL (identity) */
    uint32_t device_id;            /* optional diagnostic, 0 = unknown */
} payload_poll_vote_t;

/** Poll start: backend → students (MSG_POLL_START) */
typedef struct __attribute__((packed)) {
    uint16_t poll_id;
    uint8_t  num_options;          /* buttons A.. (max 4) */
    char     title[64];            /* poll question (null-terminated) */
} payload_poll_start_t;

/** Quiz / poll end: backend → students (MSG_QUIZ_END / MSG_POLL_END) */
typedef struct __attribute__((packed)) {
    uint16_t id;                   /* quiz_id or poll_id */
} payload_session_end_t;

/** SPI aggregate: S3 batches multiple student messages for C6 */
typedef struct __attribute__((packed)) {
    uint8_t  count;                /* number of messages in batch */
    uint16_t total_size;           /* total bytes following */
    /* followed by `count` serialized messages */
} payload_spi_aggregate_t;

/** OTA prompt: C6 → S3 when the server holds a new S3 firmware build.
 *  S3 should temporarily attach to WiFi, fetch the binary, apply it, and
 *  return to mesh + SPI master duty. */
typedef struct __attribute__((packed)) {
    char     version[32];          /* target version, e.g. "1.2.0" */
    char     token[64];            /* one-time download token, 0 = none */
} payload_ota_prompt_t;

/** OTA result: S3 -> C6 -> backend (MSG_OTA_APPLIED, an SPI record from
 *  sender 0). Sent after rebooting into the new image (APPLIED), when the
 *  bootloader rolled back to the previous one (ROLLED_BACK), or when an
 *  attempt failed before any reboot (FAILED, with the esp_err_t). The
 *  backend records success only from APPLIED with the expected version. */
typedef enum {
    OTA_RESULT_APPLIED     = 0,
    OTA_RESULT_ROLLED_BACK = 1,
    OTA_RESULT_FAILED      = 2,
} ota_result_code_t;

typedef struct __attribute__((packed)) {
    char     version[32];          /* running version (APPLIED) / attempted target */
    char     mac[13];              /* reporting device, 12 hex + NUL, as it registered */
    uint8_t  result;               /* ota_result_code_t */
    int32_t  error;                /* esp_err_t, 0 if none */
} payload_ota_result_t;

/* ── API Functions ─────────────────────────────────────────────────── */

/**
 * @brief Encode a message into a byte buffer.
 * @param type       Message type
 * @param payload    Pointer to payload data (can be NULL if length=0)
 * @param length     Payload length in bytes
 * @param out_buf    Output buffer (must be at least MSG_OVERHEAD + length)
 * @param out_size   Size of output buffer
 * @return Number of bytes written, or -1 on error
 */
int msg_encode(msg_type_t type, const uint8_t *payload, uint16_t length,
               uint8_t *out_buf, size_t out_size);

/**
 * @brief Decode a message from a byte buffer.
 * @param data       Input buffer
 * @param data_len   Available bytes in buffer
 * @param out_msg    Output parsed message
 * @return Number of bytes consumed (including overhead), 0 if incomplete,
 *         -1 if invalid (bad start byte or CRC)
 */
int msg_decode(const uint8_t *data, size_t data_len, msg_t *out_msg);

/**
 * @brief Validate a message's CRC.
 * @param msg  Parsed message (with crc field set)
 * @return true if CRC matches
 */
bool msg_verify_crc(const msg_t *msg);

/**
 * @brief Compute CRC-16/CCITT over data.
 * @param data  Data buffer
 * @param len   Number of bytes
 * @return CRC-16 value
 */
uint16_t crc16_ccitt(const uint8_t *data, size_t len);

/**
 * @brief Get human-readable name for a message type.
 */
const char *msg_type_name(msg_type_t type);

/* ── SPI batch record (S3 → C6) ────────────────────────────────────────
 * One S3 slot payload is a sequence of records:
 *   [FRAME_LEN:2 BE][SENDER_ID:4 LE][FRAME:FRAME_LEN]
 * FRAME_LEN counts the protocol frame ONLY (not the sender id). Both ends
 * MUST use these helpers so the layout cannot drift again.
 */
#define SPI_RECORD_HEADER_SIZE 6

/**
 * @brief Append one record. @return bytes written, or -1 if it doesn't fit.
 */
int spi_record_write(uint8_t *out, size_t out_size, uint32_t sender_id,
                     const uint8_t *frame, uint16_t frame_len);

/**
 * @brief Parse the record at the start of buf.
 * @return bytes consumed (> 0), or 0 if buf holds no complete record.
 */
int spi_record_read(const uint8_t *buf, size_t buf_len, uint32_t *sender_id,
                    const uint8_t **frame, uint16_t *frame_len);

/* ── SPI slot (S3 <-> C6, both directions) ──────────────────────────────
 * Every SPI exchange moves exactly one fixed-size slot each way (standard
 * full-duplex SPI, S3 = master):
 *   [LEN:2 BE][PAYLOAD:LEN][CRC16:2 BE, crc16_ccitt over PAYLOAD][zero pad]
 * LEN = 0 (an all-zero slot) means "nothing to send".
 * Each side queues outgoing payloads in a spi_slot_fifo_t, so back-to-back
 * frames are never overwritten (they were, with a single latest-wins slot).
 * Locking is the caller's job; the FIFO itself is plain data.
 */
#define SPI_SLOT_BYTES        4096
#define SPI_SLOT_OVERHEAD     4      /* LEN(2) + CRC(2) */
#define SPI_SLOT_PAYLOAD_MAX  (SPI_SLOT_BYTES - SPI_SLOT_OVERHEAD)

#define SPI_SLOT_ERR_LEN      (-1)   /* LEN larger than the slot can hold */
#define SPI_SLOT_ERR_CRC      (-2)   /* CRC mismatch: corrupted transfer */
#define SPI_SLOT_ERR_SPACE    (-3)   /* caller buffer smaller than LEN */

/** @brief Build a slot (zero-padded). @return 0, or SPI_SLOT_ERR_LEN. */
int spi_slot_encode(uint8_t *slot, const uint8_t *data, size_t len);

/**
 * @brief Validate a received slot and copy its payload.
 * @return payload length (0 = empty slot) or a negative SPI_SLOT_ERR_*.
 */
int spi_slot_decode(const uint8_t *slot, uint8_t *out, size_t out_size);

#define SPI_SLOT_FIFO_DEPTH   8

typedef struct {
    uint8_t  slot[SPI_SLOT_FIFO_DEPTH][SPI_SLOT_BYTES];  /* encoded, ready to clock */
    uint8_t  head;
    uint8_t  count;
    uint32_t dropped;                                    /* pushes refused: FIFO full */
} spi_slot_fifo_t;

void spi_slot_fifo_init(spi_slot_fifo_t *f);

/** @brief Encode and enqueue. @return 0, SPI_SLOT_ERR_LEN, or -4 when full. */
int spi_slot_fifo_push(spi_slot_fifo_t *f, const uint8_t *data, size_t len);

/** @brief Copy the oldest slot into out (an all-zero slot when empty).
 *  @return true if a queued slot was copied. Does not remove it. */
bool spi_slot_fifo_peek(const spi_slot_fifo_t *f, uint8_t *out);

/** @brief Remove the oldest slot (after it was actually clocked out). */
void spi_slot_fifo_drop(spi_slot_fifo_t *f);

static inline unsigned spi_slot_fifo_count(const spi_slot_fifo_t *f) { return f->count; }

/* ── Mesh de-duplication ───────────────────────────────────────────────
 * A message relayed through the mesh is the same message at every hop:
 * identify it by (origin sender_id, protocol frame) — NEVER by the mesh
 * header, whose ttl/hops change on every relay.
 */
uint32_t mesh_msg_id(uint32_t sender_id, const uint8_t *frame, size_t frame_len);

#define MESH_DEDUP_SLOTS      64
#define MESH_DEDUP_WINDOW_MS  10000u   /* relay copies arrive within ms; retries after */

typedef struct {
    uint32_t id[MESH_DEDUP_SLOTS];
    uint32_t seen_ms[MESH_DEDUP_SLOTS];
    uint8_t  used[MESH_DEDUP_SLOTS];
    int      next;
} mesh_dedup_t;

/**
 * @brief Record id; @return true if it was already seen within the window.
 *        Caller supplies a monotonic ms clock (wraps safely). Not thread-safe.
 */
bool mesh_dedup_check(mesh_dedup_t *d, uint32_t id, uint32_t now_ms);

#ifdef __cplusplus
}
#endif
