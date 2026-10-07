/* Host tests for firmware/protocol (frame codec + S3→C6 SPI batch record).
 * Run: ./run.sh   (plain cc, no ESP-IDF) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "protocol.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define RUN(t) do { t(); printf("ok   %s\n", #t); } while (0)

static int frame_vote(uint8_t *out, uint16_t poll_id)
{
    payload_poll_vote_t v = { .poll_id = poll_id, .selected_option = 2, .enrollment = "ABCDE12345" };
    return msg_encode(MSG_POLL_VOTE, (const uint8_t *)&v, sizeof v, out, MSG_MAX_SIZE);
}

static void test_frame_roundtrip(void)
{
    uint8_t buf[MSG_MAX_SIZE];
    int n = frame_vote(buf, 7);
    CHECK(n == MSG_OVERHEAD + (int)sizeof(payload_poll_vote_t));
    msg_t m;
    CHECK(msg_decode(buf, n, &m) == n);
    CHECK(m.type == MSG_POLL_VOTE && msg_verify_crc(&m));
    CHECK(((payload_poll_vote_t *)m.payload)->poll_id == 7);
    buf[5] ^= 0xFF;                              /* corrupt payload */
    CHECK(msg_decode(buf, n, &m) == n && !msg_verify_crc(&m));
}

static void test_frame_limits(void)
{
    uint8_t p[MSG_MAX_PAYLOAD + 1] = {0}, out[MSG_MAX_SIZE + 8];
    CHECK(msg_encode(MSG_ACK, p, MSG_MAX_PAYLOAD, out, sizeof out) == MSG_MAX_SIZE);
    CHECK(msg_encode(MSG_ACK, p, MSG_MAX_PAYLOAD + 1, out, sizeof out) == -1);
    msg_t m;
    CHECK(msg_decode(out, MSG_MAX_SIZE - 1, &m) == 0);   /* incomplete */
}

/* Wire layout is pinned byte-for-byte: [len BE][id LE][frame]. */
static void test_record_golden_bytes(void)
{
    const uint8_t frame[3] = { 0xAA, 0xBB, 0xCC };
    uint8_t out[16];
    CHECK(spi_record_write(out, sizeof out, 0x11223344, frame, 3) == 9);
    const uint8_t want[9] = { 0x00, 0x03, 0x44, 0x33, 0x22, 0x11, 0xAA, 0xBB, 0xCC };
    CHECK(memcmp(out, want, 9) == 0);
}

/* Regression for #2: a single record must be parsed (was 0 of 1). */
static void test_record_single(void)
{
    uint8_t frame[MSG_MAX_SIZE], slot[4092];
    int fl = frame_vote(frame, 7);
    int n = spi_record_write(slot, sizeof slot, 0xD53FC8B1, frame, fl);
    uint32_t id; const uint8_t *f; uint16_t flen;
    CHECK(spi_record_read(slot, n, &id, &f, &flen) == n);
    CHECK(id == 0xD53FC8B1 && flen == fl);
    msg_t m;
    CHECK(msg_decode(f, flen, &m) == fl && msg_verify_crc(&m));
}

/* Regression for #2: every record in a batch must be parsed (was 1 of 3). */
static void test_record_batch_fills_slot(void)
{
    uint8_t frame[MSG_MAX_SIZE], slot[4092];
    int fl = frame_vote(frame, 1);
    int total = 0, written = 0;
    for (;;) {                                   /* fill like mesh_master_flush_to_spi */
        int n = spi_record_write(slot + total, sizeof slot - total, 1000 + written, frame, fl);
        if (n < 0) break;
        total += n; written++;
    }
    CHECK(written == (int)(sizeof slot / (SPI_RECORD_HEADER_SIZE + fl)));
    int off = 0, parsed = 0;
    for (;;) {                                   /* consume like process_spi_payload */
        uint32_t id; const uint8_t *f; uint16_t flen; msg_t m;
        int n = spi_record_read(slot + off, total - off, &id, &f, &flen);
        if (n <= 0) break;
        off += n;
        CHECK(id == (uint32_t)(1000 + parsed));
        CHECK(msg_decode(f, flen, &m) == fl && m.type == MSG_POLL_VOTE);
        parsed++;
    }
    CHECK(parsed == written && off == total);
}

static void test_record_truncated_and_edges(void)
{
    uint8_t frame[4] = {1, 2, 3, 4}, out[16];
    int n = spi_record_write(out, sizeof out, 5, frame, 4);
    for (int cut = 0; cut < n; cut++) {
        CHECK(spi_record_read(out, cut, NULL, NULL, NULL) == 0);  /* never over-reads */
    }
    CHECK(spi_record_write(out, 9, 5, frame, 4) == -1);           /* doesn't fit */
    CHECK(spi_record_write(out, sizeof out, 5, NULL, 0) == SPI_RECORD_HEADER_SIZE);
    uint8_t zeros[64] = {0};                                       /* empty slot */
    uint16_t fl = 99;
    CHECK(spi_record_read(zeros, sizeof zeros, NULL, NULL, &fl) == SPI_RECORD_HEADER_SIZE && fl == 0);
}

int main(void)
{
    RUN(test_frame_roundtrip);
    RUN(test_frame_limits);
    RUN(test_record_golden_bytes);
    RUN(test_record_single);
    RUN(test_record_batch_fills_slot);
    RUN(test_record_truncated_and_edges);
    puts("PASS test_protocol");
    return 0;
}
