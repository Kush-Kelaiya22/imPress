# OTA updates

Over-the-air updates are implemented for the **S3 hub**. The C6 and student modules have dual OTA partitions but no OTA client yet, so update them over serial.

## How it works

```mermaid
flowchart TB
    U["Admin uploads s3-X.Y.Z.bin<br/>POST /api/admin/firmware/upload"] --> P["Admin pushes version to the hub<br/>POST /api/admin/modules/{s3_id}/ota"]
    P --> W["Backend: pending_version = X.Y.Z<br/>WS device_command ota_update → class room of the S3's C6 (gateway_id)"]
    W --> C6["C6: MSG_OTA_PROMPT over SPI"]
    C6 --> S3["S3: s3_ota task joins Wi-Fi<br/>(mesh + SPI keep running)"]
    S3 --> CK{"POST /firmware/check<br/>update_available?"}
    CK -- no --> DT["detach: unregister handlers · disconnect ·<br/>restore mesh channel — NO reboot"]
    CK -- yes --> DL["GET /firmware/download (only the pending version is served)<br/>esp_ota_write → esp_ota_end → set boot partition"]
    DL -- failure --> DT
    DL -- ok --> AP["MSG_OTA_APPLIED → C6 · reboot"]
    AP --> B{"first boot of the new image<br/>(PENDING_VERIFY)"}
    B -- "mesh + SPI init OK" --> V["esp_ota_mark_app_valid_cancel_rollback()"]
    B -- "crash / reset before that" --> RB["bootloader rolls back to the previous image"]
```

## Step by step

1. **Build** with the version string bumped (`FIRMWARE_VERSION` in `firmware/class_s3/main/config.h`):
   ```bash
   docker run --rm -v "$PWD/firmware":/project -w /project/class_s3 espressif/idf:v6.1 idf.py build
   # image: firmware/class_s3/build/impress_class_s3.bin
   ```
2. **Upload** (admin): *multipart* `device_type=s3`, `version=1.2.0`, `file=@impress_class_s3.bin`. The version must be semver (`1.2.0` or `v1.2.0`). It is stored as `firmware_bins/s3-1.2.0.bin`.
3. **Make sure the S3 has a gateway**: its `gateway_id` must point at the room's C6 (admin "link device"). Otherwise the prompt can't be delivered.
4. **Push**: `POST /api/admin/modules/{s3_id}/ota {"version": "1.2.0"}`. The response shows `pending_version` and `ota_status: downloading`.
5. **Watch:** the S3 log shows the hop, download size and reboot. After reboot: `New firmware verified — rollback cancelled`.
6. The device row is updated by `/firmware/check` (current version). `/firmware/applied` is available for reporting.

## Safety properties

| Property | Mechanism |
|---|---|
| A crashing image can't brick the hub | `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` + mark-valid only after mesh + SPI init |
| Only images an admin pushed can be fetched | `/firmware/download` requires `version == pending_version` of that device |
| No path traversal in the store | strict semver + a fixed device-type set |
| A no-op prompt doesn't disturb the class | no update → detach and continue, no reboot |
| Partial download | `esp_ota_end` validates the image; on error → abort and detach |

> The rollback-capable **bootloader** can't be delivered by OTA. Flash every S3 once over serial (`idf.py flash`) with the v2 `sdkconfig`.

## Signing images

Recommended for production. Without signing, anyone holding the device key and able to plant a file in the store, or to MITM the HTTP download, could ship code to hubs.

1. Generate a key **outside the repository** (it is git-ignored, but keep it offline anyway):
   ```bash
   espsecure.py generate_signing_key --version 2 secure_boot_signing_key.pem
   ```
2. `idf.py menuconfig` → *Security features*:
   - **Require signed app images** (`CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT`) for signature checks on OTA without burning eFuses, **or**
   - **Secure Boot v2** for full chain-of-trust (irreversible eFuse burn; plan carefully).
3. Set the signing key path, rebuild and flash **over serial once**. From then on `esp_ota_end()` rejects unsigned or mis-signed images.
4. Keep the key in a secrets manager; CI should sign release builds, not developer laptops.

## Transport security

The S3 currently downloads over `http://`. To move to HTTPS:
1. serve the backend behind TLS;
2. embed the CA certificate in the S3 firmware and set `esp_http_client_config_t.cert_pem`;
3. change `_url()` in `ota.c` to `https://`.

Signing (above) protects integrity even over plain HTTP; TLS adds confidentiality and protects the API key.

## Troubleshooting OTA

| Symptom | Check |
|---|---|
| S3 never starts a hop | Does the S3 row have `gateway_id`? Is the C6 connected to the class WS? (C6 log: `Relayed OTA prompt`) |
| `OTA aborted — could not connect to WiFi` | the S3's `wifi_ssid`/`wifi_pass` NVS values |
| `No pending update` | `pending_version` empty, or equal to the current version |
| download 403 | requested version ≠ `pending_version` (re-push) |
| download 404 | the file `s3-<version>.bin` is missing from `IMPRESS_FIRMWARE_DIR` |
| boots the old version after the update | rollback happened: the new image crashed before mark-valid; read its boot log |
