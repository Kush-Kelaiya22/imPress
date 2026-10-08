# OTA architecture

How a firmware image gets from an administrator's upload onto classroom devices, and how the system knows whether it worked. For the operator's step-by-step guide see [OTA updates](../guides/ota-updates.md); for the API see [REST](../api/rest-api.md#firmware-deployments-38) and [device API](../api/device-api.md).

## Overview

```mermaid
flowchart LR
    U["Upload .bin<br/>(Firmware page)"] --> V{"valid imPress image?<br/>chip · project · X.Y.Z · SHA-256 · size"}
    V -- no --> R["422 with the reason"]
    V -- yes --> A["firmware_artifacts<br/>status: uploaded"]
    A --> AP["Approve"] --> D["Deploy<br/>(select devices, strategy)"]
    D --> E["deployment engine<br/>(services/deployments.py)"]
    E -- "offer: pending_version + ota_update prompt" --> G["C6 gateway"]
    G -- "SPI MSG_OTA_PROMPT" --> S3["S3 hub"]
    S3 -- "Wi-Fi hop: check, download, verify, install, reboot" --> BE["backend"]
    S3 -- "result after reboot (SPI record)" --> G -- "batch ota_result" --> E
```

| Piece | Where | Responsibility |
|---|---|---|
| Image validation | `backend/app/services/firmware_image.py` | Read facts from the image; refuse anything that isn't a sound imPress app image (#35) |
| Registry | `firmware_artifacts`, `services/firmware_store.py`, `routers/firmware.py` | Immutable binaries (`<sha256>.bin`); uploaded → approved → deprecated; retention (#35, #36) |
| Deployment engine | `services/deployments.py`, `routers/deployments.py` | Per-device state machine, staged rollout, retries, timeouts, durability (#34, #38) |
| Device reports | `POST /api/device/ota/status`, batch `ota_result`, `firmware/check`, `firmware/download` | Move a device through the states |
| S3 client | `firmware/class_s3/main/ota.c` | Wi-Fi hop, HTTP status and size checks, `esp_ota_*`, result after reboot (#33) |

## Per-device state machine

```mermaid
stateDiagram-v2
    [*] --> waiting: in a later stage
    [*] --> queued: stage active
    waiting --> queued: stage starts (concurrency permitting)
    queued --> precheck: device asks firmware/check
    precheck --> downloading: download served / reported
    downloading --> verifying
    verifying --> installing
    installing --> rebooting
    rebooting --> health_check
    health_check --> success: running the expected version
    queued --> cancelled
    precheck --> cancelled
    waiting --> cancelled
    queued --> unreachable: timeout
    downloading --> timed_out: timeout
    rebooting --> rolled_back: bootloader reverted
    health_check --> rolled_back
    downloading --> failed
    installing --> failed
    failed --> waiting: retry (attempts left)
    timed_out --> waiting: retry
    unreachable --> waiting: retry
```

Rules (all enforced by `deployments.report()` and tested in `test_deployments.py`):

- **Forward only.** A device can skip states (the S3 reports only its final result) but never go back: 409. Repeating the current state is a no-op, so lost acknowledgements and relay duplicates are harmless.
- **Success needs proof.** `success` counts only when the device reports the image's version running **after** the reboot. Any other version is recorded as a failure, and the device row shows what really runs. A completed download, or a reboot, is not success.
- **Rollback is recorded as such.** `rolled_back` keeps the device on its previous version, and the pending version is cleared so the bad image isn't offered again.
- **Bounded retries.** `failed`, `timed_out` and `unreachable` are retried up to `max_attempts`. While a retry is pending, the device keeps `pending_version`.
- **Timeouts.** An attempt that hasn't finished within `timeout_s` becomes `unreachable` (never started) or `timed_out` (stalled).
- **Cancellation is safe.** Only `waiting`, `queued` and `precheck` are cancelled, because nothing has been written to flash yet. Devices further along finish and report.
- **Server-observed progress.** `firmware/check` moves `queued → precheck` and returns the image's SHA-256 and size. Serving the download moves it to `downloading`.

## Staged rollout

```mermaid
flowchart LR
    C["stage 0: canary<br/>(strategy.canary devices)"] --> H1{"failures ≤ max_failures?"}
    H1 -- yes --> B1["stage 1: batch_size devices"] --> H2{"…"} --> BN["last batch"] --> DONE["completed"]
    H1 -- no --> P["paused<br/>(note says which stage)"]
    P -- "Resume (accept)" --> B1
    P -- Cancel --> X["cancelled"]
```

| Strategy field | Default | Meaning |
|---|---|---|
| `canary` | 1 | devices in stage 0 |
| `batch_size` | 5 | devices per later stage |
| `max_concurrent` | 5 | devices updating at the same time (network load) |
| `max_failures` | 0 | failures a finished stage may have before the rollout pauses |
| `max_attempts` | 2 | tries per device |
| `timeout_s` | 900 | per attempt |

- **Selection:** specific devices, every device of the image's type, devices running a given version, or a classroom's devices (its gateway and the hub it relays). The filters can be combined.
- **Exclusions:** a device is excluded, with its reason shown in the preview, if it is:
  - a different type;
  - a student module (no over-the-air path yet);
  - disabled;
  - already on the version;
  - busy in another deployment;
  - due for a downgrade that wasn't explicitly allowed (`allow_downgrade`, which makes a `rollback` deployment).
- **Idempotency:** the same `idempotency_key` returns the deployment it created before, so a double submit or retry doesn't start two rollouts.
- **Durability:** everything is stored in `firmware_deployments` and `deployment_targets`. The scheduler (`deployments_loop`, every 5 s) is idempotent, so after a backend restart running deployments continue where they were. This is tested by dropping every database connection mid-rollout.
- **Per-device push:** *Push OTA* on the Modules page, and `POST /api/admin/modules/{id}/ota`, is a one-device deployment with the same guarantees.

## How each device type is reached

| Device | Prompt | Download | Result | Status |
|---|---|---|---|---|
| S3 hub | WS `device_command ota_update` → its C6 → SPI `MSG_OTA_PROMPT` | Wi-Fi hop, `firmware/download` | after reboot, `MSG_OTA_APPLIED` record → C6 → batch `ota_result` | implemented (#33) |
| C6 gateway | WS `ota_update` with its own MAC | `firmware/download` | `POST /api/device/ota/status` | client in progress (#34) |
| Student module | – | – | – | **no OTA transport**: ESP-NOW frames are ≤ 250 bytes and there is no Wi-Fi provisioning; deployments exclude them. Update over serial. |

## What is and isn't verified

- **Verified by automated tests:** image validation against real build output; the whole state machine and rollout logic against simulated devices (`test_deployments.py`, `ui_tests/test_deployments.py`); the S3 client's structure (`firmware/tests/test_ota_versioning.py`); IDF builds.
- **Not yet verified on hardware:** an actual S3 or C6 update, a rollback after a crashing image, power loss mid-download. The bench checklist is in PR #55 and will move into the hardware validation matrix (#43).
