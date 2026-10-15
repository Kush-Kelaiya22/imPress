/* Host tests for acknowledged SPI slots (#182): two sides with send queues,
 * exchanges with corrupted slots in either direction, an unarmed gateway,
 * reboots, and old firmware on either side. Run: ./run_spi_link.sh */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "protocol.h"
#include "spi_link.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define OK(name) printf("ok   %s\n", name)

#define QMAX 64
typedef struct {
    spi_link_t link;
    bool legacy;                  /* old firmware: no trailers, drop after clocking */
    char q[QMAX][16]; int qh, qn; /* send queue of short messages */
    char got[QMAX * 4][16]; int ngot;
} side_t;

static void side_init(side_t *s, uint8_t epoch, bool announce, bool legacy)
{
    memset(s, 0, sizeof(*s));
    spi_link_init(&s->link, epoch, announce);
    s->legacy = legacy;
}

static void push(side_t *s, const char *m) { strcpy(s->q[(s->qh + s->qn++) % QMAX], m); }

/* What this side clocks out; *sent_head = it carried the queue head. */
static int build(side_t *s, uint8_t *out, bool *sent_head)
{
    const char *head = s->qn ? s->q[s->qh] : NULL;
    *sent_head = head != NULL;
    if (s->legacy) {
        size_t n = head ? strlen(head) + 1 : 0;
        if (head) memcpy(out, head, n);
        return (int)n;
    }
    return spi_link_tx(&s->link, (const uint8_t *)head, head ? strlen(head) + 1 : 0, out, SPI_SLOT_PAYLOAD_MAX);
}

/* This side received `len` bytes (len < 0: the slot failed its CRC). */
static void take(side_t *s, uint8_t *in, int len, bool sent_head)
{
    bool acked = false;
    if (len >= 0) {
        size_t data = s->legacy ? (size_t)len : spi_link_rx(&s->link, in, (size_t)len, &acked);
        if (s->legacy && data >= SPI_LINK_TRAILER && in[data - SPI_LINK_TRAILER] == 0xFF) data -= SPI_LINK_TRAILER;  /* an old side's parsers stop at FF FF */
        if (data > 0 && data <= 16) strcpy(s->got[s->ngot++], (const char *)in);
    }
    bool drop = s->legacy ? sent_head : spi_link_drop_head(&s->link, sent_head, acked);
    if (drop && s->qn) { s->qh = (s->qh + 1) % QMAX; s->qn--; }
}

/* One full-duplex exchange. bad_to_c6 / bad_to_s3: that direction's slot fails
 * its CRC. c6_unarmed: the gateway had not re-armed (the hub reads an empty
 * slot, the gateway never sees the hub's). */
static void exchange(side_t *s3, side_t *c6, bool bad_to_c6, bool bad_to_s3, bool c6_unarmed)
{
    uint8_t a[SPI_SLOT_PAYLOAD_MAX], b[SPI_SLOT_PAYLOAD_MAX];
    bool s3_head, c6_head = false;
    int na = build(s3, a, &s3_head);
    if (c6_unarmed) {
        take(s3, b, 0, s3_head);                     /* an all-zero slot: LEN 0 */
        return;
    }
    int nb = build(c6, b, &c6_head);
    take(c6, a, bad_to_c6 ? -1 : na, c6_head);
    take(s3, b, bad_to_s3 ? -1 : nb, s3_head);
}

static bool got_all_once(const side_t *s, int n, const char *prefix)
{
    if (s->ngot != n) return false;
    for (int i = 0; i < n; i++) {
        char want[16];
        snprintf(want, sizeof want, "%s%d", prefix, i);
        if (strcmp(s->got[i], want) != 0) return false;
    }
    return true;
}

static void test_clean_link_delivers_in_order(void)
{
    side_t s3, c6;
    side_init(&s3, 7, true, false); side_init(&c6, 9, false, false);
    char m[16];
    for (int i = 0; i < 20; i++) { snprintf(m, sizeof m, "u%d", i); push(&s3, m); snprintf(m, sizeof m, "d%d", i); push(&c6, m); }
    for (int i = 0; i < 100 && (s3.qn || c6.qn); i++) exchange(&s3, &c6, false, false, false);
    CHECK(s3.qn == 0 && c6.qn == 0);
    CHECK(got_all_once(&c6, 20, "u") && got_all_once(&s3, 20, "d"));
    OK("test_clean_link_delivers_in_order");
}

static void test_corruption_and_unarmed_slots_lose_nothing(void)
{
    for (unsigned seed = 1; seed <= 50; seed++) {
        srand(seed);
        side_t s3, c6;
        side_init(&s3, (uint8_t)(seed * 3 + 1), true, false); side_init(&c6, (uint8_t)(seed * 5 + 2), false, false);
        /* Boot: idle exchanges until both sides have heard the other's
         * trailer. Data queued before that uses the old rule (see spi_link.h). */
        for (int i = 0; i < 50 && !(s3.link.peer && c6.link.peer); i++)
            exchange(&s3, &c6, rand() % 4 == 0, rand() % 4 == 0, rand() % 10 == 0);
        CHECK(s3.link.peer && c6.link.peer);
        char m[16];
        for (int i = 0; i < 40; i++) { snprintf(m, sizeof m, "u%d", i); push(&s3, m); snprintf(m, sizeof m, "d%d", i); push(&c6, m); }
        for (int i = 0; i < 2000 && (s3.qn || c6.qn); i++)
            exchange(&s3, &c6, rand() % 4 == 0, rand() % 4 == 0, rand() % 10 == 0);
        if (!(s3.qn == 0 && c6.qn == 0 && got_all_once(&c6, 40, "u") && got_all_once(&s3, 40, "d"))) {
            printf("FAIL seed=%u\n", seed); exit(1);
        }
    }
    OK("test_corruption_and_unarmed_slots_lose_nothing");
}

static void test_a_rebooted_peer_is_not_mistaken_for_a_repeat(void)
{
    side_t s3, c6;
    side_init(&s3, 11, true, false); side_init(&c6, 12, false, false);
    push(&s3, "a"); push(&s3, "b");
    for (int i = 0; i < 10; i++) exchange(&s3, &c6, false, false, false);
    CHECK(c6.ngot == 2);
    side_init(&s3, 13, true, false);                 /* hub reboots: seq starts at 1 again */
    push(&s3, "c");
    for (int i = 0; i < 10; i++) exchange(&s3, &c6, false, false, false);
    CHECK(c6.ngot == 3 && strcmp(c6.got[2], "c") == 0 && s3.qn == 0);
    int before = c6.ngot;
    side_init(&c6, 14, false, false);                /* gateway reboots */
    c6.ngot = before;
    push(&s3, "d");
    for (int i = 0; i < 10; i++) exchange(&s3, &c6, false, false, false);
    CHECK(c6.ngot == before + 1 && strcmp(c6.got[before], "d") == 0 && s3.qn == 0);
    OK("test_a_rebooted_peer_is_not_mistaken_for_a_repeat");
}

static void test_new_hub_old_gateway_keeps_the_old_behaviour(void)
{
    side_t s3, c6;
    side_init(&s3, 21, true, false); side_init(&c6, 0, false, true);
    push(&s3, "u0"); push(&c6, "d0");
    exchange(&s3, &c6, false, false, false);
    CHECK(s3.qn == 0 && c6.qn == 0);                 /* both dropped after one clock, as before */
    CHECK(got_all_once(&c6, 1, "u") && got_all_once(&s3, 1, "d"));
    CHECK(!s3.link.peer);
    OK("test_new_hub_old_gateway_keeps_the_old_behaviour");
}

static void test_new_gateway_never_sends_trailers_to_an_old_hub(void)
{
    side_t s3, c6;
    side_init(&s3, 0, false, true); side_init(&c6, 31, false, false);
    push(&c6, "d0");
    uint8_t out[SPI_SLOT_PAYLOAD_MAX];
    bool head;
    int n = build(&c6, out, &head);
    CHECK(n == 3);                                   /* "d0\0" only: no trailer */
    exchange(&s3, &c6, false, false, false);
    CHECK(c6.qn == 0 && got_all_once(&s3, 1, "d"));
    OK("test_new_gateway_never_sends_trailers_to_an_old_hub");
}

static void test_old_parsers_ignore_the_trailer(void)
{
    spi_link_t l;
    spi_link_init(&l, 5, true);
    uint8_t out[64];
    int n = spi_link_tx(&l, NULL, 0, out, sizeof out);
    CHECK(n == (int)SPI_LINK_TRAILER);
    uint32_t sender; const uint8_t *frame; uint16_t flen;
    CHECK(spi_record_read(out, (size_t)n, &sender, &frame, &flen) == 0);   /* old gateway: incomplete record */
    msg_t m;
    CHECK(msg_decode(out, (size_t)n, &m) <= 0);                          /* old hub: not a frame */
    OK("test_old_parsers_ignore_the_trailer");
}

int main(void)
{
    test_clean_link_delivers_in_order();
    test_corruption_and_unarmed_slots_lose_nothing();
    test_a_rebooted_peer_is_not_mistaken_for_a_repeat();
    test_new_hub_old_gateway_keeps_the_old_behaviour();
    test_new_gateway_never_sends_trailers_to_an_old_hub();
    test_old_parsers_ignore_the_trailer();
    printf("PASS test_spi_link\n");
    return 0;
}
