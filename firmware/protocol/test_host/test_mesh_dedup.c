/* Host tests for mesh de-duplication (#6): mesh_msg_id() + mesh_dedup_check(),
 * plus a relay-storm simulation of a fully connected classroom comparing the
 * legacy student rule (hash of the first 20 bytes INCLUDING ttl/hops) with the
 * new one. Run: ./run_mesh_dedup.sh */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "protocol.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)

typedef struct __attribute__((packed)) { uint8_t ttl; uint32_t sender_id; uint8_t hops; } hdr_t;
#define TTL 5

static int vote_frame(uint8_t *out, uint8_t option)
{
    payload_poll_vote_t v = { .poll_id = 3, .selected_option = option, .enrollment = "ABCDE12345" };
    return msg_encode(MSG_POLL_VOTE, (const uint8_t *)&v, sizeof v, out, MSG_MAX_SIZE);
}

static void test_id_ignores_hops_but_not_content(void)
{
    uint8_t f1[MSG_MAX_SIZE], f2[MSG_MAX_SIZE];
    int n1 = vote_frame(f1, 1), n2 = vote_frame(f2, 2);
    uint32_t a = mesh_msg_id(0x1111, f1, n1);
    CHECK(a == mesh_msg_id(0x1111, f1, n1));       /* every relay copy: same id */
    CHECK(a != mesh_msg_id(0x2222, f1, n1));       /* other student, same press */
    CHECK(a != mesh_msg_id(0x1111, f2, n2));       /* same student, other option */
    puts("ok   test_id_ignores_hops_but_not_content");
}

static void test_dedup_window_and_wrap(void)
{
    static mesh_dedup_t d;
    memset(&d, 0, sizeof d);
    CHECK(!mesh_dedup_check(&d, 42, 1000));
    CHECK(mesh_dedup_check(&d, 42, 1000 + MESH_DEDUP_WINDOW_MS - 1));   /* relay copy */
    CHECK(!mesh_dedup_check(&d, 42, 1000 + MESH_DEDUP_WINDOW_MS + 5));  /* later retry = new */
    memset(&d, 0, sizeof d);
    CHECK(!mesh_dedup_check(&d, 7, 0xFFFFFF00u));                      /* tick wrap-around */
    CHECK(mesh_dedup_check(&d, 7, 0x00000100u));
    puts("ok   test_dedup_window_and_wrap");
}

static void test_ring_evicts_oldest(void)
{
    static mesh_dedup_t d;
    memset(&d, 0, sizeof d);
    for (uint32_t i = 0; i < MESH_DEDUP_SLOTS + 1; i++) CHECK(!mesh_dedup_check(&d, 100 + i, 5));
    CHECK(!mesh_dedup_check(&d, 100, 5));          /* slot 0 was overwritten */
    CHECK(mesh_dedup_check(&d, 100 + MESH_DEDUP_SLOTS, 5));
    puts("ok   test_ring_evicts_oldest");
}

/* ── Relay storm simulation ─────────────────────────────────────────── */

#define MAXN 32
typedef struct { hdr_t h; uint8_t frame[MSG_MAX_SIZE]; int flen; int from; } pkt_t;
static pkt_t q[200000];
static int qh, qt;

static uint32_t legacy_hash(const uint8_t *data, size_t len)   /* old compute_msg_hash */
{
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < len && i < 20; i++) { h ^= data[i]; h *= 16777619u; }
    return h;
}

typedef struct { uint32_t seen[4096]; int n; } legacy_cache_t;
static int legacy_seen(legacy_cache_t *c, uint32_t h)
{
    for (int i = 0; i < c->n; i++) if (c->seen[i] == h) return 1;
    c->seen[c->n++] = h;
    return 0;
}

/* One student press heard by everyone; node 0 is the S3 root.
 * Returns transmissions on air; *root_fwd = copies the root forwards to C6. */
static int simulate(int students, int use_new, int *root_fwd)
{
    static mesh_dedup_t nd[MAXN];
    static legacy_cache_t lc[MAXN];
    memset(nd, 0, sizeof nd); memset(lc, 0, sizeof lc);
    qh = qt = 0; *root_fwd = 0;
    pkt_t p = { .h = { TTL, 0x1001, 0 }, .from = 1 };
    p.flen = vote_frame(p.frame, 1);
    q[qt++] = p;
    int tx = 0;
    while (qh < qt) {
        pkt_t cur = q[qh++];
        tx++;
        for (int node = 0; node <= students; node++) {
            if (node == cur.from) continue;
            if (node == 0) {                       /* S3 root */
                if (!use_new || !mesh_dedup_check(&nd[0], mesh_msg_id(cur.h.sender_id, cur.frame, cur.flen), 0))
                    (*root_fwd)++;
                continue;
            }
            if (node == 1) continue;               /* originator ignores its own */
            int dup;
            if (use_new) {
                dup = mesh_dedup_check(&nd[node], mesh_msg_id(cur.h.sender_id, cur.frame, cur.flen), 0);
            } else {
                uint8_t raw[sizeof(hdr_t) + MSG_MAX_SIZE];
                memcpy(raw, &cur.h, sizeof(hdr_t)); memcpy(raw + sizeof(hdr_t), cur.frame, cur.flen);
                dup = legacy_seen(&lc[node], legacy_hash(raw, sizeof(hdr_t) + cur.flen));
            }
            if (!dup && cur.h.ttl > 1) {
                pkt_t r = cur;
                r.h.ttl--; r.h.hops++; r.from = node;
                CHECK(qt < (int)(sizeof q / sizeof q[0]));
                q[qt++] = r;
            }
        }
    }
    return tx;
}

static void test_relay_storm(void)
{
    for (int n = 3; n <= 30; n += 9) {
        int old_fwd, new_fwd;
        int old_tx = simulate(n, 0, &old_fwd);
        int new_tx = simulate(n, 1, &new_fwd);
        printf("     %2d students: legacy %6d tx, root forwards %6d | new %3d tx, root forwards %d\n",
               n, old_tx, old_fwd, new_tx, new_fwd);
        CHECK(new_fwd == 1);                       /* exactly one copy reaches the C6 */
        CHECK(new_tx == n);                        /* origin + each other student relays once */
        CHECK(old_fwd > new_fwd && old_tx > new_tx);
    }
    puts("ok   test_relay_storm");
}

int main(void)
{
    test_id_ignores_hops_but_not_content();
    test_dedup_window_and_wrap();
    test_ring_evicts_oldest();
    test_relay_storm();
    puts("PASS test_mesh_dedup");
    return 0;
}
