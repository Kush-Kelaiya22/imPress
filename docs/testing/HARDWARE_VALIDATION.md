# Hardware validation

What has and hasn't been verified on real boards. **As of 2026-10-08, no v2.1 check below has been run on hardware.** Every status is *not run* until someone runs it and records the result here. Simulated and host tests are listed next to each check so it's clear which software path is already covered, but they never count as a hardware pass.

## How to record a result

Replace *not run* with:

```
passed | failed — <board/module part numbers>, firmware <version + commit>, backend <version>, <date>, <who>; <notes, log excerpt or link>
```

A failed check gets a GitHub issue, linked from the row.

## Bench setup

- One gateway (ESP32-C6, ≥ 8 MB flash) and one hub (ESP32-S3; see [requirements](../hardware/CLASSROOM_NODE_REQUIREMENTS.md)) wired as in the [hardware reference](../reference/hardware.md#s3--c6-wiring).
- At least three student modules (classic ESP32, four buttons). Thirty or more for the load checks.
- A backend installed with `scripts/install.sh` on the same LAN, and its device key set on the gateway.
- A serial console on each of the three roles (`idf.py monitor`).

## Checks

### Link and mesh

| # | Check | Procedure | Pass when | Software covered by | Status |
|---|---|---|---|---|---|
| H1 | S3 ↔ C6 SPI link (#29) | power both, leave them 30 min | no `bad slot` / CRC lines on either console; the gateway's diagnostics show `s3_link_ok` true and S3 uptime rising | host `test_spi_slave.c`, `protocol` slot/FIFO tests | not run |
| H2 | Student join and leave | power a module, then switch it off | the class page lists it as connected, then *seen* within ~90 s (#40) | `test_student_modules.py`, `test_e2e_quiz.py` | not run |
| H3 | Multi-hop relay | place a module out of the hub's range, with another between | its answers arrive once; `hops` > 1 in the hub log | host `mesh_dedup` tests | not run |
| H4 | Quiz answers end to end | run a quiz with 3 modules | every press counted once, live on the teacher page | `test_e2e_quiz.py` | not run |
| H5 | Burst | 30 / 100 / 300 modules press within 1 s | stored = pressed; no `Message queue full` on the hub | `test_fault_injection.py` (backend side only) | not run |

### Over-the-air updates

| # | Check | Procedure | Pass when | Software covered by | Status |
|---|---|---|---|---|---|
| H6 | First serial flash with rollback (#34) | flash v2.1 to the C6 over serial | boots, registers, then updates over the air afterwards | — | not run |
| H7 | C6 OTA (#34) | deploy a newer C6 image from the Firmware page | every step appears on the deployment; the gateway runs the new version; `success` | `test_e2e_ota.py`, `test_c6_ota.py`, `test_ota_logic.c` | not run |
| H8 | S3 OTA (#33) | deploy a newer S3 image | the hub runs it; `applied` / `success` | `test_ota_results.py`, `test_deployments.py` | not run |
| H9 | C6 rollback | deploy an image built with a wrong Wi-Fi SSID | after 120 s the old image boots and reports `rolled_back` | `test_e2e_ota.py` (unhealthy image) | not run |
| H10 | Power loss mid-download | cut power during `downloading` | the old image boots; the target times out and is retried | `test_e2e_ota.py` (power loss) | not run |
| H11 | Staged rollout | 3 gateways, canary 1, batch 2 | the canary updates first; the rest only after it succeeds | `test_e2e_ota.py` | not run |

### Diagnostics and hardware variants

| # | Check | Procedure | Pass when | Software covered by | Status |
|---|---|---|---|---|---|
| H12 | Reset reasons (#39) | power-cycle; trigger a panic (`abort()` from a debug build); hold a task to trip the watchdog | diagnostics show `poweron`, `panic`, `task_wdt`; health `ERROR` for 10 min after a crash | `test_health.py`, `test_c6_diagnostics.py` | not run |
| H13 | Boot counter | power-cycle 3 times | `boot_count` rises by 3 | host `test_boot_count_increments_once_per_boot` | not run |
| H14 | S3 link loss | unplug the SPI cable | within 15 s the gateway reports `s3_link_ok` false, health `DEGRADED` | `test_health.py` | not run |
| H15 | Hub without PSRAM (#30) | flash the S3 image on a module with no PSRAM | boots; the log shows PSRAM not found, then normal operation | `test_hardware_requirements.py` | not run |
| H16 | Reduced-flash hub profile (#30) | build and flash the [8 MB quad profile](../hardware/CLASSROOM_NODE_REQUIREMENTS.md#reduced-flash-hub-profile-built-not-booted) on an 8 MB quad-flash S3 | boots, links to the C6, accepts an OTA update built with the same profile | build only | not run |

### Physical

| # | Check | Procedure | Pass when | Status |
|---|---|---|---|---|
| H17 | Range | walk a module away from the hub, with and without a relay | record the distance where answers stop | not run |
| H18 | Power draw | USB meter on each role: idle, during a quiz, during OTA | record mA; the gateway's brown-out never trips | not run |
| H19 | Endurance | a full school day, 30 modules, a quiz every hour | no resets (boot counter unchanged), lowest free heap stable | not run |

## Before v2.1

The `v2` audit found that no hardware evidence was available to it either. The intermittent C6 resets reported before `v2` were traced through code review (#1), not on a bench ([system audit](../engineering/SYSTEM_AUDIT.md)).
