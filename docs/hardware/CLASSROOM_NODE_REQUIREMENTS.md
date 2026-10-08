# Classroom node requirements

What hardware a classroom needs to run imPress v2.1: one **gateway** (ESP32-C6), one **hub** (ESP32-S3), and one **student module** (classic ESP32) per student.

Every value below is labelled with where it came from:

| Label | Meaning |
|---|---|
| **measured** | From a build: `idf.py size` or the image file. |
| **configured** | Read from `sdkconfig`, `partitions.csv` or the source. A build enforces it. |
| **computed** | Arithmetic on configured values, such as a struct size × a table length. |
| **estimate** | Reasoned, not measured. Treat it as a planning number until a bench run replaces it. |

Nothing on this page has been measured on a running board. The runtime figures (heap in use, CPU load, latency, radio range, power) need the bench procedure [below](#runtime-figures-pending-hardware).

## Static footprint (measured)

These were measured on 2026-10-08. The build used ESP-IDF v6.1 in Docker (`espressif/idf:v6.1@sha256:81893c71…`), on `varun/v2.1` at `d472e06` plus this change, with `idf.py size`.

| | Gateway `class_c6` | Hub `class_s3` | Student `student` |
|---|---|---|---|
| Chip (configured) | ESP32-C6, RISC-V, 160 MHz | ESP32-S3, 2 × Xtensa LX7, 160 MHz | ESP32, 2 × Xtensa LX6, 160 MHz |
| App image | 1,142,021 B | 980,692 B | 808,948 B |
| OTA slot (configured) | 3,968 KB (0x3E0000) | 4,096 KB (0x400000) | 1,792 KB (0x1C0000) |
| Image share of the slot (computed) | 28 % | 23 % | 44 % |
| Static RAM | DIRAM 187,835 of 452,112 B (41.5 %) | DIRAM 204,790 of 341,760 B (59.9 %) | DRAM 39,643 of 180,736 B (21.9 %); IRAM 90,163 of 131,072 B (68.8 %) |

Static RAM is what the image reserves before it runs: `.data`, `.bss` and IRAM code. The heap that is left over is shared by Wi-Fi, ESP-NOW, HTTP and the tasks. How much of it is actually used is a runtime figure. The C6 now reports its lowest free heap since boot (`min_free_heap`, #39), so that figure can be read from the Modules page once a gateway runs.

The hub's dedicated 16 KB IRAM region is full (`SPI_MASTER_IN_IRAM`), which is normal. Code that doesn't fit spills into DIRAM, which is included in the 59.9 %.

## Flash each build needs (configured)

The partition table fixes a hard minimum. The image header also declares a flash size and mode, and both must match the chip that is fitted.

| Project | Partitions end at | Minimum flash, from the partition table | Flash declared in the image header | Flash mode (configured) |
|---|---|---|---|---|
| `class_c6` | 0x7E0000 | 8 MB | 8 MB | DIO, 80 MHz |
| `class_s3` | 0x820000 | 16 MB | 32 MB | **octal (OPI)**, 80 MHz |
| `student` | 0x3A0000 | 4 MB | 4 MB | DIO, 40 MHz |

The shipped hub image is the restrictive one. It is built for **octal flash** with a **32 MB** header, so it needs an ESP32-S3 module with 32 MB of octal flash, such as the ESP32-S3-WROOM-2 family. Quad-flash modules, the much more common kind, can't boot it. See [the reduced-flash profile](#reduced-flash-hub-profile-built-not-booted).

## PSRAM

| | Before v2.1 | Since #30 |
|---|---|---|
| Hub (`class_s3`) | **Required.** With `SPIRAM_IGNORE_NOTFOUND` off, a module without PSRAM aborts at boot. | **Optional** (`CONFIG_SPIRAM_IGNORE_NOTFOUND=y`). No code needs PSRAM: the routing table is a static array, and nothing allocates with `MALLOC_CAP_SPIRAM`. When PSRAM is present, allocations over 16 KB may use it (`SPIRAM_USE_MALLOC`). |
| Gateway, student | not used | not used |

A firmware structural test, `firmware/tests/test_hardware_requirements.py`, fails if PSRAM becomes mandatory again.

## Configurations

### Minimum: runs the shipped images unchanged

| Role | Requirement | Source |
|---|---|---|
| Gateway | ESP32-C6 with ≥ 8 MB flash. No PSRAM needed. 2.4 GHz Wi-Fi coverage at the gateway. | configured |
| Hub | ESP32-S3 with **32 MB octal flash**. PSRAM optional. | configured |
| Student module | Classic ESP32 with ≥ 4 MB flash, plus four answer buttons, wired as in the [hardware reference](../reference/hardware.md#student-module). | configured |
| Students per room | ≤ 300 (`MESH_MAX_STUDENTS` on the hub, `STUDENT_SET_MAX` on the gateway). | configured |
| Hub ↔ gateway | SPI and ready lines, wired as in the [hardware reference](../reference/hardware.md#s3--c6-wiring). | configured |

### Reduced-flash hub profile (built, not booted)

Use this to run the hub on a cheaper and more common ESP32-S3 with **8 MB quad flash**, with or without quad PSRAM. It needs a rebuild and **one serial flash**: the bootloader, the flash mode and the partition table can't change over the air.

1. Add a partition table, `firmware/class_s3/partitions_8mb.csv`:
   ```csv
   # Name,   Type, SubType, Offset,   Size,     Flags
   nvs,      data, nvs,     0x9000,   0x6000,
   otadata,  data, ota,     0xf000,   0x2000,
   phy_init, data, phy,     0x11000,  0x1000,
   ota_0,    app,  ota_0,   0x20000,  0x3E0000,
   ota_1,    app,  ota_1,   0x400000, 0x3E0000,
   ```
2. Add `firmware/class_s3/sdkconfig.defaults.quad8`:
   ```ini
   # CONFIG_ESPTOOLPY_OCT_FLASH is not set
   CONFIG_ESPTOOLPY_FLASHMODE_QIO=y
   CONFIG_ESPTOOLPY_FLASHSIZE_8MB=y
   CONFIG_PARTITION_TABLE_CUSTOM=y
   CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions_8mb.csv"
   CONFIG_SPIRAM_MODE_QUAD=y
   ```
3. Delete `sdkconfig`, then build with both defaults files:
   ```bash
   idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.quad8" build
   ```
4. Flash everything over serial, bootloader included:
   ```bash
   idf.py -p <port> flash
   ```

| Check | Result | Label |
|---|---|---|
| The build completes on ESP-IDF v6.1 | yes; image 1,022,400 B | measured (2026-10-08) |
| The image and bootloader headers declare an 8 MB size and quad-capable mode | yes. The header says DIO, as ESP-IDF writes for QIO; the bootloader switches the flash to quad itself. | measured |
| It boots and runs on an 8 MB quad-flash S3 | **not verified** | pending hardware |

Two side effects of this profile:
- **Slot size:** each slot shrinks to 3,968 KB. The backend's image check (`SLOT_BYTES["s3"]` in `backend/app/services/firmware_image.py`) still allows 4,096 KB, so an image between 3,968 and 4,096 KB would pass upload and then fail `esp_ota_begin` on the device. Today's image is 1 MB.
- **Keep the profile consistent:** a hub flashed with this profile must receive OTA images built with the same profile. A default-build image declares octal flash and would not run.

### High capacity (estimate)

More than 300 students in one room needs a code change. `MESH_MAX_STUDENTS` (hub) and `STUDENT_SET_MAX` (gateway) must be raised together.

| Cost per extra student | Value | Label |
|---|---|---|
| Hub routing table entry (`student_entry_t`) | 32 B (11-char enrollment, ID, MAC, hops, RSSI, timestamp, flag, with padding) | computed |
| Gateway online-set entry | 11 B | computed |
| 300 students | hub 9.6 KB, gateway 3.3 KB | computed |

Static RAM is not the limit. Radio airtime and the hub's 64-message forwarding queue (`MSG_QUEUE_SIZE`) are more likely to limit a large room: a quiz in which every student presses a button within the same second. That is an **estimate**. Measure it with the burst test below before relying on it.

## Runtime figures (pending hardware)

None of these have been measured. Record them here with the board, firmware version and date when they are.

| Figure | How to measure | Status |
|---|---|---|
| Gateway heap in use, lowest free heap | Modules page → Diagnostics (`min_free_heap`, #39) after 1 h with 30 students | pending |
| Hub free heap | serial log; not reported to the backend yet | pending |
| Answer latency, button → teacher dashboard | timestamp a button press on a student (serial) and the WS `quiz_answer` event | pending |
| Burst handling | 30 / 100 / 300 modules answering within 1 s: answers stored vs pressed, `skipped`, `Message queue full` lines in the hub log | pending |
| Mesh range and hop count | walk test with `rssi` and `hops` from the hub's routing table | pending |
| Power draw | USB meter on each role: idle, during a quiz, during OTA | pending |
| OTA duration | deployment timeline (precheck → success) for each role on the room's Wi-Fi | pending |

The full bench checklist is in [hardware validation](../testing/HARDWARE_VALIDATION.md).

## Related

- [Device compatibility](DEVICE_COMPATIBILITY.md): which image runs where, and what can change over the air.
- [Hardware reference](../reference/hardware.md): wiring, pins, power.
- [System audit §2](../engineering/SYSTEM_AUDIT.md#2-hardware-and-device-architecture): the pre-v2.1 baseline.
