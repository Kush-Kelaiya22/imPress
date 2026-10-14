/**
 * @file spi_link.c
 * @brief Acknowledged SPI slots (#182). See spi_link.h.
 */
#include "spi_link.h"

#include <string.h>

static const uint8_t MAGIC[4] = {0xFF, 0xFF, 0x5A, 0xA5};

void spi_link_init(spi_link_t *l, uint8_t epoch, bool announce)
{
    memset(l, 0, sizeof(*l));
    l->epoch = epoch ? epoch : 1;
    l->announce = announce;
    l->next_seq = 1;
}

static bool trailers(const spi_link_t *l)
{
    return l->announce || l->peer;
}

int spi_link_tx(spi_link_t *l, const uint8_t *head, size_t head_len, uint8_t *out, size_t out_size)
{
    size_t need = (head ? head_len : 0) + (trailers(l) ? SPI_LINK_TRAILER : 0);
    if (need > out_size) {
        return -1;
    }
    if (head) {
        if (l->head_seq == 0) {
            l->head_seq = l->next_seq;
            l->next_seq = (uint8_t)(l->next_seq == 255 ? 1 : l->next_seq + 1);
        } else {
            l->resent++;
        }
        memcpy(out, head, head_len);
    }
    l->sent_trailer = trailers(l);
    if (l->sent_trailer) {
        uint8_t *t = out + (head ? head_len : 0);
        memcpy(t, MAGIC, sizeof(MAGIC));
        t[4] = l->epoch;
        t[5] = head ? l->head_seq : 0;
        t[6] = l->peer_epoch;
        t[7] = l->rx_last;
    }
    return (int)need;
}

size_t spi_link_rx(spi_link_t *l, uint8_t *payload, size_t len, bool *acked)
{
    *acked = false;
    if (len < SPI_LINK_TRAILER || memcmp(payload + len - SPI_LINK_TRAILER, MAGIC, sizeof(MAGIC)) != 0) {
        return len;                                  /* no trailer: an old peer, deliver as is */
    }
    const uint8_t *t = payload + len - SPI_LINK_TRAILER;
    size_t data = len - SPI_LINK_TRAILER;
    uint8_t epoch = t[4], seq = t[5], ack_epoch = t[6], ack = t[7];
    l->peer = true;
    if (epoch != l->peer_epoch) {                    /* the peer (re)started: a new numbering */
        l->peer_epoch = epoch;
        l->rx_last = 0;
    }
    if (l->head_seq != 0 && ack_epoch == l->epoch && ack == l->head_seq) {
        *acked = true;
    }
    if (seq == 0) {
        return 0;                                    /* acknowledgement only */
    }
    if (seq == l->rx_last) {
        l->duplicates++;
        return 0;
    }
    l->rx_last = seq;
    return data;
}

bool spi_link_drop_head(spi_link_t *l, bool sent_head, bool acked)
{
    bool drop = (l->peer && l->sent_trailer) ? acked : sent_head;
    if (drop) {
        l->head_seq = 0;
    }
    return drop;
}
