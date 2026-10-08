/* Host regression test for main/spi_slave.c (C6 SPI slave slot handling).
 *
 * The fake driver below mirrors what ESP-IDF's spi_slave.c does: it keeps the
 * descriptor POINTER passed to spi_slave_queue_trans(), and when the S3 later
 * clocks the slot the ISR reads ->length / ->rx_buffer through it and writes
 * ->trans_len back into it. A descriptor that lived on the caller's stack is
 * garbage by then.
 *
 * Run from firmware/class_c6/test_host:
 *   cc -std=gnu11 -g -fsanitize=address -fsanitize-address-use-after-return=always \
 *      -Istubs -I../main -I../../protocol \
 *      test_spi_slave.c ../main/spi_slave.c ../../protocol/protocol.c -o test_spi_slave \
 *   && ./test_spi_slave
 */
#include <stdlib.h>
#include <string.h>
#include "spi_slave.h"
#include "config.h"
#include "protocol.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)

/* ── Fake FreeRTOS / GPIO ─────────────────────────────────────────── */

static int s_sem;
SemaphoreHandle_t xSemaphoreCreateBinary(void) { return &s_sem; }
SemaphoreHandle_t xSemaphoreCreateMutex(void) { return &s_sem; }
BaseType_t xSemaphoreTake(SemaphoreHandle_t s, TickType_t t) { (void)s; (void)t; return 1; }
BaseType_t xSemaphoreGive(SemaphoreHandle_t s) { (void)s; return 1; }
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t s, BaseType_t *w) { (void)s; (void)w; return 1; }
esp_err_t gpio_config(const gpio_config_t *c) { (void)c; return ESP_OK; }
static int s_ready_c6 = -1;  /* last level driven on PIN_READY_C6_TO_S3 */
esp_err_t gpio_set_level(gpio_num_t p, uint32_t l) { if (p == PIN_READY_C6_TO_S3) s_ready_c6 = (int)l; return ESP_OK; }

/* ── Fake SPI slave driver (pointer-retaining, like ESP-IDF) ─────── */

static spi_slave_interface_config_t s_cfg;
static const spi_slave_transaction_t *s_queued[8];
static int s_nqueued;                       /* trans_queue depth */
static spi_slave_transaction_t *s_done[8];
static int s_ndone;                         /* ret_queue depth */

esp_err_t spi_slave_initialize(spi_host_device_t h, const spi_bus_config_t *b,
                               const spi_slave_interface_config_t *c, int dma)
{
    (void)h; (void)b; (void)dma;
    s_cfg = *c;
    return ESP_OK;
}

esp_err_t spi_slave_queue_trans(spi_host_device_t h, const spi_slave_transaction_t *t,
                                TickType_t wait)
{
    (void)h;
    if (s_nqueued == s_cfg.queue_size) {
        printf("FAIL: trans_queue full; with wait=%s spi2http would block until the S3 clocks\n",
               wait == portMAX_DELAY ? "portMAX_DELAY" : "finite");
        exit(1);
    }
    s_queued[s_nqueued++] = t;
    return ESP_OK;
}

esp_err_t spi_slave_get_trans_result(spi_host_device_t h, spi_slave_transaction_t **t,
                                     TickType_t wait)
{
    (void)h; (void)wait;
    if (s_ndone == 0) return ESP_ERR_TIMEOUT;
    *t = s_done[0];
    memmove(s_done, s_done + 1, --s_ndone * sizeof s_done[0]);
    return ESP_OK;
}

/* The S3 clocks one 4096-byte slot: what spi_intr() does with the next descriptor.
 * miso (optional) receives the slot the C6 presented. */
static uint8_t s_miso[SPI_SLOT_BYTES];
static void s3_clocks(const uint8_t *mosi, size_t n)
{
    CHECK(s_nqueued > 0);
    spi_slave_transaction_t *t = (spi_slave_transaction_t *)s_queued[0];
    memmove(s_queued, s_queued + 1, --s_nqueued * sizeof s_queued[0]);

    CHECK(t->length == SPI_SLOT_BYTES * 8);  /* descriptor must still be intact */
    CHECK(t->rx_buffer && t->tx_buffer);
    if (s_cfg.post_setup_cb) s_cfg.post_setup_cb(t);
    memcpy(s_miso, t->tx_buffer, SPI_SLOT_BYTES);
    memset(t->rx_buffer, 0, SPI_SLOT_BYTES);
    memcpy(t->rx_buffer, mosi, n);
    t->trans_len = t->length;                /* driver writes back into the descriptor */
    s_cfg.post_trans_cb(t);
    if (s_ndone < s_cfg.queue_size) s_done[s_ndone++] = t;
}

/* ── Helpers ──────────────────────────────────────────────────────── */

static size_t make_slot(uint8_t *slot, const char *payload)
{
    size_t len = strlen(payload);
    slot[0] = len >> 8;
    slot[1] = len & 0xFF;
    memcpy(slot + 2, payload, len);
    uint16_t crc = crc16_ccitt(slot + 2, len);
    slot[2 + len] = crc >> 8;
    slot[3 + len] = crc & 0xFF;
    return len + 4;
}

/* Reuse the stack region a returned queue_slot() frame occupied. */
static void __attribute__((noinline)) clobber_stack(void)
{
    volatile uint8_t junk[8192];
    memset((void *)junk, 0xA5, sizeof junk);
}

int main(void)
{
    uint8_t slot[64], buf[SPI_SLOT_BYTES];

    CHECK(spi_slave_init() == 0);
    CHECK(s_nqueued == 1);

    /* spi2http polls every 50 ms while the S3 is idle: no slots may pile up. */
    for (int i = 0; i < 10; i++) {
        CHECK(spi_slave_read(buf, sizeof buf) == 0);
    }
    CHECK(s_nqueued == 1);

    /* Caller stack is reused before the S3 finally clocks the armed slot. */
    clobber_stack();
    s3_clocks(slot, make_slot(slot, "hello"));
    CHECK(spi_slave_read(buf, sizeof buf) == 5);
    CHECK(memcmp(buf, "hello", 5) == 0);
    CHECK(s_nqueued == 1);  /* re-armed exactly once */

    /* A second exchange works the same way. */
    clobber_stack();
    s3_clocks(slot, make_slot(slot, "world!"));
    CHECK(spi_slave_read(buf, sizeof buf) == 6);
    CHECK(memcmp(buf, "world!", 6) == 0);
    CHECK(s_nqueued == 1);

    CHECK(s_cfg.queue_size == 1);   /* one armed slot, never more */

    /* ── C6 -> S3: back-to-back frames all arrive, in order ────────── */
    CHECK(spi_slave_send((const uint8_t *)"A1", 2) == 0);
    CHECK(spi_slave_send((const uint8_t *)"B22", 3) == 0);
    CHECK(spi_slave_send((const uint8_t *)"C333", 4) == 0);
    CHECK(s_ready_c6 == 1);
    uint8_t got[SPI_SLOT_BYTES];
    const char *expect[] = {NULL /* slot armed before the sends */, "A1", "B22", "C333", NULL};
    for (int i = 0; i < 5; i++) {
        s3_clocks(NULL, 0);
        int glen = spi_slot_decode(s_miso, got, sizeof got);
        if (expect[i]) {
            CHECK(glen == (int)strlen(expect[i]) && memcmp(got, expect[i], glen) == 0);
        } else {
            CHECK(glen == 0);
        }
        CHECK(spi_slave_read(buf, sizeof buf) == 0);   /* S3 sent nothing */
        CHECK(s_nqueued == 1);
    }
    CHECK(s_ready_c6 == 0);   /* FIFO drained */

    /* ── Corrupted S3 slot: rejected (CRC), slot still re-armed ────── */
    size_t sl = make_slot(slot, "corrupt-me");
    slot[5] ^= 0x10;
    s3_clocks(slot, sl);
    CHECK(spi_slave_read(buf, sizeof buf) == 0);
    CHECK(s_nqueued == 1);
    s3_clocks(slot, make_slot(slot, "fine"));      /* link recovers next slot */
    CHECK(spi_slave_read(buf, sizeof buf) == 4 && memcmp(buf, "fine", 4) == 0);

    /* ── FIFO full: the 9th queued frame is refused, earlier ones kept ─ */
    for (int i = 0; i < SPI_SLOT_FIFO_DEPTH; i++) CHECK(spi_slave_send((const uint8_t *)"x", 1) == 0);
    CHECK(spi_slave_send((const uint8_t *)"y", 1) != 0);
    CHECK(spi_slave_send(buf, SPI_SLOT_PAYLOAD_MAX + 1) == SPI_SLOT_ERR_LEN);

    puts("PASS test_spi_slave");
    return 0;
}
