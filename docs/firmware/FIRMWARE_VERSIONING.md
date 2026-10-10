# Firmware versioning

How a firmware version is set, carried, checked and compared, from the build to the deployment engine.

## Where the version comes from

| Place | Holds | Read by |
|---|---|---|
| `firmware/<project>/version.txt` | the version of that project's image (`2.1.0`) | ESP-IDF at build time: with no `PROJECT_VER` set, it uses `version.txt` and writes it into the image's `esp_app_desc_t` |
| `esp_app_desc_t.version` | the version inside the built `.bin` (offset 48 of the app descriptor) | the device (`FIRMWARE_VERSION` = `esp_app_get_description()->version` in each `config.h`, #33); the backend's image parser at upload (#35) |
| `VERSION` (repository root) | the release version (#42) | the backend (`/health`, OpenAPI); a repository test requires every `version.txt` to equal it |

There is one source per image, and the device never hard-codes its version. Before #33 the hub reported a constant `0.1.0`, whatever it was running.

## Rules

1. **Semantic versions only.** `MAJOR.MINOR.PATCH` with digits only. The registry refuses an image whose embedded version isn't `X.Y.Z` (422).
2. **Immutable once uploaded.** For each target, one version means one set of bytes (`uq_firmware_artifacts_target_version`). Uploading the same bytes again is idempotent; uploading different bytes under an existing version is a **409**. To publish a fix, bump the version.
3. **The facts come from the image.** Target, chip, project and version are read from the binary, not the upload form. A C6 image can't be registered or deployed as an S3 one.
4. **Compared numerically.** `semver()` in `services/deployments.py` compares versions as integer tuples (2.10.0 > 2.9.0). A device already on the target version is excluded from a deployment, and one on a newer version is excluded unless the downgrade is confirmed (`allow_downgrade`).
5. **Success means the expected version is running.** A device reporting `success` with a different version is not counted as successful (`test_success_needs_the_expected_version`).

## Releasing a new version

1. **Patch releases are automatic** (#100). Every push to an integration line (`varun/v2.1`) that passes CI is released as `varun/v2.1.<n>`. The release workflow writes the version `2.1.<n>` into every `version.txt` before it builds, so each image's app descriptor carries it (without the owner). Download the images from the release (`impress-<owner>-<version>-firmware.zip`).
   **A new line** (`2.2`) is a pull request that sets `VERSION` and the three `version.txt` files to `2.2.0`. `tests/test_install_scripts.py` fails if they differ. See [releases](../guides/releases.md#starting-a-new-release-line).
2. For a local test image, build with `idf.py build`. It reports the repository's `X.Y.0`, so don't deploy it over a release version.
3. Upload `build/impress_<project>.bin` on the Firmware page and check that the version, target and chip shown are the ones you expect.
4. Approve it, then deploy it ([OTA updates](../guides/ota-updates.md)).
5. Add a changelog entry.

## What a version does not tell you

- **The bootloader or partition table.** OTA replaces only the app, so two devices on 2.1.0 can have different bootloaders. A gateway first flashed before 2.1 has no rollback until it is flashed over serial once ([device compatibility](../hardware/DEVICE_COMPATIBILITY.md#what-an-over-the-air-update-can-change)).
- **The build profile.** An S3 built with the reduced-flash profile and one built with the default profile both report 2.1.0, but their images are not interchangeable. Deploy to such hubs by selecting them explicitly, and only with images built from the same profile.

## Related

- [OTA architecture](OTA_ARCHITECTURE.md)
- [Recovery procedure](RECOVERY_PROCEDURE.md)
