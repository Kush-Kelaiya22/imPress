# Build, configure and flash the firmware

This walkthrough covers the three firmware roles. Use a supported ESP32-C6 for the gateway, an ESP32-S3 for the hub, and the project's student-module board for each learner. Board revisions and attached flash/PSRAM parts matter; check the [device compatibility](../hardware/DEVICE_COMPATIBILITY.md) and [hardware reference](../reference/hardware.md) before connecting power.

## Safety and prerequisites

- Install Espressif ESP-IDF **v6.1** and the matching USB-to-serial drivers, or use the pinned `espressif/idf:v6.1` Docker image to build. Keep the board disconnected while wiring and verify its voltage/pinout against the board documentation.
- Use a known-good USB data cable and identify the serial port (`COM5` in Windows Device Manager, `/dev/ttyACM0` or `/dev/ttyUSB0` on Linux, `/dev/cu.usbmodem*` on macOS). Close other serial monitors before flashing.
- Configure against a test server first. The defaults in project configuration are examples, not production credentials. Use a unique production device key, a reachable backend address, and matching 2.4 GHz credentials where the device needs Wi-Fi.
- A normal app `.bin` is not the same as a complete factory image. Use the project `idf.py flash` command for the first flash so the matching bootloader, partition table and app are installed together.

## Configure and build each role

From the repository root, for each project below, open its configuration menu, set the board's values, save, then build and flash:

```sh
cd firmware/class_c6
idf.py menuconfig
idf.py build
idf.py -p <PORT> flash monitor
```

Repeat with `firmware/class_s3` and `firmware/student`. In **Backend Server**, configure the server host and port, shared provisioning key and (when enabled) HTTPS/WSS and its CA trust. For the C6, set Wi-Fi credentials and the room/backend values. For the S3, set Wi-Fi values used by its OTA hop and the mesh channel. Set the student module's mesh channel to the same channel as the S3. Configuration option names and their NVS mapping are listed in the [configuration reference](../guides/configuration.md#c6-gateway-firmwareclass_c6).

Keep the mesh channel identical on all modules in a room. Use WPA2-PSK or better on 2.4 GHz. The device key must match the server's provisioning configuration during initial registration; devices with per-device-key support then use the key issued by the backend. Never paste private keys or real credentials into a public issue or commit them to source control.

For production over TLS, first make the backend serve HTTPS/WSS and install the intended CA certificate at the configured firmware path. Then enable TLS in **Backend Server**, build the C6 and S3, and test their connection before updating any fleet. A device whose TLS trust or hostname is wrong cannot fall back to plaintext; see [device TLS](../guides/deployment.md#tls-for-devices).

## Flash and verify

1. Connect only one board. Run `idf.py -p <PORT> flash monitor` from that role's project directory. If the tool cannot find the board, check the port, data cable, driver, permissions and bootloader/download-mode procedure for the exact board; do not erase the board until its recovery plan is understood.
2. Wait for `idf.py flash` to report success, then watch the serial monitor through reboot. The C6 should log its backend connection/registration result; the S3 should initialize its mesh/SPI link; a student module should display its enrollment/setup state.
3. Disconnect the monitor cleanly (`Ctrl+]` in the IDF monitor), power-cycle the board, and confirm it starts again without the USB serial session.
4. For the first classroom test, check **Modules** in the web app and the [end-to-end classroom checklist](../guides/deployment.md#4-go-live-checklist). Do not infer that flashing succeeded merely because the tool wrote bytes; verify the expected app version and online/health state.

Expected: the board boots the intended project/version and reports its real next-stage status. If logs show a backend key, TLS, Wi-Fi, room-link or mesh-channel error, correct that specific configuration and rebuild/reflash the affected role before trying a quiz.

## First v2.1 bootloader update

The rollback-capable bootloader cannot be sent by OTA. Flash each C6 and S3 once with the full v2.1 project image over serial. Later supported C6/S3 application updates can use the staged OTA flow. Student modules currently remain serial-flashed. See [OTA updates](../guides/ota-updates.md), [prebuilt release binaries](../guides/releases.md#flash-prebuilt-images), and the [recovery procedure](../firmware/RECOVERY_PROCEDURE.md).

## Student enrollment

After the student firmware boots, enroll the module using the board's physical setup controls described in the [hardware reference](../reference/hardware.md) and associate the student's roster record in the web application. Follow the exact button sequence and screen/log prompt for the board revision; do not reuse another student's enrollment identity. If the screen indicates that a module is already enrolled, use the documented re-provisioning procedure rather than erasing arbitrary flash regions.
