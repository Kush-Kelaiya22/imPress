/**
 * @file spi_link.h
 * @brief Acknowledged SPI slots between the hub (S3) and the gateway (C6) (#182).
 *
 * Pure C, host-tested (test_host/test_spi_link.c). Both sides used to drop a
 * slot from their send queue as soon as it was clocked; a slot that arrived
 * with a bad CRC (or while the gateway had not re-armed) was gone, with up to
 * a full slot of answers in it.
 *
 * Each side now appends an 8-byte trailer to its slot payload:
 *
 *   FF FF 5A A5 | epoch | seq | ack_epoch | ack
 *
 *   epoch      random per boot, never 0: a peer that rebooted is noticed
 *   seq        number of the data this slot carries (1..255), 0 = none
 *   ack_epoch  the epoch of the peer whose slot is acknowledged
 *   ack        the last seq received intact from that peer
 *
 * A side keeps its queued payload, re-sending it in every exchange, until the
 * peer acknowledges its seq; the receiver delivers each seq once. Old
 * firmware never sees a difference: the trailer begins with FF FF, which an
 * old gateway's record parser reads as an over-long record (ignored) and an
 * old hub's frame decoder rejects; and the gateway only adds trailers once it
 * has received one, so an old hub is never sent one. Until a side has heard
 * a trailer from its peer it keeps the old rule: drop after clocking.
 *
 * Until both sides have heard each other (the first intact exchanges after
 * boot, normally while both queues are still empty) the old rule applies, so
 * a slot corrupted in that window is still lost. Necessary to work with old
 * firmware, which never acknowledges.
 *
 * ponytail: stop-and-wait, so each data slot crosses the link twice (the ack
 * arrives one exchange later). Fine for classroom rates; a two-slot window
 * if a hub ever needs more throughput.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SPI_LINK_TRAILER   8u

typedef struct {
    bool     announce;      /* add trailers before the peer has (the hub) */
    bool     peer;          /* the peer sends trailers */
    uint8_t  epoch;         /* ours */
    uint8_t  next_seq;
    uint8_t  head_seq;      /* seq given to the queued payload, 0 = not sent yet */
    bool     sent_trailer;  /* the last slot sent carried a trailer */
    uint8_t  peer_epoch;
    uint8_t  rx_last;       /* last seq delivered from peer_epoch */
    uint32_t resent;        /* exchanges that repeated an unacknowledged payload */
    uint32_t duplicates;    /* repeats received and not delivered again */
} spi_link_t;

void spi_link_init(spi_link_t *l, uint8_t epoch, bool announce);

/** Build the payload to send: `head` (the queued payload, or NULL) followed
 *  by the trailer when this side uses trailers. @return its length, or -1 if
 *  out_size is too small. */
int spi_link_tx(spi_link_t *l, const uint8_t *head, size_t head_len, uint8_t *out, size_t out_size);

/** A payload received with a valid CRC. Strips the trailer in place.
 *  @return the length of data to deliver (0 = none, or a repeat), and sets
 *  *acked when the peer confirmed our queued payload. */
size_t spi_link_rx(spi_link_t *l, uint8_t *payload, size_t len, bool *acked);

/** After an exchange: drop the queued payload now? Only once acknowledged
 *  if the slot went out with a trailer to a peer that sends them; otherwise
 *  (an old peer, or a slot sent the old way before the peer was known) once
 *  it was clocked, as before. */
bool spi_link_drop_head(spi_link_t *l, bool sent_head, bool acked);
