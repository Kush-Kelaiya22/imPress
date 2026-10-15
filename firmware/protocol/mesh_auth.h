/* Mesh frame authentication (#187, docs/design/mesh-authentication.md): a truncated HMAC-SHA256 tag and a per-sender counter
 * on every mesh frame, so a frame that was altered, forged without the key, or recorded and sent again is dropped.
 *
 * This is the host-tested core: pure C with no ESP-IDF dependency, so the same code runs on the modules, the hub and in the
 * tests. It is NOT yet wired into mesh_espnow.c / mesh_master.c: doing that changes the on-air format and needs the three
 * decisions at the end of the design note and bench tests (#183, #184, #185).
 *
 * Version-2 mesh header (19 bytes, replacing the 6-byte one):
 *     TTL(1) SENDER(4, little endian) HOPS(1) VERSION(1) = 2, COUNTER(4, little endian) TAG(8)  then the protocol frame
 *     TAG = first 8 bytes of HMAC-SHA256(key, SENDER || VERSION || COUNTER || frame)
 * TTL and HOPS change at every relay, so they are outside the tag. A resend repeats the identical packet, counter included.
 * Integrity and freshness only: ESP-NOW broadcast stays plaintext. */
#ifndef MESH_AUTH_H
#define MESH_AUTH_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define MESH_AUTH_VERSION        2
#define MESH_AUTH_KEY_BYTES      16
#define MESH_AUTH_TAG_BYTES      8
#define MESH_AUTH_HDR_BYTES      19
#define MESH_AUTH_ESPNOW_MAX     250
#define MESH_AUTH_FRAME_OVERHEAD 6          /* MSG_OVERHEAD of protocol.h */
#define MESH_AUTH_MAX_PAYLOAD    (MESH_AUTH_ESPNOW_MAX - MESH_AUTH_HDR_BYTES - MESH_AUTH_FRAME_OVERHEAD)   /* 225 */
#define MESH_AUTH_PERSIST_EVERY  64         /* the counter is written to NVS every 64 frames */
#define MESH_AUTH_COUNTER_LAST   0xFFFFFFFFu /* never sent: a sender that reaches it must be given a new key */

typedef enum {
    MESH_AUTH_OK = 0,
    MESH_AUTH_TOO_SHORT,
    MESH_AUTH_NOT_V2,          /* an old module: the room's policy decides (accept as unauthenticated, or drop) */
    MESH_AUTH_BAD_TAG,         /* altered, or made without the key */
    MESH_AUTH_REPLAY,          /* a counter already seen, or too old for the window */
} mesh_auth_result_t;

/* Per-sender replay state: the highest counter seen and which of the 64 below it were seen. */
typedef struct {
    uint32_t highest;
    uint64_t seen;             /* bit i set: counter (highest - i) was accepted */
    bool     any;
} mesh_auth_window_t;

void mesh_auth_sha256(const uint8_t *data, size_t len, uint8_t out[32]);
void mesh_auth_hmac_sha256(const uint8_t *key, size_t key_len, const uint8_t *data, size_t len, uint8_t out[32]);

/* Build a packet in `out` (cap bytes). Returns its length, or 0 when it does not fit the budget or the counter is spent. */
size_t mesh_auth_seal(uint8_t *out, size_t cap, uint8_t ttl, uint8_t hops, uint32_t sender, uint32_t counter,
                      const uint8_t key[MESH_AUTH_KEY_BYTES], const uint8_t *frame, size_t frame_len);

/* Check a packet. On MESH_AUTH_OK, `*sender`, `*counter` and `*frame` (a pointer into `pkt`) are set and the window is updated.
 * The window is changed only for a packet whose tag verified. */
mesh_auth_result_t mesh_auth_open(const uint8_t *pkt, size_t len, const uint8_t key[MESH_AUTH_KEY_BYTES],
                                  mesh_auth_window_t *window, uint32_t *sender, uint32_t *counter,
                                  const uint8_t **frame, size_t *frame_len);

/* Read the sender without verifying (to look its key up): false if the packet is too short or not version 2. */
bool mesh_auth_peek_sender(const uint8_t *pkt, size_t len, uint32_t *sender);

/* Replay window on its own. */
bool mesh_auth_window_accept(mesh_auth_window_t *w, uint32_t counter);

/* Counter persistence: after a reboot continue above anything that may have been sent since the last stored value. */
uint32_t mesh_auth_resume_counter(uint32_t stored);
bool     mesh_auth_should_persist(uint32_t counter);

#endif
