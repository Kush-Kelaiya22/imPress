/**
 * @file ota_chunk.c
 * @brief Student-module OTA chunking and reassembly (#130). See ota_chunk.h.
 */
#include "ota_chunk.h"

#include <string.h>

uint16_t ota_chunk_count(uint32_t size)
{
    return (uint16_t)((size + OTA_CHUNK_BYTES - 1) / OTA_CHUNK_BYTES);
}

uint8_t ota_chunk_len(uint32_t size, uint16_t seq)
{
    uint32_t start = (uint32_t)seq * OTA_CHUNK_BYTES;
    if (start >= size) return 0;
    uint32_t left = size - start;
    return (uint8_t)(left < OTA_CHUNK_BYTES ? left : OTA_CHUNK_BYTES);
}

static bool has(const ota_rx_t *rx, uint16_t seq)
{
    return (rx->bitmap[seq / 8] >> (seq % 8)) & 1u;
}

static void advance(ota_rx_t *rx)
{
    while (rx->next_missing < rx->total && has(rx, rx->next_missing)) rx->next_missing++;
}

int ota_rx_init(ota_rx_t *rx, uint16_t session, uint32_t size, uint32_t slot_bytes)
{
    memset(rx, 0, sizeof(*rx));
    if (size == 0 || size > slot_bytes || (size + OTA_CHUNK_BYTES - 1) / OTA_CHUNK_BYTES > OTA_MAX_CHUNKS) {
        return -1;
    }
    rx->session = session;
    rx->size = size;
    rx->total = ota_chunk_count(size);
    return 0;
}

void ota_rx_resume(ota_rx_t *rx, uint16_t contiguous)
{
    if (contiguous > rx->total) contiguous = rx->total;
    for (uint16_t s = 0; s < contiguous; s++) {
        if (!has(rx, s)) {
            rx->bitmap[s / 8] |= (uint8_t)(1u << (s % 8));
            rx->received++;
        }
    }
    advance(rx);
}

ota_rx_result_t ota_rx_accept(ota_rx_t *rx, const ota_chunk_hdr_t *hdr, uint32_t *offset)
{
    if (hdr->session != rx->session) return OTA_RX_WRONG_SESSION;
    if (hdr->seq >= rx->total) return OTA_RX_BAD_SEQ;
    if (hdr->len == 0 || hdr->len != ota_chunk_len(rx->size, hdr->seq)) return OTA_RX_BAD_LEN;
    if (has(rx, hdr->seq)) return OTA_RX_DUPLICATE;
    rx->bitmap[hdr->seq / 8] |= (uint8_t)(1u << (hdr->seq % 8));
    rx->received++;
    advance(rx);
    *offset = (uint32_t)hdr->seq * OTA_CHUNK_BYTES;
    return OTA_RX_NEW;
}

void ota_rx_status(const ota_rx_t *rx, ota_status_t *out)
{
    out->session = rx->session;
    out->next_missing = rx->next_missing;
    out->window = 0;
    for (uint32_t i = 0; i < OTA_WINDOW; i++) {
        uint32_t seq = (uint32_t)rx->next_missing + i;
        if (seq < rx->total && has(rx, (uint16_t)seq)) out->window |= (uint64_t)1 << i;
    }
}

bool ota_rx_complete(const ota_rx_t *rx)
{
    return rx->total > 0 && rx->received == rx->total;
}

size_t ota_tx_wanted(const ota_status_t *st, uint16_t total, uint16_t *out, size_t max)
{
    size_t n = 0;
    for (uint32_t i = 0; i < OTA_WINDOW && n < max; i++) {
        uint32_t seq = (uint32_t)st->next_missing + i;
        if (seq >= total) break;
        if (!((st->window >> i) & 1u)) out[n++] = (uint16_t)seq;
    }
    return n;
}

ota_decline_t ota_should_accept(bool session_live, uint8_t battery_pct, uint8_t min_battery_pct,
                                bool same_version, uint32_t size, uint32_t slot_bytes, bool authorised)
{
    if (session_live) return OTA_BUSY_SESSION;              /* answers and votes come first */
    if (!authorised) return OTA_NOT_AUTHORISED;
    if (battery_pct < min_battery_pct) return OTA_LOW_BATTERY;
    if (same_version) return OTA_SAME_VERSION;
    if (size == 0 || size > slot_bytes) return OTA_TOO_LARGE;
    return OTA_OK;
}
