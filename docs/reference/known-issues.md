# Known issues and limitations

Verified observations that are **not fixed** on `v2`. Each tracked bug has a GitHub issue with reproduction steps.

## Open bugs

None. Every issue opened so far (#1–#25) is fixed on its own branch and merged into `v2` (see the [changelog](changelog-v2.md)). The ones found after the first audit were resolved like this:

| Issue | Resolution |
|---|---|
| [#19](https://github.com/Kush-Kelaiya22/imPress/issues/19) class takeover via join code | joining adds **co-faculty**; the primary teacher is never replaced |
| [#20](https://github.com/Kush-Kelaiya22/imPress/issues/20) results readable cross-class | quiz/poll details and results require class access |
| [#21](https://github.com/Kush-Kelaiya22/imPress/issues/21) co-faculty couldn't run quizzes | quizzes and polls share the class access rule |
| [#22](https://github.com/Kush-Kelaiya22/imPress/issues/22) `correct_option` unchecked | validated against the number of options (422) |
| [#23](https://github.com/Kush-Kelaiya22/imPress/issues/23) missing Python deps showed as 180 test failures | runner checks each suite's requirements first; one FAIL with the install command |
| [#24](https://github.com/Kush-Kelaiya22/imPress/issues/24) idf/frontend suites looked frozen; Ctrl-C traceback | live progress / CI heartbeat, clean Ctrl-C (exit 130), `--timeout`, `docker run --init` |
| [#25](https://github.com/Kush-Kelaiya22/imPress/issues/25) backend tests took 3m22s, ~160 SAWarnings | bcrypt cost 4 in tests, DB reset by file deletion: ~18 s, no warnings |

## Limitations by design or pending decisions

| Area | Limitation | Mitigation / next step |
|---|---|---|
| OTA | Images are **not signed**; download over plain HTTP. | Enable signed apps / Secure Boot v2 + TLS ([OTA guide](../guides/ota-updates.md#signing-images)). |
| OTA | Only the S3 has an OTA client; the C6 and students update over serial. | Port `ota.c` (minus the Wi-Fi hop) to the C6. |
| Device auth | One shared `DEVICE_API_KEY` for every gateway. | Per-device keys with rotation/revocation. |
| Firmware transport | The C6 uses `http://` and `ws://`. | `cert_pem` + `https`/`wss` once the server has TLS. |
| Mesh security | ESP-NOW frames are unauthenticated; a rogue device can claim any enrollment number. | Per-class key + HMAC over frames ([security model](../design/security-model.md)). |
| Mesh frame size | `MSG_MAX_SIZE` (246) + 6-byte header = 252 > ESP-NOW v1's 250. Every message actually sent is ≤ 220 bytes. | Cap mesh payloads at 238, or require ESP-NOW v2. |
| SPI link | No flow control: an exchange the S3 clocks while the C6 has no slot armed (e.g. during a 10 s HTTP POST) is lost. | A "slot armed" handshake, or let the C6 re-arm from a dedicated task. |
| Backend scale | One process (in-memory WS rooms), SQLite single writer. Migrations are an in-repo runner (`migrations.py`), SQLite-specific. | Redis pub/sub for WS; PostgreSQL would need its migrations ported (or Alembic). |
| Fire-and-forget tasks | Presence pushes are untracked `create_task`s; dropped on shutdown. | Harmless today (the next heartbeat re-pushes); track them if they become important. |
| Student battery | `battery_pct` is hard-coded to 100 on student modules. | Read the ADC. |
| React UI | `Classes` page creates classes with a name only; the API also requires `code` (→ 422). | Use the vanilla admin UI, or add a code field. |
| Git history | Databases with user/session data were committed before v2. | Purge with `git filter-repo` ([deployment](../guides/deployment.md#4-go-live-checklist)). |

## Pre-existing compiler warnings

| File | Warning |
|---|---|
| `firmware/class_c6/main/wifi_client.c` | unused `s_adc`, `s_adc_ready` (when `BATTERY_ADC_EN=n`) |
| `firmware/class_s3/main/config.c` | unused function `_nvs_write_str` |
| `firmware/student/main/mesh_espnow.c` | unused variable `s_student_id` |

## Not yet verified on hardware

The v2 firmware fixes are verified by host tests (ASan/UBSan against real sources) and real ESP-IDF v6.1 builds, **not** yet on boards. Recommended acceptance run: a 2-hour classroom soak with `esp_reset_reason()` logged at boot, `CONFIG_HEAP_POISONING_COMPREHENSIVE=y` on the C6, and a quiz every few minutes.
