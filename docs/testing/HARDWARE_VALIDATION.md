# Hardware validation

What has and hasn't been verified on real boards. **As of 2026-10-08, no v2.1 check below has been run on hardware.** Every status is *not run* until someone runs it and records the result here, in a pull request that links the test issue. Simulated and host tests are listed next to each check so it's clear which software path is already covered, but they never count as a hardware pass.

## Test plan and ownership

The checks below are planned as GitHub issues. Each issue has numbered test cases with steps, expected results, edge cases, pass criteria and the recording format. The tracking issue is [#94](https://github.com/Kush-Kelaiya22/imPress/issues/94). It gives the run order and the equipment list.

| Order | Issue | Checks |
|---|---|---|
| 1 | [#84](https://github.com/Kush-Kelaiya22/imPress/issues/84): bench bring-up and SPI link soak | H6, H1 |
| 2 | [#85](https://github.com/Kush-Kelaiya22/imPress/issues/85): student identity, join and leave, multi-hop relay | H2, H3 |
| 3 | [#86](https://github.com/Kush-Kelaiya22/imPress/issues/86): quizzes and polls end to end | H4 |
| 4 | [#83](https://github.com/Kush-Kelaiya22/imPress/issues/83): timed quizzes on modules | H20 |
| 5 | [#90](https://github.com/Kush-Kelaiya22/imPress/issues/90): diagnostics and health states | H12–H14 |
| 6 | [#88](https://github.com/Kush-Kelaiya22/imPress/issues/88): gateway OTA, rollback, power loss | H7, H9, H10 |
| 7 | [#89](https://github.com/Kush-Kelaiya22/imPress/issues/89): hub OTA and staged rollout | H8, H11 |
| 8 | [#92](https://github.com/Kush-Kelaiya22/imPress/issues/92): device keys, signed firmware, TLS | H21–H23 |
| 9 | [#87](https://github.com/Kush-Kelaiya22/imPress/issues/87): burst load and endurance | H5, H19 |
| 10 | [#93](https://github.com/Kush-Kelaiya22/imPress/issues/93): range, power, brownout, buttons | H17, H18 |
| 11 | [#91](https://github.com/Kush-Kelaiya22/imPress/issues/91): hub variants (no PSRAM, 8 MB quad flash) | H15, H16 |

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

| # | Check | Procedure | Pass when | Software covered by | Test issue | Status |
|---|---|---|---|---|---|---|
| H1 | S3 ↔ C6 SPI link (#29) | power both, leave them 30 min | no `bad slot` / CRC lines on either console; the gateway's diagnostics show `s3_link_ok` true and S3 uptime rising | host `test_spi_slave.c`, `protocol` slot/FIFO tests | [#84](https://github.com/Kush-Kelaiya22/imPress/issues/84) | not run |
| H2 | Student join and leave | power a module, then switch it off | the class page lists it as connected, then *seen* within ~90 s (#40) | `test_student_modules.py`, `test_e2e_quiz.py` | [#85](https://github.com/Kush-Kelaiya22/imPress/issues/85) | not run |
| H3 | Multi-hop relay | place a module out of the hub's range, with another between | its answers arrive once; `hops` > 1 in the hub log | host `mesh_dedup` tests | [#85](https://github.com/Kush-Kelaiya22/imPress/issues/85) | not run |
| H4 | Quiz answers end to end | run a quiz with 3 modules | every press counted once, live on the teacher page | `test_e2e_quiz.py` | [#86](https://github.com/Kush-Kelaiya22/imPress/issues/86) | not run |
| H5 | Burst | 30 / 100 / 300 modules press within 1 s | stored = pressed; no `Message queue full` on the hub | `test_fault_injection.py` (backend side only) | [#87](https://github.com/Kush-Kelaiya22/imPress/issues/87) | not run |

### Over-the-air updates

| # | Check | Procedure | Pass when | Software covered by | Test issue | Status |
|---|---|---|---|---|---|---|
| H6 | First serial flash with rollback (#34) | flash v2.1 to the C6 over serial | boots, registers, then updates over the air afterwards | — | [#84](https://github.com/Kush-Kelaiya22/imPress/issues/84) | not run |
| H7 | C6 OTA (#34) | deploy a newer C6 image from the Firmware page | every step appears on the deployment; the gateway runs the new version; `success` | `test_e2e_ota.py`, `test_c6_ota.py`, `test_ota_logic.c` | [#88](https://github.com/Kush-Kelaiya22/imPress/issues/88) | not run |
| H8 | S3 OTA (#33) | deploy a newer S3 image | the hub runs it; `applied` / `success` | `test_ota_results.py`, `test_deployments.py` | [#89](https://github.com/Kush-Kelaiya22/imPress/issues/89) | not run |
| H9 | C6 rollback | deploy an image built with a wrong Wi-Fi SSID | after 120 s the old image boots and reports `rolled_back` | `test_e2e_ota.py` (unhealthy image) | [#88](https://github.com/Kush-Kelaiya22/imPress/issues/88) | not run |
| H10 | Power loss mid-download | cut power during `downloading` | the old image boots; the target times out and is retried | `test_e2e_ota.py` (power loss) | [#88](https://github.com/Kush-Kelaiya22/imPress/issues/88) | not run |
| H11 | Staged rollout | 3 gateways, canary 1, batch 2 | the canary updates first; the rest only after it succeeds | `test_e2e_ota.py` | [#89](https://github.com/Kush-Kelaiya22/imPress/issues/89) | not run |

### Diagnostics and hardware variants

| # | Check | Procedure | Pass when | Software covered by | Test issue | Status |
|---|---|---|---|---|---|---|
| H12 | Reset reasons (#39) | power-cycle; trigger a panic (`abort()` from a debug build); hold a task to trip the watchdog | diagnostics show `poweron`, `panic`, `task_wdt`; health `ERROR` for 10 min after a crash | `test_health.py`, `test_c6_diagnostics.py` | [#90](https://github.com/Kush-Kelaiya22/imPress/issues/90) | not run |
| H13 | Boot counter | power-cycle 3 times | `boot_count` rises by 3 | host `test_boot_count_increments_once_per_boot` | [#90](https://github.com/Kush-Kelaiya22/imPress/issues/90) | not run |
| H14 | S3 link loss | unplug the SPI cable | within 15 s the gateway reports `s3_link_ok` false, health `DEGRADED` | `test_health.py` | [#90](https://github.com/Kush-Kelaiya22/imPress/issues/90) | not run |
| H15 | Hub without PSRAM (#30) | flash the S3 image on a module with no PSRAM | boots; the log shows PSRAM not found, then normal operation | `test_hardware_requirements.py` | [#91](https://github.com/Kush-Kelaiya22/imPress/issues/91) | not run |
| H16 | Reduced-flash hub profile (#30) | build and flash the [8 MB quad profile](../hardware/CLASSROOM_NODE_REQUIREMENTS.md#reduced-flash-hub-profile-built-not-booted) on an 8 MB quad-flash S3 | boots, links to the C6, accepts an OTA update built with the same profile | build only | [#91](https://github.com/Kush-Kelaiya22/imPress/issues/91) | not run |

### Physical

| # | Check | Procedure | Pass when | Test issue | Status |
|---|---|---|---|---|---|
| H17 | Range | walk a module away from the hub, with and without a relay | record the distance where answers stop | [#93](https://github.com/Kush-Kelaiya22/imPress/issues/93) | not run |
| H18 | Power draw | USB meter on each role: idle, during a quiz, during OTA | record mA; the gateway's brown-out never trips | [#93](https://github.com/Kush-Kelaiya22/imPress/issues/93) | not run |
| H19 | Endurance | a full school day, 30 modules, a quiz every hour | no resets (boot counter unchanged), lowest free heap stable | [#87](https://github.com/Kush-Kelaiya22/imPress/issues/87) | not run |

### Added after the first plan

| # | Check | Procedure | Pass when | Software covered by | Test issue | Status |
|---|---|---|---|---|---|---|
| H20 | Timed quizzes (#73) | per-question 10 s and total 30 s quizzes on modules with and without a display | countdown on the OLED, presses after the deadline ignored by the module and refused by the server, automatic advance and end within ±1.5 s | `test_quiz_timer.py`, `test_quiz_timing.py`, `test_student_quiz_timer.py` | [#83](https://github.com/Kush-Kelaiya22/imPress/issues/83) | not run |
| H21 | Per-device keys (#66) | erase and flash a gateway; reset its key; disable it; copy its key to another board | key issued then active; 401 recovery after a reset; 403 when disabled or on another MAC | `test_device_keys.py`, `test_device_keys_firmware.py` | [#92](https://github.com/Kush-Kelaiya22/imPress/issues/92) | not run |
| H22 | Signed firmware (#66) | first signed-profile install, then an unsigned and a wrongly signed image | the device refuses both (`esp_ota_end` fails, `failed`) and keeps running | `test_firmware_signing.py`, CI signed build | [#92](https://github.com/Kush-Kelaiya22/imPress/issues/92) | not run |
| H23 | Device TLS (#66) | HTTPS/WSS with a private CA; a host-name mismatch; a TLS image before the server serves TLS | encrypted traffic only; no fallback to HTTP; rollback after 120 s | `test_device_tls.py`, CI TLS builds | [#92](https://github.com/Kush-Kelaiya22/imPress/issues/92) | not run |

## Before v2.1

The `v2` audit found that no hardware evidence was available to it either. The intermittent C6 resets reported before `v2` were traced through code review (#1), not on a bench ([system audit](../engineering/SYSTEM_AUDIT.md)).
