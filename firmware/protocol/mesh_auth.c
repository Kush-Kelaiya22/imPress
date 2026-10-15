#include "mesh_auth.h"

#include <string.h>

/* ── SHA-256 (FIPS 180-4) ─────────────────────────────────────────────── */

typedef struct { uint32_t h[8]; uint8_t buf[64]; uint64_t total; size_t fill; } sha_ctx;

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
    0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
    0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

#define ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static void sha_block(sha_ctx *c, const uint8_t *p) {
    uint32_t w[64], a, b, cc, d, e, f, g, h;
    for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 | (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    a = c->h[0]; b = c->h[1]; cc = c->h[2]; d = c->h[3]; e = c->h[4]; f = c->h[5]; g = c->h[6]; h = c->h[7];
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h + (ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
        uint32_t t2 = (ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)) + ((a & b) ^ (a & cc) ^ (b & cc));
        h = g; g = f; f = e; e = d + t1; d = cc; cc = b; b = a; a = t1 + t2;
    }
    c->h[0] += a; c->h[1] += b; c->h[2] += cc; c->h[3] += d; c->h[4] += e; c->h[5] += f; c->h[6] += g; c->h[7] += h;
}

static void sha_init(sha_ctx *c) {
    static const uint32_t iv[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    memcpy(c->h, iv, sizeof iv);
    c->total = 0;
    c->fill = 0;
}

static void sha_update(sha_ctx *c, const uint8_t *d, size_t n) {
    c->total += n;
    while (n) {
        size_t take = 64 - c->fill < n ? 64 - c->fill : n;
        memcpy(c->buf + c->fill, d, take);
        c->fill += take; d += take; n -= take;
        if (c->fill == 64) { sha_block(c, c->buf); c->fill = 0; }
    }
}

static void sha_final(sha_ctx *c, uint8_t out[32]) {
    uint64_t bits = c->total * 8;
    uint8_t pad = 0x80;
    sha_update(c, &pad, 1);
    pad = 0;
    while (c->fill != 56) sha_update(c, &pad, 1);
    uint8_t len[8];
    for (int i = 0; i < 8; i++) len[i] = (uint8_t)(bits >> (56 - 8 * i));
    sha_update(c, len, 8);
    for (int i = 0; i < 8; i++) { out[4 * i] = (uint8_t)(c->h[i] >> 24); out[4 * i + 1] = (uint8_t)(c->h[i] >> 16); out[4 * i + 2] = (uint8_t)(c->h[i] >> 8); out[4 * i + 3] = (uint8_t)c->h[i]; }
}

void mesh_auth_sha256(const uint8_t *data, size_t len, uint8_t out[32]) {
    sha_ctx c;
    sha_init(&c);
    sha_update(&c, data, len);
    sha_final(&c, out);
}

/* ── HMAC-SHA256 (RFC 2104), over up to three pieces so nothing is copied ─────────── */

static void hmac3(const uint8_t *key, size_t kl, const uint8_t *a, size_t al, const uint8_t *b, size_t bl,
                  const uint8_t *d, size_t dl, uint8_t out[32]) {
    uint8_t k[64] = {0}, ipad[64], opad[64], inner[32];
    if (kl > 64) mesh_auth_sha256(key, kl, k); else memcpy(k, key, kl);
    for (int i = 0; i < 64; i++) { ipad[i] = k[i] ^ 0x36; opad[i] = k[i] ^ 0x5c; }
    sha_ctx c;
    sha_init(&c); sha_update(&c, ipad, 64); sha_update(&c, a, al); sha_update(&c, b, bl); sha_update(&c, d, dl); sha_final(&c, inner);
    sha_init(&c); sha_update(&c, opad, 64); sha_update(&c, inner, 32); sha_final(&c, out);
}

void mesh_auth_hmac_sha256(const uint8_t *key, size_t key_len, const uint8_t *data, size_t len, uint8_t out[32]) {
    hmac3(key, key_len, data, len, data, 0, data, 0, out);
}

/* ── frames ───────────────────────────────────────────────────────────── */

static void put32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24); }
static uint32_t get32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }

/* tag = HMAC(key, SENDER || VERSION || COUNTER || frame): the header fields that do not change in flight, in a fixed order */
static void tag_of(const uint8_t *key, const uint8_t *hdr_sender, uint8_t version, const uint8_t *hdr_counter, const uint8_t *frame,
                   size_t frame_len, uint8_t out[MESH_AUTH_TAG_BYTES]) {
    uint8_t head[9], mac[32];
    memcpy(head, hdr_sender, 4);
    head[4] = version;
    memcpy(head + 5, hdr_counter, 4);
    hmac3(key, MESH_AUTH_KEY_BYTES, head, sizeof head, frame, frame_len, frame, 0, mac);
    memcpy(out, mac, MESH_AUTH_TAG_BYTES);
}

size_t mesh_auth_seal(uint8_t *out, size_t cap, uint8_t ttl, uint8_t hops, uint32_t sender, uint32_t counter,
                      const uint8_t key[MESH_AUTH_KEY_BYTES], const uint8_t *frame, size_t frame_len) {
    if (counter == MESH_AUTH_COUNTER_LAST) return 0;
    if (frame_len > MESH_AUTH_ESPNOW_MAX - MESH_AUTH_HDR_BYTES || cap < MESH_AUTH_HDR_BYTES + frame_len) return 0;
    out[0] = ttl;
    put32(out + 1, sender);
    out[5] = hops;
    out[6] = MESH_AUTH_VERSION;
    put32(out + 7, counter);
    tag_of(key, out + 1, MESH_AUTH_VERSION, out + 7, frame, frame_len, out + 11);
    memcpy(out + MESH_AUTH_HDR_BYTES, frame, frame_len);
    return MESH_AUTH_HDR_BYTES + frame_len;
}

bool mesh_auth_peek_sender(const uint8_t *pkt, size_t len, uint32_t *sender) {
    if (len < MESH_AUTH_HDR_BYTES || pkt[6] != MESH_AUTH_VERSION) return false;
    *sender = get32(pkt + 1);
    return true;
}

bool mesh_auth_window_accept(mesh_auth_window_t *w, uint32_t counter) {
    if (!w->any) { w->any = true; w->highest = counter; w->seen = 1; return true; }
    if (counter > w->highest) {
        uint32_t shift = counter - w->highest;
        w->seen = shift >= 64 ? 0 : w->seen << shift;
        w->seen |= 1;
        w->highest = counter;
        return true;
    }
    uint32_t back = w->highest - counter;
    if (back >= 64) return false;                  /* older than the window: cannot be told from a replay */
    if (w->seen & ((uint64_t)1 << back)) return false;
    w->seen |= (uint64_t)1 << back;
    return true;
}

mesh_auth_result_t mesh_auth_open(const uint8_t *pkt, size_t len, const uint8_t key[MESH_AUTH_KEY_BYTES], mesh_auth_window_t *window,
                                  uint32_t *sender, uint32_t *counter, const uint8_t **frame, size_t *frame_len) {
    if (len < 7) return MESH_AUTH_TOO_SHORT;
    if (pkt[6] != MESH_AUTH_VERSION) return MESH_AUTH_NOT_V2;
    if (len < MESH_AUTH_HDR_BYTES) return MESH_AUTH_TOO_SHORT;
    uint8_t want[MESH_AUTH_TAG_BYTES], diff = 0;
    tag_of(key, pkt + 1, pkt[6], pkt + 7, pkt + MESH_AUTH_HDR_BYTES, len - MESH_AUTH_HDR_BYTES, want);
    for (int i = 0; i < MESH_AUTH_TAG_BYTES; i++) diff |= want[i] ^ pkt[11 + i];       /* constant time */
    if (diff) return MESH_AUTH_BAD_TAG;
    uint32_t c = get32(pkt + 7);
    if (!mesh_auth_window_accept(window, c)) return MESH_AUTH_REPLAY;
    *sender = get32(pkt + 1);
    *counter = c;
    *frame = pkt + MESH_AUTH_HDR_BYTES;
    *frame_len = len - MESH_AUTH_HDR_BYTES;
    return MESH_AUTH_OK;
}

uint32_t mesh_auth_resume_counter(uint32_t stored) {
    return stored > MESH_AUTH_COUNTER_LAST - MESH_AUTH_PERSIST_EVERY - 1 ? MESH_AUTH_COUNTER_LAST : stored + MESH_AUTH_PERSIST_EVERY;
}

bool mesh_auth_should_persist(uint32_t counter) { return counter % MESH_AUTH_PERSIST_EVERY == 0; }
