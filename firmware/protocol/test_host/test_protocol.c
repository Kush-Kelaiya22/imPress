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

/* Reference CRC-16 (poly 0x1021, init 0xFFFF), written out independently, to
 * prove crc16_ccitt matches the local copies the v3 drivers carried. */
static uint16_t crc_ref(const uint8_t *d, size_t n)
{
    uint16_t c = 0xFFFF;
    while (n--) {
        c ^= (uint16_t)(*d++ << 8);
        for (int b = 0; b < 8; b++) c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1);
    }
    return c;
}

static void test_crc_matches_reference(void)
{
    static const uint8_t check[] = "123456789";
    CHECK(crc16_ccitt(check, 9) == 0x29B1);            /* CRC-16/CCITT-FALSE check value */
    uint8_t buf[300];
    for (size_t i = 0; i < sizeof buf; i++) buf[i] = (uint8_t)(i * 37 + 11);
    for (size_t n = 0; n <= sizeof buf; n += 17) CHECK(crc16_ccitt(buf, n) == crc_ref(buf, n));
}

static void test_slot_roundtrip_and_golden_layout(void)
{
    static uint8_t slot[SPI_SLOT_BYTES], out[SPI_SLOT_BYTES];
    const uint8_t p[] = {0xAA, 0x01, 0x00, 0x02, 0x10, 0x20};
    CHECK(spi_slot_encode(slot, p, sizeof p) == 0);
    CHECK(slot[0] == 0x00 && slot[1] == sizeof p);              /* LEN big-endian */
    CHECK(memcmp(slot + 2, p, sizeof p) == 0);
    uint16_t crc = crc16_ccitt(p, sizeof p);
    CHECK(slot[2 + sizeof p] == (crc >> 8) && slot[3 + sizeof p] == (crc & 0xFF));
    for (size_t i = 4 + sizeof p; i < SPI_SLOT_BYTES; i++) CHECK(slot[i] == 0);  /* zero padding */
    CHECK(spi_slot_decode(slot, out, sizeof out) == (int)sizeof p);
    CHECK(memcmp(out, p, sizeof p) == 0);
}

static void test_slot_empty_full_and_errors(void)
{
    static uint8_t slot[SPI_SLOT_BYTES], out[SPI_SLOT_BYTES], big[SPI_SLOT_BYTES];
    memset(big, 0x5A, sizeof big);
    CHECK(spi_slot_encode(slot, NULL, 0) == 0);                 /* empty = all zero */
    for (size_t i = 0; i < SPI_SLOT_BYTES; i++) CHECK(slot[i] == 0);
    CHECK(spi_slot_decode(slot, out, sizeof out) == 0);

    CHECK(spi_slot_encode(slot, big, SPI_SLOT_PAYLOAD_MAX) == 0);   /* exactly fits */
    CHECK(spi_slot_decode(slot, out, sizeof out) == SPI_SLOT_PAYLOAD_MAX);
    CHECK(spi_slot_encode(slot, big, SPI_SLOT_PAYLOAD_MAX + 1) == SPI_SLOT_ERR_LEN);

    CHECK(spi_slot_encode(slot, big, 100) == 0);
    slot[50] ^= 0x01;                                           /* one flipped bit */
    CHECK(spi_slot_decode(slot, out, sizeof out) == SPI_SLOT_ERR_CRC);
    slot[50] ^= 0x01;
    CHECK(spi_slot_decode(slot, out, 99) == SPI_SLOT_ERR_SPACE); /* never a partial copy */
    slot[0] = 0xFF; slot[1] = 0xFF;                             /* garbage LEN */
    CHECK(spi_slot_decode(slot, out, sizeof out) == SPI_SLOT_ERR_LEN);
}

static spi_slot_fifo_t g_fifo;   /* 32 KB: static, like the drivers */

static void test_slot_fifo_order_and_overflow(void)
{
    static uint8_t slot[SPI_SLOT_BYTES], out[SPI_SLOT_BYTES];
    spi_slot_fifo_init(&g_fifo);
    CHECK(!spi_slot_fifo_peek(&g_fifo, slot));                  /* empty → zero slot */
    CHECK(spi_slot_decode(slot, out, sizeof out) == 0);

    /* back-to-back frames all survive, in order (the v2 latest-wins bug) */
    for (int i = 0; i < SPI_SLOT_FIFO_DEPTH; i++) {
        uint8_t b = (uint8_t)(0x40 + i);
        CHECK(spi_slot_fifo_push(&g_fifo, &b, 1) == 0);
    }
    uint8_t extra = 0xEE;
    CHECK(spi_slot_fifo_push(&g_fifo, &extra, 1) == -4);        /* full: refused, counted */
    CHECK(g_fifo.dropped == 1 && spi_slot_fifo_count(&g_fifo) == SPI_SLOT_FIFO_DEPTH);

    for (int i = 0; i < SPI_SLOT_FIFO_DEPTH; i++) {
        CHECK(spi_slot_fifo_peek(&g_fifo, slot));
        CHECK(spi_slot_fifo_peek(&g_fifo, slot));               /* peek doesn't consume */
        CHECK(spi_slot_decode(slot, out, sizeof out) == 1 && out[0] == 0x40 + i);
        spi_slot_fifo_drop(&g_fifo);
    }
    CHECK(spi_slot_fifo_count(&g_fifo) == 0);
    spi_slot_fifo_drop(&g_fifo);                                /* drop on empty is a no-op */
    CHECK(spi_slot_fifo_count(&g_fifo) == 0);

    /* wrap-around keeps order */
    for (int round = 0; round < 3; round++) {
        for (int i = 0; i < 5; i++) { uint8_t b = (uint8_t)(round * 10 + i); CHECK(spi_slot_fifo_push(&g_fifo, &b, 1) == 0); }
        for (int i = 0; i < 5; i++) {
            CHECK(spi_slot_fifo_peek(&g_fifo, slot) && spi_slot_decode(slot, out, sizeof out) == 1);
            CHECK(out[0] == round * 10 + i);
            spi_slot_fifo_drop(&g_fifo);
        }
    }
    CHECK(spi_slot_fifo_push(&g_fifo, &extra, SPI_SLOT_PAYLOAD_MAX + 1) == SPI_SLOT_ERR_LEN);
    CHECK(spi_slot_fifo_count(&g_fifo) == 0);
}

static void test_json_get_string(void)
{
    char out[48];
    const char *reg = "{\"device_id\":3,\"status\":\"registered\",\"class_id\":null,"
                      "\"device_key\":\"AbC-12_xyz\"}";
    CHECK(json_get_string(reg, "device_key", out, sizeof out) == 10 && strcmp(out, "AbC-12_xyz") == 0);
    CHECK(json_get_string(reg, "status", out, sizeof out) == 10 && strcmp(out, "registered") == 0);
    CHECK(json_get_string(reg, "missing", out, sizeof out) == -1 && out[0] == '\0');
    CHECK(json_get_string(reg, "class_id", out, sizeof out) == -1);          /* null is not a string */
    CHECK(json_get_string(reg, "device_id", out, sizeof out) == -1);         /* number */
    /* the key's name appearing as a value is not the key */
    CHECK(json_get_string("{\"a\":\"device_key\",\"device_key\" : \"K\"}", "device_key", out, sizeof out) == 1
          && strcmp(out, "K") == 0);
    CHECK(json_get_string("{\"device_keys\":\"no\"}", "device_key", out, sizeof out) == -1);   /* prefix only */
    char small[4];
    CHECK(json_get_string("{\"k\":\"abcd\"}", "k", small, sizeof small) == -1 && small[0] == '\0');   /* too long */
    CHECK(json_get_string("{\"k\":\"abc\"}", "k", small, sizeof small) == 3);
    CHECK(json_get_string("{\"k\":\"a\\\"b\"}", "k", out, sizeof out) == -1);   /* escapes refused */
    CHECK(json_get_string("{\"k\":\"abc", "k", out, sizeof out) == -1 && out[0] == '\0');   /* unterminated */
    CHECK(json_get_string("{\"k\":\"\"}", "k", out, sizeof out) == 0);
    CHECK(json_get_string(NULL, "k", out, sizeof out) == -1);
}

int main(void)
{
    RUN(test_frame_roundtrip);
    RUN(test_frame_limits);
    RUN(test_record_golden_bytes);
    RUN(test_record_single);
    RUN(test_record_batch_fills_slot);
    RUN(test_record_truncated_and_edges);
    RUN(test_crc_matches_reference);
    RUN(test_slot_roundtrip_and_golden_layout);
    RUN(test_slot_empty_full_and_errors);
    RUN(test_slot_fifo_order_and_overflow);
    RUN(test_json_get_string);
    puts("PASS test_protocol");
    return 0;
}
