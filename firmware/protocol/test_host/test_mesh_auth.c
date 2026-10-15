/* Host tests for mesh frame authentication (#187): known-answer vectors, altered/forged/replayed frames, relays, counters. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mesh_auth.h"

static int failures;
#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); failures++; } } while (0)

static void hex(const uint8_t *p, size_t n, char *out) { for (size_t i = 0; i < n; i++) snprintf(out + 2 * i, 3, "%02x", p[i]); }

static const uint8_t KEY[16] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
static const uint8_t OTHER[16] = {16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1};

static void vectors(void) {
    uint8_t d[32]; char h[65];
    mesh_auth_sha256((const uint8_t *)"abc", 3, d); hex(d, 32, h);
    CHECK(!strcmp(h, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));
    mesh_auth_sha256((const uint8_t *)"", 0, d); hex(d, 32, h);
    CHECK(!strcmp(h, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"));
    const char *two = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";            /* crosses a block boundary */
    mesh_auth_sha256((const uint8_t *)two, strlen(two), d); hex(d, 32, h);
    CHECK(!strcmp(h, "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"));
    uint8_t k[20]; memset(k, 0x0b, 20);                                                      /* RFC 4231 test case 1 */
    mesh_auth_hmac_sha256(k, 20, (const uint8_t *)"Hi There", 8, d); hex(d, 32, h);
    CHECK(!strcmp(h, "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"));
    mesh_auth_hmac_sha256((const uint8_t *)"Jefe", 4, (const uint8_t *)"what do ya want for nothing?", 28, d); hex(d, 32, h);   /* case 2 */
    CHECK(!strcmp(h, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"));
    uint8_t big[131]; memset(big, 0xaa, sizeof big);                                         /* case 6: a key longer than a block */
    mesh_auth_hmac_sha256(big, 131, (const uint8_t *)"Test Using Larger Than Block-Size Key - Hash Key First", 54, d); hex(d, 32, h);
    CHECK(!strcmp(h, "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"));
}

static void budget(void) {
    CHECK(MESH_AUTH_HDR_BYTES == 19 && MESH_AUTH_MAX_PAYLOAD == 225);
    uint8_t frame[231], pkt[256];                                                             /* a 225-byte payload + 6 bytes of framing */
    memset(frame, 7, sizeof frame);
    CHECK(mesh_auth_seal(pkt, sizeof pkt, 5, 0, 1, 1, KEY, frame, 231) == 250);              /* exactly the ESP-NOW limit */
    CHECK(mesh_auth_seal(pkt, sizeof pkt, 5, 0, 1, 1, KEY, frame, 232) == 0);                /* one byte over: refused */
    CHECK(mesh_auth_seal(pkt, 20, 5, 0, 1, 1, KEY, frame, 10) == 0);                         /* the buffer is too small */
}

static void accept_alter_forge(void) {
    uint8_t frame[40], pkt[80], tmp[80]; memset(frame, 0x42, sizeof frame);
    mesh_auth_window_t w = {0};
    uint32_t sender, counter; const uint8_t *f; size_t fl;
    size_t n = mesh_auth_seal(pkt, sizeof pkt, 5, 0, 0xCAFE0001u, 100, KEY, frame, sizeof frame);
    CHECK(n == 19 + 40);
    CHECK(mesh_auth_open(pkt, n, KEY, &w, &sender, &counter, &f, &fl) == MESH_AUTH_OK);
    CHECK(sender == 0xCAFE0001u && counter == 100 && fl == 40 && !memcmp(f, frame, 40));
    CHECK(mesh_auth_peek_sender(pkt, n, &sender) && sender == 0xCAFE0001u);
    for (size_t i = 0; i < n; i++) {                                                          /* flip every single bit of every byte */
        for (int bit = 0; bit < 8; bit++) {
            memcpy(tmp, pkt, n); tmp[i] ^= (uint8_t)(1 << bit);
            mesh_auth_window_t fresh = {0};
            mesh_auth_result_t r = mesh_auth_open(tmp, n, KEY, &fresh, &sender, &counter, &f, &fl);
            if (i == 0 || i == 5) CHECK(r == MESH_AUTH_OK);                                   /* TTL and HOPS change at every relay: not covered */
            else CHECK(r != MESH_AUTH_OK);
            if (r != MESH_AUTH_OK) CHECK(!fresh.any);                                          /* a rejected frame never moves the window */
        }
    }
    mesh_auth_window_t other = {0};
    CHECK(mesh_auth_open(pkt, n, OTHER, &other, &sender, &counter, &f, &fl) == MESH_AUTH_BAD_TAG);       /* the wrong key */
    uint8_t forged[80]; memcpy(forged, pkt, n); memset(forged + 11, 0xAA, 8);                            /* a tag made up */
    CHECK(mesh_auth_open(forged, n, KEY, &other, &sender, &counter, &f, &fl) == MESH_AUTH_BAD_TAG);
    CHECK(mesh_auth_open(pkt, 10, KEY, &other, &sender, &counter, &f, &fl) == MESH_AUTH_TOO_SHORT);
    CHECK(mesh_auth_open(pkt, 3, KEY, &other, &sender, &counter, &f, &fl) == MESH_AUTH_TOO_SHORT);
    uint8_t old[20] = {5, 1, 0, 0, 0, 0, 1 /* version 1 */}; CHECK(mesh_auth_open(old, 20, KEY, &other, &sender, &counter, &f, &fl) == MESH_AUTH_NOT_V2);
    CHECK(!mesh_auth_peek_sender(old, 20, &sender));
}

static void relays_keep_the_tag_valid(void) {
    uint8_t frame[30], pkt[64]; memset(frame, 9, sizeof frame);
    size_t n = mesh_auth_seal(pkt, sizeof pkt, 5, 0, 7, 1, KEY, frame, sizeof frame);
    mesh_auth_window_t w = {0}; uint32_t s, c; const uint8_t *f; size_t fl;
    for (int hop = 1; hop <= 5; hop++) { pkt[0]--; pkt[5] = (uint8_t)hop; CHECK(mesh_auth_open(pkt, n, KEY, &w, &s, &c, &f, &fl) == MESH_AUTH_OK || hop > 1); }
    mesh_auth_window_t w2 = {0};
    CHECK(mesh_auth_open(pkt, n, KEY, &w2, &s, &c, &f, &fl) == MESH_AUTH_OK);                 /* after five relays it still verifies */
}

static void replay(void) {
    uint8_t frame[10] = {1}, pkt[40]; mesh_auth_window_t w = {0};
    uint32_t s, c; const uint8_t *f; size_t fl;
    size_t n = mesh_auth_seal(pkt, sizeof pkt, 5, 0, 1, 10, KEY, frame, sizeof frame);
    CHECK(mesh_auth_open(pkt, n, KEY, &w, &s, &c, &f, &fl) == MESH_AUTH_OK);
    CHECK(mesh_auth_open(pkt, n, KEY, &w, &s, &c, &f, &fl) == MESH_AUTH_REPLAY);              /* the same packet again (a resend is de-duplicated above this layer) */
    uint8_t p2[40]; size_t n2 = mesh_auth_seal(p2, sizeof p2, 5, 0, 1, 12, KEY, frame, sizeof frame);
    CHECK(mesh_auth_open(p2, n2, KEY, &w, &s, &c, &f, &fl) == MESH_AUTH_OK);                  /* newer: fine */
    uint8_t p3[40]; size_t n3 = mesh_auth_seal(p3, sizeof p3, 5, 0, 1, 11, KEY, frame, sizeof frame);
    CHECK(mesh_auth_open(p3, n3, KEY, &w, &s, &c, &f, &fl) == MESH_AUTH_OK);                  /* late but inside the window and unseen: fine */
    CHECK(mesh_auth_open(p3, n3, KEY, &w, &s, &c, &f, &fl) == MESH_AUTH_REPLAY);
    mesh_auth_window_t far = {0};
    uint8_t p4[40]; size_t n4 = mesh_auth_seal(p4, sizeof p4, 5, 0, 1, 1000, KEY, frame, sizeof frame);
    CHECK(mesh_auth_open(p4, n4, KEY, &far, &s, &c, &f, &fl) == MESH_AUTH_OK);
    CHECK(mesh_auth_open(pkt, n, KEY, &far, &s, &c, &f, &fl) == MESH_AUTH_REPLAY);            /* counter 10 is far behind 1000: dropped */
    CHECK(far.highest == 1000);
}

static void window_edges(void) {
    mesh_auth_window_t w = {0};
    CHECK(mesh_auth_window_accept(&w, 0));                      /* a first counter of 0 is allowed */
    CHECK(!mesh_auth_window_accept(&w, 0));
    CHECK(mesh_auth_window_accept(&w, 63) && mesh_auth_window_accept(&w, 1));
    CHECK(!mesh_auth_window_accept(&w, 0) && !mesh_auth_window_accept(&w, 63));
    CHECK(mesh_auth_window_accept(&w, 64));                      /* 0 now falls off the window: 64 - 0 = 64 */
    CHECK(!mesh_auth_window_accept(&w, 0));                      /* too old to tell from a replay */
    CHECK(mesh_auth_window_accept(&w, 0xFFFFFFF0u) && !mesh_auth_window_accept(&w, 5));
    for (uint32_t i = 0xFFFFFFF1u; i < 0xFFFFFFFFu; i++) CHECK(mesh_auth_window_accept(&w, i));
}

static void counters(void) {
    CHECK(mesh_auth_resume_counter(0) == 64 && mesh_auth_resume_counter(640) == 704);
    CHECK(mesh_auth_resume_counter(0xFFFFFFFFu - 10) == MESH_AUTH_COUNTER_LAST);               /* near the end: spent, needs a new key */
    CHECK(mesh_auth_should_persist(0) && mesh_auth_should_persist(128) && !mesh_auth_should_persist(129));
    uint8_t pkt[40], f[4] = {0};
    CHECK(mesh_auth_seal(pkt, sizeof pkt, 5, 0, 1, MESH_AUTH_COUNTER_LAST, KEY, f, 4) == 0);  /* the last counter is never sent */
    CHECK(mesh_auth_seal(pkt, sizeof pkt, 5, 0, 1, MESH_AUTH_COUNTER_LAST - 1, KEY, f, 4) == 23);
    /* a reboot never reuses a counter: whatever was sent after the last stored value is below stored + 64 */
    uint32_t stored = 640, sent_after = stored + MESH_AUTH_PERSIST_EVERY - 1;
    CHECK(mesh_auth_resume_counter(stored) > sent_after);
}

static void two_senders_are_independent(void) {
    uint8_t frame[8] = {3}, a[40], b[40]; uint32_t s, c; const uint8_t *f; size_t fl;
    mesh_auth_window_t wa = {0}, wb = {0};
    size_t na = mesh_auth_seal(a, sizeof a, 5, 0, 1, 5, KEY, frame, 8), nb = mesh_auth_seal(b, sizeof b, 5, 0, 2, 5, OTHER, frame, 8);
    CHECK(mesh_auth_open(a, na, KEY, &wa, &s, &c, &f, &fl) == MESH_AUTH_OK && s == 1);
    CHECK(mesh_auth_open(b, nb, OTHER, &wb, &s, &c, &f, &fl) == MESH_AUTH_OK && s == 2);
    /* a module cannot pass off its frame as another sender's: changing the sender field breaks the tag */
    a[1] = 2;
    mesh_auth_window_t wc = {0};
    CHECK(mesh_auth_open(a, na, KEY, &wc, &s, &c, &f, &fl) == MESH_AUTH_BAD_TAG);
}

int main(void) {
    vectors(); budget(); accept_alter_forge(); relays_keep_the_tag_valid(); replay(); window_edges(); counters(); two_senders_are_independent();
    if (failures) { printf("%d failure(s)\n", failures); return 1; }
    puts("PASS test_mesh_auth");
    return 0;
}
