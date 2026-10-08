# Recovery procedure

What to do when an update goes wrong, from the most automatic case to the most manual. Each step says how to tell it worked. Nothing here has been rehearsed on hardware yet ([hardware validation](../testing/HARDWARE_VALIDATION.md) H9, H10).

## 1. The device rolled itself back (no action needed)

**You see:** the device shows `rolled_back` on the deployment, its health is *error* ("last OTA update rolled back"), and it still runs the old version.

**What happened:** the new image didn't pass its health check, so the bootloader booted the previous one:
- **Gateway:** a 120 s watchdog fires if it can't reach SPI, Wi-Fi and the backend.
- **Hub:** the image doesn't reach mark-valid after it initialises.

**Next:**
1. Read the failed device's error on the Firmware page → deployment.
2. Don't resume the deployment until you know why. The rollout paused by itself (`max_failures`), so no other device received the image.
3. **Fix the image:** bump the version, rebuild, upload, approve and deploy the new image.
4. **Abandon the image:** cancel the deployment and deprecate the image.

The error health state clears after the next successful update.

## 2. A deployment paused or timed out

**You see:** the deployment is *paused*, or targets show `failed`, `timed_out` or `unreachable`.

| Target state | Meaning | Action |
|---|---|---|
| `failed` | the device reported an error (HTTP, size, SHA-256, `esp_ota_end`) and nothing was installed. On a device running the signed profile (#66), `esp_ota_end` also fails for an image that isn't signed with the key the device trusts. Check the image with `scripts/verify_firmware.py --key` | if attempts remain it is retried automatically; otherwise check the error, then resume or cancel |
| `timed_out` | it started but didn't finish within `timeout_s` (for example power loss) | retried while attempts remain; check the device is powered and online |
| `unreachable` | it never answered the offer | check the device's health (offline?) and that its gateway is connected |

- **Resume:** accepts the failures so far and continues with the next stage.
- **Cancel:** stops devices that haven't started installing. Devices already installing finish and report.

## 3. Roll a fleet back to an earlier version

The device-side rollback only covers the update that just failed. To go back to an older version that is already installed, use an operator rollback:

1. On the Firmware page, approve the older image again if it was deprecated.
2. Deploy it to the devices concerned and tick **Allow downgrading** (`allow_downgrade`; without it they are excluded as "would downgrade").
3. The deployment is recorded with `kind: rollback`.

## 4. A device can't update at all: reflash over serial

Use this when a device doesn't boot either image, is stuck in a reset loop (boot count rising, uptime short), or predates v2.1 and needs the new bootloader.

1. Check out the version you want to run, and build it:
   ```bash
   git checkout <tag or commit>
   cd firmware/<project> && idf.py build
   ```
2. Flash everything, including bootloader, partition table, initial `otadata` and app:
   ```bash
   idf.py -p <PORT> flash monitor
   ```
   `idf.py flash` writes the initial OTA data, so the device boots the image you just flashed, whichever slot ran before.
3. If the configuration in NVS is suspect, erase the whole flash first. This also erases Wi-Fi, the backend address, the device key and the class ID:
   ```bash
   idf.py -p <PORT> erase-flash flash monitor
   ```
   The device then boots with the Kconfig defaults (`idf.py menuconfig` → "imPress … Configuration") and writes them to NVS.

**It worked when:** the device registers, the Modules page shows the expected version, and its health is *online*.

## 5. The firmware signing key is lost

Devices on the signed profile accept only images signed with that key, so they can no longer be updated over the air.
1. Create a new key (`scripts/firmware_key.sh`, into a new directory).
2. Point `IMPRESS_FIRMWARE_SIGNING_KEY` at its public key.
3. Reflash each device over serial with a `scripts/build_signed.sh` image ([§4](#4-a-device-cant-update-at-all-reflash-over-serial)).

Prevent this: keep the private key backed up in two places, offline.

## 6. Undo a backend upgrade

1. Stop the service.
2. **Restore the database.** Before migrating, the backend copied it next to the original as `<db>.bak-<from>-to-<to>-<timestamp>`. Copy that file back over the database. Anything written after the upgrade is lost.
3. **Restore the code.** `git checkout` the previous release, then run `scripts/install.sh`.
4. Start the service. `GET /health` shows the old `version` and `schema_version`.

Firmware already on devices doesn't need to change. A v2.1 gateway against a v2.0 backend still handles presence and quizzes, but not OTA ([device compatibility](../hardware/DEVICE_COMPATIBILITY.md#firmware--backend)).

## Related

- [OTA architecture](OTA_ARCHITECTURE.md)
- [Firmware versioning](FIRMWARE_VERSIONING.md)
- [OTA updates guide](../guides/ota-updates.md#troubleshooting-ota)
- [Troubleshooting](../guides/troubleshooting.md)
