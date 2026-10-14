/* Host tests for the delivery acknowledgement state machine (#181). */
#include "protocol.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define OK(name) printf("ok   %s\n", name)

static void test_resends_then_fails(void)
{
    answer_tx_t t;
    answer_tx_start(&t, 0xABCD1234u, 1000, 100);                 /* due at 1000 + 600 + 100 */
    CHECK(t.state == ANSWER_PENDING);
    CHECK(!answer_tx_poll(&t, 1699, 0));                         /* not yet */
    uint32_t now = 1700;
    for (int i = 1; i <= ANSWER_RESENDS; i++) {
        CHECK(answer_tx_poll(&t, now, 0));                       /* resend i */
        CHECK(t.resends == i && t.state == ANSWER_PENDING);
        CHECK(!answer_tx_poll(&t, now + ANSWER_RESEND_MS - 1, 0));
        now += ANSWER_RESEND_MS;
    }
    CHECK(!answer_tx_poll(&t, now, 0));                          /* the last wait is over */
    CHECK(t.state == ANSWER_FAILED);
    CHECK(!answer_tx_poll(&t, now + 10000, 0));                  /* stays failed, never resends */
    OK("test_resends_then_fails");
}

static void test_ack_delivers_and_stops_resends(void)
{
    answer_tx_t t;
    answer_tx_start(&t, 77, 0, 0);
    payload_ack_t other_dev = {.msg_id = 77, .device_id = 2, .seq = 1};
    payload_ack_t other_msg = {.msg_id = 78, .device_id = 1, .seq = 2};
    payload_ack_t mine = {.msg_id = 77, .device_id = 1, .seq = 3};
    CHECK(!answer_tx_ack(&t, &other_dev, 1));
    CHECK(!answer_tx_ack(&t, &other_msg, 1));
    CHECK(t.state == ANSWER_PENDING);
    CHECK(answer_tx_ack(&t, &mine, 1) && t.state == ANSWER_DELIVERED);
    CHECK(!answer_tx_poll(&t, 100000, 0));
    CHECK(!answer_tx_ack(&t, &mine, 1));                         /* a late duplicate ACK changes nothing */
    OK("test_ack_delivers_and_stops_resends");
}

static void test_ack_after_failure_is_ignored(void)
{
    answer_tx_t t;
    answer_tx_start(&t, 5, 0, 0);
    uint32_t now = 0;
    while (t.state == ANSWER_PENDING) { now += 50; answer_tx_poll(&t, now, 0); }
    payload_ack_t late = {.msg_id = 5, .device_id = 9, .seq = 1};
    CHECK(t.state == ANSWER_FAILED && !answer_tx_ack(&t, &late, 9));
    OK("test_ack_after_failure_is_ignored");
}

static void test_clock_wrap(void)
{
    answer_tx_t t;
    answer_tx_start(&t, 1, UINT32_MAX - 100, 0);                  /* due wraps past 0 */
    CHECK(!answer_tx_poll(&t, UINT32_MAX - 50, 0));
    CHECK(!answer_tx_poll(&t, 10, 0));
    CHECK(answer_tx_poll(&t, (uint32_t)(UINT32_MAX - 100 + ANSWER_RESEND_MS), 0));
    OK("test_clock_wrap");
}

static void test_ack_ttl_reaches_just_far_enough(void)
{
    CHECK(ack_ttl(0, 5) == 1);                                   /* direct: no relay */
    CHECK(ack_ttl(1, 5) == 2 && ack_ttl(4, 5) == 5);
    CHECK(ack_ttl(5, 5) == 5 && ack_ttl(200, 5) == 5);
    OK("test_ack_ttl_reaches_just_far_enough");
}

static void test_ack_frame_fits_the_mesh_budget(void)
{
    CHECK(sizeof(payload_ack_t) == 10);
    uint8_t frame[MSG_MAX_SIZE];
    payload_ack_t a = {.msg_id = 1, .device_id = 2, .seq = 3};
    int n = msg_encode(MSG_ACK, (const uint8_t *)&a, sizeof(a), frame, sizeof(frame));
    CHECK(n == (int)(MSG_OVERHEAD + sizeof(a)) && n + MESH_HDR_BYTES <= ESPNOW_MAX_DATA);
    msg_t m;
    CHECK(msg_decode(frame, (size_t)n, &m) == n && msg_verify_crc(&m) && m.type == MSG_ACK);
    OK("test_ack_frame_fits_the_mesh_budget");
}

int main(void)
{
    test_resends_then_fails();
    test_ack_delivers_and_stops_resends();
    test_ack_after_failure_is_ignored();
    test_clock_wrap();
    test_ack_ttl_reaches_just_far_enough();
    test_ack_frame_fits_the_mesh_budget();
    printf("PASS test_answer_ack\n");
    return 0;
}
