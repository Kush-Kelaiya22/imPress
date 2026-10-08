# v2 / v3 comparison

| | |
|---|---|
| `v2` | `4fce7f7`: audit fixes #1–#25, tests, CI, docs |
| `v3` | `c88d3c7` "feat: demo ready" (author `_Encrypted`, 2026-10-08). **One commit, directly on top of `v2`.** |
| Diff | `git diff --stat origin/v2 origin/v3`: 9 files, +1031 / −294 |
| `v3` CI | [run 37732615325](https://github.com/Kush-Kelaiya22/imPress/actions/runs/37732615325): **failure** in one job (`host:class_c6`); every other job, including all three ESP-IDF builds, passed |

## Scope of the difference

| Area | Files changed in `v3` |
|---|---|
| Frontend (vanilla SPA, React) | **none** |
| Backend, database, API | **none** |
| CI, dependencies, tests | **none** |
| Firmware: C6 gateway | `main/main.c`, `main/spi_slave.c`, `sdkconfig` |
| Firmware: S3 hub | `main/main.c`, `main/spi_master.c`, `main/mesh_master.c`, `main/config.h` |
| Firmware: student | `main/config.h` |
| Other | `docs.zip` (72 KB binary archive) |

> [!IMPORTANT]
> The brief describes UI defects in `v2` "reportedly corrected in `v3`". **`v3` contains no UI changes**: neither the vanilla SPA (`backend/app/static`) nor the React app (`frontend/`) differ between the branches (`git diff origin/v2 origin/v3 -- backend frontend` is empty). There is nothing to port for the UI. The value of `v3` is entirely in the S3↔C6 SPI link and two firmware bug fixes, which match the commit message: the hardware demo started working.

## Why `v3` CI failed

The first causal error, from the job log:

```
../main/spi_slave.c:184:32: error: 'pdFALSE' undeclared (first use in this function)
```

`v3`'s rewritten `spi_post_trans_cb` uses `pdFALSE` and `portYIELD_FROM_ISR()`. The host test (`firmware/class_c6/test_host`) compiles the real `spi_slave.c` against minimal FreeRTOS stubs that don't define them. This is a **test-harness gap, not a firmware defect**: the same file compiled in the real ESP-IDF build, which passed. The fix is to extend the stubs and update the test for the new queue semantics. No test is weakened.

## Change-by-change matrix

| # | Component | `v2` behaviour | `v3` behaviour | Root cause addressed | Benefit | Risk | Decision |
|---|---|---|---|---|---|---|---|
| 1 | S3 + C6 SPI bus mode | S3 master **quad half-duplex**; C6 `spi_slave` (standard full-duplex only) | Both **standard full-duplex** (MOSI/MISO), WP/HD unused | Incompatible wire modes; slots never exchanged correctly ([audit](SYSTEM_AUDIT.md) A1) | Link works (demo) | Two pins freed; throughput still ≫ need | **Adopt** |
| 2 | S3 SPI clock | 80 MHz | 10 MHz | Signal integrity on hand-wired boards (inferred: no scope traces were available) | Reliable clocking | One 4 KB slot takes ~3.3 ms instead of ~0.4 ms; the link is far from saturated (§ below) | **Adapt**: Kconfig `SPI_CLOCK_MHZ`, default 10, so a PCB build can raise it |
| 3 | TX path, both ends | One pending slot; a new `send()` **overwrites** the previous one (latest wins) | 8-deep FIFO per side; the DMA buffer is written only between transactions | Lost back-to-back frames (A2); writing the DMA buffer while clocked | No dropped commands; no torn slots | +32 KB static RAM per side (C6 34%→41%, S3 50%→60% DIRAM) | **Adopt** |
| 4 | C6 RX validation | CRC-16 checked in the ISR before accepting a slot | **CRC not checked at all** | none (regression) | none | Corrupt S3 slots reach the batch parser | **Adapt**: verify CRC when the slot is reaped (task context) |
| 5 | CRC implementation | Local copy in each driver | Local copy in each driver | n/a | n/a | Duplication (contradicts [D4](../design/decisions.md)) | **Adapt**: use the shared `crc16_ccitt()` (bit-identical, see the host test) |
| 6 | S3 link task scheduling | Wait on a semaphore (TX queued or R_C6 rising-edge ISR); transfer only if something is pending | Fixed `vTaskDelay(poll_interval)`, then **always** transfer; R_C6 ISR removed | Missed ready-line edges stalled the link (inferred) | Link can't stall | Up to 50 ms extra latency for S3→C6 frames | **Adapt**: wait on the semaphore *with* the poll interval as timeout (immediate wake on TX), then always transfer |
| 7 | C6 SPI servicing | `spi2http` every 50 ms and **skipped while Wi-Fi is down** | Every 2 ms, always; only the HTTP flush waits for Wi-Fi | The S3 can't clock a slot the C6 hasn't re-armed (A3) | Mesh traffic and commands keep flowing during Wi-Fi drops | Batch grows **without bound** during a long outage, leading to heap exhaustion and reset | **Adapt**: cap the buffered batch (oldest heartbeats dropped first, counted, logged) |
| 8 | C6 student count | `++` on every heartbeat, `--` on leave | Set of online enrollments, maintained from JOIN/LEAVE | Count was meaningless (A4) | Correct count for the backend | Stale after an S3 reboot (no LEAVEs sent) | **Adapt**: clear the set when the S3 heartbeat's `uptime_s` goes backwards |
| 9 | S3 mesh heartbeat | `msg_encode()` then `mesh_master_broadcast()`, which encodes again | Raw payload to `mesh_master_broadcast()` | Double encoding (A5) | Students parse heartbeats | none | **Adopt** |
| 10 | S3 `heartbeat_task` buffers | Encode into `encoded[]`, copy into `slot[]` | Encode straight into `slot + header`, then `spi_record_write()` copies the frame **onto itself** | Saves 250 B of `.bss` | negligible | `memcpy` with overlapping (identical) source and destination is undefined behaviour | **Reject**: keep `v2` |
| 11 | C6 flash mode | QIO | DIO | Boards whose flash doesn't support QIO fail to boot or reset at boot | Boots on more modules | ~5–10% slower flash reads, irrelevant here | **Adopt** |
| 12 | C6 batch logging | One INFO line per flush | Adds INFO dump of the **whole batch JSON** and the HTTP status | Demo visibility | Debugging | Every student answer and enrollment number in the UART log; UART time on the hot path | **Adapt**: keep the HTTP result at INFO, the JSON dump at DEBUG |
| 13 | C6 command relay log | none | INFO log of each queued SPI command with rc | Visibility | Useful field diagnostics | none | **Adopt** |
| 14 | Student `DEFAULT_ENROLLMENT` | `"0000000000"` placeholder | `"AU24401230"` | Demo convenience | none | It is the **unprovisioned sentinel** (`config.c` compares against it), so every unprovisioned module would claim to be that student, and that student could never provision. It also looks like a real student ID. | **Reject** |
| 15 | `docs.zip` | n/a | 72 KB archive committed | n/a | none | Binary duplicate of `docs/` | **Reject** |
| 16 | C6 `sdkconfig` `# default:` lines | present | some removed | menuconfig rewrite | none | none | **Adopt** (comes with #11) |

### Link budget check for #2

At 10 MHz, one 4096-byte full-duplex slot takes 4096 × 8 / 10⁶ s ≈ 3.3 ms. With the 50 ms poll interval that is about 7% bus utilisation. One slot carries up to 136 quiz answers (the record format from #2), so the link can move ~2,700 answers/s, far above a 300-student class answering once per question.

## Outcome

- Adopted or adapted: 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 16, in branch `fix/v2.1-v3-firmware-link` ([#29](https://github.com/Kush-Kelaiya22/imPress/issues/29)). Each adaptation has a host or structural test.
- Rejected: 10, 14, 15.
- The UI recovery workstream ([#28](https://github.com/Kush-Kelaiya22/imPress/issues/28)) is closed as **not applicable**, with this document as evidence.
- Hardware verification of the link (both boards, a full class) stays open under `needs:hardware`.
