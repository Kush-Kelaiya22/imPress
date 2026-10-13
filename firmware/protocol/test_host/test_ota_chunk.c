/* Host tests for ota_chunk.c (#130): a simulated lossy ESP-NOW link. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ota_chunk.h"

#define SLOT (0x1C0000u)                 /* the student OTA slot */

static uint32_t rng = 12345;
static uint32_t rnd(void) { rng = rng * 1103515245u + 12345u; return (rng >> 8) & 0xFFFFFFu; }

/* Hub sends the wanted chunks; the radio drops `loss_pct` %, duplicates 5 %,
 * and reorders each burst. Returns the rounds (status reports) needed. */
static int transfer(const uint8_t *img, uint32_t size, uint8_t *flash, ota_rx_t *rx, int loss_pct, int max_rounds)
{
    uint16_t total = ota_chunk_count(size), wanted[OTA_WINDOW];
    for (int round = 1; round <= max_rounds; round++) {
        ota_status_t st;
        ota_rx_status(rx, &st);
        if (ota_rx_complete(rx)) return round - 1;
        size_t n = ota_tx_wanted(&st, total, wanted, OTA_WINDOW);
        assert(n > 0);                                           /* incomplete ⇒ something is wanted */
        for (size_t i = n; i > 1; i--) {                          /* reorder the burst */
            size_t j = rnd() % i; uint16_t t = wanted[i - 1]; wanted[i - 1] = wanted[j]; wanted[j] = t;
        }
        for (size_t i = 0; i < n; i++) {
            for (int copy = 0; copy < ((rnd() % 100) < 5 ? 2 : 1); copy++) {
                if ((int)(rnd() % 100) < loss_pct) continue;     /* lost on the air */
                ota_chunk_hdr_t h = { rx->session, wanted[i], ota_chunk_len(size, wanted[i]) };
                uint32_t off;
                ota_rx_result_t r = ota_rx_accept(rx, &h, &off);
                assert(r == OTA_RX_NEW || r == OTA_RX_DUPLICATE);
                if (r == OTA_RX_NEW) memcpy(flash + off, img + off, h.len);
            }
        }
    }
    return -1;
}

static void test_lossy_links_deliver_every_byte(void)
{
    uint32_t sizes[] = { 1, 191, 192, 193, 1000003, SLOT };
    int losses[] = { 0, 10, 30 };
    for (size_t s = 0; s < sizeof sizes / sizeof *sizes; s++) {
        uint8_t *img = malloc(sizes[s]), *flash = calloc(1, sizes[s]);
        for (uint32_t i = 0; i < sizes[s]; i++) img[i] = (uint8_t)(rnd() & 0xFF);
        for (size_t l = 0; l < sizeof losses / sizeof *losses; l++) {
            static ota_rx_t rx;
            memset(flash, 0, sizes[s]);
            assert(ota_rx_init(&rx, 7, sizes[s], SLOT) == 0);
            int rounds = transfer(img, sizes[s], flash, &rx, losses[l], 100000);
            assert(rounds >= 0 && ota_rx_complete(&rx));
            assert(memcmp(img, flash, sizes[s]) == 0);
            if (sizes[s] == SLOT) printf("  %u bytes, %d%% loss: %d status rounds\n", sizes[s], losses[l], rounds);
        }
        free(img); free(flash);
    }
}

static void test_interrupted_transfer_resumes(void)
{
    uint32_t size = 500000;
    uint8_t *img = malloc(size), *flash = calloc(1, size);
    for (uint32_t i = 0; i < size; i++) img[i] = (uint8_t)i;
    static ota_rx_t rx;
    assert(ota_rx_init(&rx, 9, size, SLOT) == 0);
    transfer(img, size, flash, &rx, 20, 20);                     /* power cut part-way */
    assert(!ota_rx_complete(&rx));
    uint16_t contiguous = rx.next_missing;                         /* what the module keeps in NVS */
    assert(contiguous > 0);
    assert(ota_rx_init(&rx, 9, size, SLOT) == 0);                  /* reboot: bitmap lost */
    ota_rx_resume(&rx, contiguous);
    ota_status_t st; ota_rx_status(&rx, &st);
    assert(st.next_missing == contiguous);                         /* asks from where it stopped */
    assert(transfer(img, size, flash, &rx, 20, 100000) >= 0);
    assert(memcmp(img, flash, size) == 0);
    free(img); free(flash);
}

static void test_bad_chunks_are_refused(void)
{
    static ota_rx_t rx;
    uint32_t off;
    assert(ota_rx_init(&rx, 3, 1000, SLOT) == 0);                  /* 6 chunks, last one 40 bytes */
    ota_chunk_hdr_t wrong_session = { 4, 0, 192 }, beyond = { 3, 6, 192 }, short_len = { 3, 0, 100 },
                    last_wrong = { 3, 5, 192 }, last_ok = { 3, 5, 40 }, zero = { 3, 1, 0 };
    assert(ota_rx_accept(&rx, &wrong_session, &off) == OTA_RX_WRONG_SESSION);
    assert(ota_rx_accept(&rx, &beyond, &off) == OTA_RX_BAD_SEQ);
    assert(ota_rx_accept(&rx, &short_len, &off) == OTA_RX_BAD_LEN);
    assert(ota_rx_accept(&rx, &last_wrong, &off) == OTA_RX_BAD_LEN);
    assert(ota_rx_accept(&rx, &zero, &off) == OTA_RX_BAD_LEN);
    assert(ota_rx_accept(&rx, &last_ok, &off) == OTA_RX_NEW && off == 960);
    assert(ota_rx_accept(&rx, &last_ok, &off) == OTA_RX_DUPLICATE);
    assert(rx.received == 1 && rx.next_missing == 0);
}

static void test_sizes_and_limits(void)
{
    static ota_rx_t rx;
    assert(ota_rx_init(&rx, 1, 0, SLOT) == -1);
    assert(ota_rx_init(&rx, 1, SLOT + 1, SLOT) == -1);
    assert(ota_rx_init(&rx, 1, (uint32_t)OTA_MAX_CHUNKS * OTA_CHUNK_BYTES + 1, 0xFFFFFFFFu) == -1);
    assert(ota_chunk_count(SLOT) == 9558 && ota_chunk_len(SLOT, 9557) == SLOT - 9557u * 192u);
    /* on air: 6-byte mesh routing header + 6-byte frame overhead + payload <= 250 (ESP-NOW v1) */
    assert(6 + 6 + sizeof(ota_chunk_hdr_t) + OTA_CHUNK_BYTES <= 250);
}

static void test_when_a_module_may_update(void)
{
    assert(ota_should_accept(true, 90, 40, false, 1000, SLOT, true) == OTA_BUSY_SESSION);
    assert(ota_should_accept(false, 90, 40, false, 1000, SLOT, false) == OTA_NOT_AUTHORISED);
    assert(ota_should_accept(false, 30, 40, false, 1000, SLOT, true) == OTA_LOW_BATTERY);
    assert(ota_should_accept(false, 90, 40, true, 1000, SLOT, true) == OTA_SAME_VERSION);
    assert(ota_should_accept(false, 90, 40, false, SLOT + 1, SLOT, true) == OTA_TOO_LARGE);
    assert(ota_should_accept(false, 90, 40, false, 1000, SLOT, true) == OTA_OK);
}

int main(void)
{
    test_lossy_links_deliver_every_byte();
    test_interrupted_transfer_resumes();
    test_bad_chunks_are_refused();
    test_sizes_and_limits();
    test_when_a_module_may_update();
    puts("PASS test_ota_chunk");
    return 0;
}
