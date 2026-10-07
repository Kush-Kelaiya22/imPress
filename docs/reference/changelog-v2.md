# Changelog: v2

`v2` = `main` + every fix (#1–#22) from the October 2026 repository audit, plus a full test suite, CI and these docs. Each fix lives on its own `fix/*` branch, merged into `v2` with `--no-ff`. `main` is unchanged. Every GitHub issue has a resolution comment with before/after test output and a safety analysis.

## Fixes

| Issue | Severity | Area | Branch | Change | Regression tests |
|---|---|---|---|---|---|
| [#1](https://github.com/Kush-Kelaiya22/imPress/issues/1) | critical | C6 firmware | `fix/c6-spi-slave-dangling-descriptor` | SPI slave descriptor made static; reap before re-arm; one transaction in flight. **Root cause of the intermittent C6 resets.** | `class_c6/test_host/test_spi_slave.c` (ASan use-after-return) |
| [#2](https://github.com/Kush-Kelaiya22/imPress/issues/2) | critical | S3 ↔ C6 | `fix/2-spi-batch-record-framing` | Shared `spi_record_write/read`; student messages reach the backend again (were 0/1, 1/N) | `protocol/test_host/test_protocol.c` |
| [#3](https://github.com/Kush-Kelaiya22/imPress/issues/3) | high | backend ↔ C6 ↔ student | `fix/3-device-command-contract` | `event` keys + `time_limit_s`; new `ws_command.c`; `POLL_START` + end events handled on students | `test_device_ws_contract.py` + `test_ws_command.c` (shared fixture) |
| [#4](https://github.com/Kush-Kelaiya22/imPress/issues/4) | high | C6 firmware | `fix/4-c6-batch-single-owner` | cJSON batch owned by `spi2http` only; correct HWM log | `firmware/tests/test_c6_batch_ownership.py` |
| [#5](https://github.com/Kush-Kelaiya22/imPress/issues/5) | medium | C6 firmware | `fix/5-c6-ws-reassign-deferred` | WS restart moved out of its own event handler | `firmware/tests/test_c6_ws_no_self_destroy.py` |
| [#6](https://github.com/Kush-Kelaiya22/imPress/issues/6) | medium | mesh + backend | `fix/6-dedup-mesh-and-batch` | `mesh_msg_id` de-dup on students and root; non-blocking ESP-NOW callback; validated + de-duplicated `/batch` | `test_device_batch_dedup.py`, `test_mesh_dedup.c` (relay-storm sim) |
| [#7](https://github.com/Kush-Kelaiya22/imPress/issues/7) | low | S3 firmware | `fix/7-s3-config-before-mesh` | Config loaded before mesh init; `set_channel` errors logged | `firmware/tests/test_s3_config_before_mesh.py` |
| [#8](https://github.com/Kush-Kelaiya22/imPress/issues/8) | high | backend WS | `fix/8-ws-teacher-session-auth` | Teacher WS validates session tokens; roles recorded; React sends the token | `test_ws_auth.py` |
| [#9](https://github.com/Kush-Kelaiya22/imPress/issues/9) | high | backend security | `fix/9-vote-answer-auth` | Vote/answer need the device key, a registered device, a valid option | `test_vote_answer_auth.py` |
| [#10](https://github.com/Kush-Kelaiya22/imPress/issues/10) | high | backend security | `fix/10-role-escalation` | Closed role set; only super admins grant admin-level roles | `test_role_escalation.py` |
| [#11](https://github.com/Kush-Kelaiya22/imPress/issues/11) | high | backend + C6 security | `fix/11-secure-defaults` | DEBUG off; refuse default secrets; random first admin; CORS allow-list; constant-time key; key in a header | `test_secure_defaults.py`, `test_c6_ws_key_not_logged.py` |
| [#12](https://github.com/Kush-Kelaiya22/imPress/issues/12) | high | repo + backend | `fix/12-untrack-data-hash-only-tokens` | `.gitignore`; DBs untracked; hash-only sessions; legacy raw tokens revoked | `test_session_token_storage.py` |
| [#13](https://github.com/Kush-Kelaiya22/imPress/issues/13) | medium | S3 OTA + backend | `fix/13-ota-rollback-no-noop-reboot` | App rollback + mark-valid; no reboot on a no-op OTA; gated downloads | `test_ota_download_gating.py`, `test_s3_ota_safety.py` |
| [#14](https://github.com/Kush-Kelaiya22/imPress/issues/14) | medium | tooling | `fix/14-ci-and-test-infra` | Test infrastructure + GitHub Actions | `test_api_smoke.py` |
| [#15](https://github.com/Kush-Kelaiya22/imPress/issues/15) | medium | backend | `fix/15-class-create-500` | `ClassCreate` exam dates (`POST /api/classes/` 500) | `test_class_create.py` |
| [#16](https://github.com/Kush-Kelaiya22/imPress/issues/16) | medium | backend | `fix/16-firmware-upload-500` | Firmware upload 500 (`log_activity(None)`); OTA prompt audit-logged | `test_firmware_upload.py` |
| [#17](https://github.com/Kush-Kelaiya22/imPress/issues/17) | high | backend | `fix/17-gateway-autolink-steal` | Only gateways auto-link, and only to classes without one (an S3 OTA hop stole the link) | `test_gateway_autolink.py` |
| [#18](https://github.com/Kush-Kelaiya22/imPress/issues/18) | low | C6 firmware | `fix/18-c6-empty-nvs-default` | An empty NVS value no longer wipes the Kconfig default | `class_c6/test_host/test_c6_config.c` |
| [#19](https://github.com/Kush-Kelaiya22/imPress/issues/19) | high | backend security | `fix/19-class-join-no-takeover` | Joining a class by code adds co-faculty; the owner is never replaced | `test_class_join.py` |
| [#20](https://github.com/Kush-Kelaiya22/imPress/issues/20) | medium | backend security | `fix/20-results-access-check` | Quiz/poll details and results require class access | `test_results_access.py` |
| [#21](https://github.com/Kush-Kelaiya22/imPress/issues/21) | medium | backend | `fix/21-cofaculty-quiz-poll-access` | One access rule for classes, quizzes and polls (co-faculty included) | `test_cofaculty_access.py` |
| [#22](https://github.com/Kush-Kelaiya22/imPress/issues/22) | low | backend | `fix/22-correct-option-range` | `correct_option` validated against the number of options | `test_quiz_correct_option.py` |

## Also in v2

- **Test suite** (see [testing](../guides/testing.md)):
  - 198 backend tests;
  - 14 firmware structural guards;
  - repository/CI/docs consistency checks (`tests/`);
  - 6 host C suites (25 cases) compiling real firmware sources under ASan/UBSan, sharing an in-memory NVS fake (`firmware/test_support`).
- **`run_tests.py`:** one command runs every suite and prints a pass/fail/duration report (also JSON, JUnit and Markdown).
- **CI:** repository checks, backend, firmware structural, firmware host, ESP-IDF v6.1 builds of all three projects (with size reports and firmware artifacts), and a frontend build, behind a single **CI result** gate. Least-privilege permissions, concurrency cancellation and per-job timeouts.
- **Repo hygiene:** categorised `.gitignore`; `.gitattributes` (LF, binaries, vendored components); runtime logs and stray `.pyc` untracked.
- **Docs:** this folder.

## Upgrading from `main`

1. **Backend:** set `IMPRESS_JWT_SECRET` and `IMPRESS_DEVICE_API_KEY` (or `IMPRESS_DEBUG=true` locally). Existing sessions that stored raw tokens are revoked once at startup, so users log in again.
2. **Gateways and hubs:** flash new C6 and S3 images together (the SPI record format and command contract changed in lock-step), and put the new device key in their config/NVS. Flash the S3 **over serial once** for the rollback bootloader.
3. **Students:** flash new student firmware (`POLL_START` handling, mesh de-dup, non-blocking receive).
4. **Data:** classes whose gateway link was stolen before #17 keep it until the C6 re-registers with its `classroom_code`, or an admin re-links it.
