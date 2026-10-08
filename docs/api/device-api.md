# Device API (gateway ↔ backend)

These endpoints are called by firmware: the C6 gateway (`firmware/class_c6/main/wifi_client.c`) and the S3 during its OTA hop (`firmware/class_s3/main/ota.c`). Treat request and response shapes as a **firmware contract**: firmware in the field can't be changed as easily as a browser.

## Authentication

Every request carries the shared device key:
```
X-API-Key: <IMPRESS_DEVICE_API_KEY>
```
A missing header → `422`; a wrong key → `403`. The key is compared in constant time. On the device side it comes from Kconfig `DEVICE_API_KEY`, overridable via NVS `api_key`.

## Endpoint summary

| Method & path | Caller | Purpose |
|---|---|---|
| `POST /api/device/register` | C6 at boot and on Wi-Fi reconnect; S3 on OTA hop | create/update the device, mark it online, link the gateway to a class |
| `POST /api/device/heartbeat` | C6 every 15 s; S3 on OTA hop | liveness + telemetry |
| `POST /api/device/ping` | C6 every 120 s | classroom status update (activity log) |
| `POST /api/device/batch` | C6, batched (≤ 20 msgs or 500 ms) | student mesh events: joins, leaves, answers, votes, heartbeats |
| `POST /api/device/attendance` | (available) | explicit attendance check-in |
| `POST /api/device/firmware/check` | S3 on OTA hop | is an update pending? |
| `GET /api/device/firmware/download` | S3 on OTA hop | fetch the pending image |
| `POST /api/device/firmware/applied` | (pre-v2.1 clients) | report an applied update (goes through the state machine) |
| `POST /api/device/ota/status` | OTA clients | report update progress (#34) |
| `POST /api/polls/{id}/vote`, `POST /api/quizzes/{id}/answer` | direct device submissions (not used by current firmware) | see [below](#direct-voteanswer-endpoints) |
| `WS /ws/class/{id}?role=device` | C6 | backend → device commands. See the [WebSocket API](websocket-api.md). |

---

## Register

`POST /api/device/register`
```json
{"mac_address": "48:F6:EE:FF:FE:C7", "device_type": "c6", "device_name": "imPress C6",
 "firmware_version": "1.0.0", "classroom_code": ""}
```
```json
{"device_id": 12, "status": "registered", "class_id": 3}
```

Behaviour:
- **Upsert by `mac_address`**: name and type are updated; the device is marked online (`esp_device.online` logged only on an offline → online transition).
- **Class linking** (`class_id` in the response; the C6 adopts it and persists it to NVS):

```mermaid
flowchart TB
    A{"classroom_code given and matches<br/>a class code / classroom_code?"} -- yes --> B["link that class to this device"]
    A -- no --> C{"device already linked?"}
    C -- yes --> D["keep that class"]
    C -- no --> E{"device_type == c6?"}
    E -- no --> F["class_id = null (S3 / student never auto-link)"]
    E -- yes --> G{"an active class without a gateway?"}
    G -- yes --> H["link the first such class (lowest id)"]
    G -- no --> F
```

## Heartbeat

`POST /api/device/heartbeat`
```json
{"mac_address": "48:F6:EE:FF:FE:C7", "battery_pct": 100, "rssi": -61, "firmware_version": "1.0.0",
 "student_count": 27, "free_heap": 180000, "total_flash": 8388608,
 "uptime_s": 3600, "reset_reason": "poweron", "boot_count": 12, "min_free_heap": 151000,
 "s3_link_ok": true, "s3_uptime_s": 3590}
```
→ `{"status":"ok","server_time":"2026-10-07T21:35:16.319+05:30"}` · unknown MAC → `404`.

It updates `last_seen`, battery, RSSI and firmware version, plus non-zero `student_count` / `free_heap` / `total_flash`, then pushes presence to teachers.

**Diagnostics (#39), optional.** Firmware before v2.1 omits them and keeps working; they are then shown as *not reported*. An out-of-range value is a `422`.

| Field | Meaning |
|---|---|
| `uptime_s` | seconds since this boot |
| `reset_reason` | why the chip last reset (`esp_reset_reason()`): `poweron`, `external`, `software` (`esp_restart`, e.g. after an OTA update), `panic`, `int_wdt`, `task_wdt`, `wdt`, `deepsleep`, `brownout`, `other`; ≤ 16 characters |
| `boot_count` | boots since the first flash, from NVS (a rising count with short uptimes means a reset loop) |
| `min_free_heap` | lowest free heap since boot, in bytes |
| `s3_link_ok` | the S3's own heartbeat arrived over SPI within 15 s (3 × its default 5 s interval) |
| `s3_uptime_s` | uptime the S3 last reported (`0` when the link is down) |

### Health states

Computed from the latest values on every read (`services/health.py`); the first rule that matches wins:

| State | When |
|---|---|
| `UNKNOWN` | never seen |
| `OFFLINE` | silent for more than 30 s |
| `UPDATING` | an OTA update is in progress (the device's deployment target is active) |
| `ERROR` | the last OTA update failed (`failed`, `rolled_back`, `timed_out`, `unreachable`), or a `panic`, `int_wdt`, `task_wdt`, `wdt` or `brownout` reset in the last 10 minutes |
| `DEGRADED` | `s3_link_ok` is false, Wi-Fi RSSI below −80 dBm, or `min_free_heap` below 20 KB |
| `ONLINE` | otherwise |

`DeviceResponse` (`GET /api/admin/modules`, `/modules/{id}`) carries `health`, `health_reasons` (why, in words) and every field above, plus `diag_at` (when they were reported). The diagnostics are read-only: they add no remote control over devices.

## Status ping

`POST /api/device/ping`
```json
{"mac_address": "48:F6:EE:FF:FE:C7", "class_id": 3, "student_count": 27, "uptime_s": 3600, "rssi": -55, "free_heap": 175000}
```
→ `{"status":"ok","server_time":…}` and an `ActivityLog` row `class.status_update` (`entity_id = class_id` when > 0). Unknown MAC → `404`.

## Batch

`POST /api/device/batch`
```json
{"device_type": "c6", "messages": [
  {"type": "heartbeat", "device_mac": "48:F6:EE:FF:FE:C7", "battery_pct": 100},
  {"type": "student_join", "enrollment_number": "ABCDE12345", "device_mac": "48:F6:EE:FF:FE:C7", "class_code": "", "device_id": 3577735345},
  {"type": "quiz_answer", "quiz_id": 4, "question_order": 0, "enrollment_number": "ABCDE12345",
   "selected_option": 1, "response_time_ms": 0, "device_id": 3577735345},
  {"type": "poll_vote", "poll_id": 2, "enrollment_number": "ABCDE12345", "selected_option": 2, "device_id": 3577735345},
  {"type": "student_leave", "enrollment_number": "ABCDE12345", "device_mac": "48:F6:EE:FF:FE:C7", "device_id": 3577735345, "reason": 0}
]}
```
→ `{"status": "ok", "processed": <stored/applied>, "skipped": <rejected answers/votes>}`

| `type` | Processing |
|---|---|
| `heartbeat` | relayed for the sender `device_id` (a student module, or `0` for the S3). The gateway `device_mac` → `last_seen`, mark online; its own battery and RSSI come only from `POST /heartbeat` (#40: a student's 12 % used to overwrite the gateway's). A non-zero `device_id` also updates that module's inventory row: battery, RSSI, connected |
| `student_join` | **inventory (#40):** upsert the module by `device_id` (by `enrollment_number` when an older firmware omits it): connected, its enrollment, the relaying gateway and that gateway's class. Then, for a known enrollment, `ActivityLog student.connect`, and if `class_code` matches a class, a `StudentEnrollment` if missing |
| `student_leave` | inventory row → *seen previously*; known enrollment → `ActivityLog student.disconnect` |
| `quiz_answer` | **stored only if** the student is known, the quiz exists and is `active`, the question exists, `0 ≤ selected_option < len(options)`, all ints, and no answer yet for (quiz, question, student). Otherwise `skipped += 1` |
| `poll_vote` | stored only if the student is known, the poll is active, the option is in range, and no vote yet for (poll, student) |
| `ota_result` | `{mac_address (12 hex, as the S3 registered), version, result: applied\|rolled_back\|failed, error, device_mac}` from the S3 via its C6 (#33). Updates the device: `applied` with the pushed version → `ota_status: applied`; another version → `failed`; `rolled_back` clears the pending version; `failed` keeps it. Logged as `module.ota_result`. Unknown MAC or result → `skipped` |

Each stored answer or vote broadcasts the live count to the class room (`quiz_answer` with `total_answers`, `poll_vote` with `total_votes`). Duplicates within one batch are caught too, because the session autoflushes before each duplicate check.

## Attendance

`POST /api/device/attendance`: `{"enrollment_number": "ABCDE12345", "class_code": "BIO1", "mac_address": ""}`

| Condition | Result |
|---|---|
| unknown class code | 404 |
| class inactive | 400 |
| unknown enrollment number | 404 |
| student not enrolled in the class (and no device fallback) | 400 |
| ok | 200 `{"status":"checked_in","class_name":"Bio"}`; upsert, so repeated check-ins keep one row |

## Firmware check, download, status

```
POST /api/device/firmware/check   {"mac_address": "…", "current_version": "1.0.0"}
→ {"update_available": true, "version": "1.2.0", "ota_status": "precheck", "current_version": "1.0.0",
   "sha256": "<64 hex>", "size": 980320, "deployment_id": 7}

GET  /api/device/firmware/download?mac_address=…&version=1.2.0   → application/octet-stream
     X-Firmware-SHA256: <64 hex>

POST /api/device/ota/status  {"mac_address": "…", "state": "verifying"}
POST /api/device/ota/status  {"mac_address": "…", "state": "success", "version": "1.2.0"}
POST /api/device/ota/status  {"mac_address": "…", "state": "failed", "error": "esp_ota_end", "error_code": 5379}
→ {"status": "ok", "state": "...", "deployment_id": 7}
```
- **`firmware/check`:**
  - `update_available` is true when `pending_version` is set and differs from the reported version;
  - for an update offered by a deployment, it returns the image's **SHA-256 and size**, which the device verifies before installing;
  - it moves the device `queued → precheck`.
- **Download:**
  - only the device's `pending_version` is served: with no pending update, or a different version, it returns `403`;
  - the image comes from the registry for the device's own type (`404` if none);
  - the response carries `X-Firmware-SHA256` and moves the device to `downloading`.
- **`ota/status`:**
  - states: `precheck`, `downloading`, `verifying`, `installing`, `rebooting`, `health_check`, `success`, `rolled_back`, `failed`;
  - **forward only**: going backwards or an unknown state is `409`; repeating the current state is a harmless no-op;
  - `success` must carry the version now running, and counts only if it is the expected one;
  - `409` when no update is in progress.

  See the [OTA architecture](../firmware/OTA_ARCHITECTURE.md#per-device-state-machine).
- **`firmware/applied`** (pre-v2.1 clients) is treated as `success` with that version. Without a deployment it sets `firmware_version`, clears `pending_version` and sets `ota_status = applied`, as before.
- **`register`** now records the reported `firmware_version` (it was accepted and dropped before).

## Direct vote/answer endpoints

`POST /api/polls/{id}/vote` and `POST /api/quizzes/{id}/answer`, body `{"device_id": <EspDevice.id>, "selected_option": n}`:
- require `X-API-Key`;
- `device_id` must be a **registered** device (`404` otherwise);
- the option must be in range for the poll or the **current** question (`422`);
- the poll/quiz must be active (`400`);
- one submission per device (`400`).

## Presence snapshot

Returned by `GET /api/classes/{id}/presence` and pushed as the WS `presence` event:
```json
{"class_id": 3, "server_time": "…", "server_time_ms": 1791382516000, "online_count": 2, "total_count": 3,
 "devices": [{"id": 12, "mac_address": "…", "device_name": "imPress C6", "device_type": "c6",
              "student_name": "", "is_connected": true, "online": true, "last_seen": "…",
              "last_seen_ms": 1791382514000, "last_seen_ago_s": 2, "rssi": -61, "battery_pct": 100,
              "student_count": 27, "firmware_version": "1.0.0", "gateway_id": null}]}
```
`devices[0]` is the class gateway; the rest are its relay tree (BFS over `gateway_id`). `online` = `is_connected` and seen within 30 s.

`student_modules` (#40) lists the class's student modules, connected first:
```json
{"id": 4, "device_uid": "1A2B3C4D", "enrollment_number": "ABCDE12345", "state": "connected",
 "gateway_id": 12, "gateway_name": "Room 201", "class_id": 3, "class_code": "PHY101", "class_name": "Physics",
 "section": "A", "battery_pct": 76, "rssi": -58, "first_seen": "…", "last_seen": "…", "last_seen_ago_s": 4}
```
- **`device_uid`:** the firmware's `device_id` (the last four bytes of the module's MAC) in hex, or `""` for older firmware keyed by enrollment.
- **`state`:** `connected`, or `seen` after a leave or 90 s of silence (three missed 30 s heartbeats; the presence sweep pushes a new snapshot).
- **History:** one row per module, updated in place; no location history is kept.

## Changing this contract

1. Keep fields additive. Old firmware ignores unknown response fields but may send old field names.
2. Update the firmware JSON builders (`msg_to_json` in `class_c6/main/main.c`, `wifi_client.c`, `ota.c`) **and** the backend schema in the same PR.
3. For WS command changes, regenerate `firmware/contract/device_ws_frames.json` and update `ws_command.c` (see [decision D5](../design/decisions.md#d5-the-backend--firmware-json-contract-is-a-committed-fixture)).
