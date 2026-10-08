# Device compatibility

Which firmware runs on which chip, what an over-the-air update can and can't change, and how firmware and backend versions interact. Values are **configured** in `sdkconfig`, `partitions.csv` and the source unless they are marked otherwise. Sizes are in [classroom node requirements](CLASSROOM_NODE_REQUIREMENTS.md).

## Matrix (v2.1.0)

| | Student module | Hub | Gateway |
|---|---|---|---|
| Project | `firmware/student` | `firmware/class_s3` | `firmware/class_c6` |
| Target | `esp32` | `esp32s3` | `esp32c6` |
| Image chip ID (header byte 12) | 0 | 9 | 13 |
| Flash: header size / mode | 4 MB / DIO | 32 MB / octal (OPI) | 8 MB / DIO |
| PSRAM | not used | optional (#30) | not available |
| App slots | 2 × 1,792 KB | 2 × 4,096 KB | 2 × 3,968 KB |
| Version source | `version.txt` → `esp_app_desc_t` (#33) | same | same |
| Over-the-air updates | **no**: no transport (ESP-NOW frames are ≤ 250 B, and the module has no Wi-Fi credentials) | yes (Wi-Fi hop, prompted via the gateway, #33) | yes (direct, #34) |
| App rollback (`BOOTLOADER_APP_ROLLBACK_ENABLE`) | off | on | on (since #34) |
| Reports to the backend | joins, leaves, heartbeats, answers and votes, through the hub and gateway | OTA results through the gateway | heartbeat with diagnostics (#39), batches, OTA status |
| Brown-out level | 0 | 7 | 7 |

## Images are not interchangeable

Each image is linked for one chip:
- **Bootloader:** reads the chip ID from the image header and refuses a mismatch.
- **Device:** `esp_ota_end()` refuses a mismatch as well.
- **Backend (#35):** checks the chip ID, the project name and the appended SHA-256 at upload. It deploys an image only to devices of its own type (`c6` / `s3` / `student`).

## What an over-the-air update can change

An OTA update replaces **only the app** in the inactive slot. Everything else on the flash stays as it was flashed over serial:

| Change | Over the air? |
|---|---|
| Application code, its version, Kconfig options compiled into the app | yes |
| Bootloader, including enabling app rollback (#34 on the C6) | **no**: serial |
| Partition table (slot sizes, adding partitions) | **no**: serial |
| Flash mode or size in the header (for example the [reduced-flash hub profile](CLASSROOM_NODE_REQUIREMENTS.md#reduced-flash-hub-profile-built-not-booted)) | **no**: serial, and every later image must be built the same way |
| NVS contents (Wi-Fi, backend address, API key, class ID, boot count) | kept across updates; edit them over serial or through a provisioning flow |

**Downgrades:** these need an explicit confirmation in the deploy dialog (`allow_downgrade`, #37/#38). The app's NVS layout is backward compatible within 2.x.

## Firmware ↔ backend

| Mix | Works? | Notes |
|---|---|---|
| v2.1 backend, v2.0 gateway | yes | The heartbeat diagnostics are optional (#39): shown as *not reported*, and the health rules that need them don't apply. Without the v2.1 gateway's OTA client, the gateway can't be updated over the air. |
| v2.1 backend, v2.0 hub | yes | Version reporting is wrong before #33 (hard-coded `0.1.0`), so deployments see the wrong running version until the hub runs v2.1. |
| v2.1 backend, older student modules without `device_id` | yes | The inventory falls back to the enrollment number as the key (#40). |
| v2.1 gateway, v2.0 backend | partly | Presence, quizzes and polls work: the extra heartbeat fields are ignored. OTA does not: a v2.0 backend sends no SHA-256 with its offer, so the gateway refuses it (#34), and `/api/device/ota/status` doesn't exist. Upgrade the backend first. |
| v2.1 hub with a v2.0 gateway, or the reverse | **no** | The hub↔gateway SPI link changed (#29: standard full-duplex SPI, a CRC-checked slot format). Flash both together. |

## Upgrading a room to v2.1

1. Upgrade the backend. Its migrations run at startup and back up the database first.
2. Flash the **gateway** and the **hub** over serial with v2.1. Do them together: the SPI link format changed (#29), and the gateway's bootloader gains rollback (#34).
3. Flash student modules over serial as convenient. v2.0 modules keep working with a v2.1 hub: the ESP-NOW message formats didn't change in v2.1. This was checked against the source, not on hardware.
4. From then on, update gateways and hubs from the Firmware page.

## Related

- [OTA architecture](../firmware/OTA_ARCHITECTURE.md)
- [OTA updates guide](../guides/ota-updates.md)
- [Hardware reference](../reference/hardware.md)
