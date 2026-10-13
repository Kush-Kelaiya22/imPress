# Student module OTA over ESP-NOW (design)

Status: **design and host-tested core** (#130). The core (`firmware/protocol/ota_chunk.c`) is implemented and tested on a simulated lossy link; the hub and module firmware that use it, and the backend targeting, are the next steps below. Nothing here has run on hardware yet.

## Why it is different from gateway and hub OTA

| | Gateway (C6), hub (S3) | Student module (ESP32) |
|---|---|---|
| Network to the server | Wi-Fi (the hub joins Wi-Fi only for the update) | none: ESP-NOW to the hub only |
| Payload per frame | HTTP | 250 bytes on air (ESP-NOW v1) = 6-byte mesh routing header + 6-byte frame overhead + **at most 238 bytes** of message payload |
| Many devices at once | one per room | 30–300 per room on one radio channel |
| Rollback | bootloader rollback enabled | **disabled** in the current bootloader (`firmware/student/sdkconfig`); it can only be enabled by one serial flash of the bootloader |
| Must not disturb | the class (maintenance windows, #128) | quizzes and polls: answers have priority on the air |

## Constraints that shape the design

1. **ESP-NOW frames are small and unacknowledged at the application level.** The image (up to the 1.75 MB slot) travels in **192-byte chunks** (5-byte chunk header + 192 = 197-byte payload, 209 bytes on air): 9,558 chunks for a full slot.
2. **Loss, duplicates and reordering happen** (multi-hop relay, interference). The receiver keeps a bitmap of chunks it has (1.2 KB of RAM for a full slot) and reports what it misses; the hub resends only those (**selective repeat**, window of 64 chunks).
3. **Power can fail mid-transfer.** Chunks are written straight into the inactive OTA partition at their offset; the module keeps the highest *contiguous* chunk count in NVS every 64 chunks. After a reboot it resumes from there: at most 64 chunks are re-sent.
4. **The image must be verified before it can boot.** After the last chunk the module computes SHA-256 over the partition and compares it with the offer, then `esp_ota_end()` validates the image header, chip and segments (the same checks the TrustedInstaller's analysis runs, #154). Only then `esp_ota_set_boot_partition()`.
5. **No rollback on current modules.** A bad image that passes verification but misbehaves cannot be undone automatically until the bootloader is re-flashed once over USB with rollback enabled. Until then: the TrustedInstaller qualification (#154), a canary of **one** module per room, and the documented USB recovery (flash the release's full image, #155).
6. **Quizzes come first.** A module accepts an offer only when no quiz or poll is live on it, the classroom has authorised a maintenance period, its battery is above the minimum (flash writes draw current; a brown-out mid-write is avoided), the version differs, and the image fits its slot (`ota_should_accept`).

## Messages (new mesh types)

| Type | Direction | Payload | Purpose |
|---|---|---|---|
| `MSG_OTA_OFFER` 0x60 | hub → module | session u16, size u32, chunks u16, version[16], sha256[32] | announce an image |
| `MSG_OTA_READY` 0x61 | module → hub | session u16, decision u8 (`ota_decline_t`), resume_from u16 | accept (with the resume point) or decline with the reason |
| `MSG_OTA_CHUNK` 0x62 | hub → module | `ota_chunk_hdr_t` (session, seq, len) + data | one chunk |
| `MSG_OTA_STATUS` 0x63 | module → hub | `ota_status_t` (session, next_missing, 64-bit window) | progress; the hub resends `ota_tx_wanted()` |
| `MSG_OTA_DONE` 0x64 | module → hub | session u16, result u8, running version[16] | verified and installed, or why not; after reboot the version it runs |

Every message is a normal mesh frame (start byte, type, length, CRC16), so corrupted frames are already dropped by the existing protocol code.

## Sequence

```{mermaid}
sequenceDiagram
    participant S as Server
    participant G as Gateway (C6)
    participant H as Hub (S3)
    participant M as Student module
    S->>G: deployment (TrustedInstaller-qualified image, maintenance window open)
    G->>H: fetch image over Wi-Fi hop (existing hub OTA path), keep it in hub flash
    H->>M: MSG_OTA_OFFER
    M->>H: MSG_OTA_READY (accept, resume_from) or decline reason
    loop until complete
        H->>M: MSG_OTA_CHUNK x up to 64 (missing ones only)
        M->>H: MSG_OTA_STATUS (next_missing, window)
    end
    M->>M: SHA-256 over partition, esp_ota_end, set boot partition, restart
    M->>H: MSG_OTA_DONE (version after reboot)
    H->>G: result
    G->>S: deployment target success / failed
```

## Concurrency and airtime

- The hub serves **one module at a time per room by default** (configurable 1–4). The core's measured round counts on a simulated link for a full 1.75 MB slot (64 chunks per round): **150 rounds** without loss, **319** at 10 % loss, **513** at 30 % loss (`run_ota_chunk.sh`). Real throughput and time per module must be measured on hardware (#164 follow-up); do not assume a figure.
- Between rounds the hub yields the channel: any quiz/poll frame preempts OTA traffic; when a session starts, OTA pauses (`OTA_BUSY_SESSION`) and resumes after.

## Server side (next step)

- Remove the `student` exclusion in `deployments.exclusion_reason` once the hub and module firmware ship this; student targets are offered through their room's hub and follow the room's maintenance window (#128).
- The deployment state machine stays the same; the hub reports `downloading` (first chunk), `verifying`, `installing`, `rebooting`, `success`/`failed` per module.
- The TrustedInstaller's qualification (#154) already covers student images (analysis, emulator boot test in CI).

## Test plan

| Level | What | Status |
|---|---|---|
| Host | chunking, reassembly, duplicates, reordering, 0/10/30 % loss, resume after a reboot, malformed chunks, slot limits, accept/decline rules (`firmware/protocol/test_host/test_ota_chunk.c`, ASan/UBSan) | **done** |
| Emulator | module firmware boots after an OTA-written partition (QEMU, #154) | next step |
| Hardware | 1 module, then 5, then a full room; loss by distance; power cut mid-transfer; battery threshold; a quiz starting mid-transfer | to do, needs boards |

## Open questions for review

1. Minimum battery for a flash write (proposed 40 %).
2. Who authorises a maintenance period in a room: the teacher on the class page, or an admin schedule.
3. Whether to require the one-time bootloader re-flash (rollback) before enabling student OTA at a site.
