# Security review (v2.1)

A review of the v2.1 changes against the brief's checklist: access control, file uploads and firmware. The threat model itself is in the [security model](../design/security-model.md); this page records what was checked and the evidence. Reviewed 2026-10-09 on `varun/v2.1`.

## Access control

| Item | Result | Evidence |
|---|---|---|
| Every route refuses an unauthenticated caller, except an explicit public list | ✅ | `backend/tests/test_route_guards.py` sends a request to every registered route without credentials. A route that forgets its guard fails the test; this was mutation-checked by removing `require_admin` from one route. Public routes: login and the two CSV templates. |
| Role-based authorization on the server | ✅ | `require_admin` / `require_teacher_or_admin` on every admin, firmware, deployment, import and inventory route; `test_role_escalation.py`, `test_admin_users.py`, `test_cofaculty_access.py`, `test_results_access.py` |
| Session handling | ✅ (from `v2`) | opaque tokens stored hashed, idle and absolute expiry, revocation: `test_auth_sessions.py`, `test_session_token_storage.py` |
| WebSocket authentication | ✅ (from `v2`) | teacher session token or device key; role-targeted broadcasts: `test_ws_auth.py` |
| Device authentication | ⚠️ shared key | every device route needs `X-API-Key`, and a wrong key is refused (`test_device_routes_reject_a_wrong_key`). All devices share **one** key: [#66](https://github.com/Kush-Kelaiya22/imPress/issues/66) |
| CSV import permissions | ✅ | question import needs class access; course and section import is admin only (`test_class_import.py::test_admin_only`) |
| Firmware upload, approval, deprecation, deletion | ✅ | admin only (`test_firmware_registry.py::test_admin_only`, `test_firmware_manager.py::test_admin_only`) |
| OTA deployment and rollback | ✅ | admin only (`test_deployments.py::test_admin_only`); a downgrade needs an explicit confirmation (`test_rollback_needs_explicit_confirmation`) |
| Student module inventory and diagnostics | ✅ | the inventory list is admin only; teachers see their own classes' modules through the presence snapshot, under the class-access rule (`test_student_modules.py::test_access_is_scoped`). Diagnostics are read-only and add no remote control. |
| Hidden UI controls are not the enforcement | ✅ | every check above is enforced server-side; the route guard test calls the API directly |

## File uploads

| Item | Firmware images | CSV files |
|---|---|---|
| Size limit | the largest app slot (4 MB): 413 | 1 MB and 500 rows: 413 / 422 |
| Content validation | parsed as an ESP-IDF app image (magic, chip ID, app descriptor, imPress project, semver version, appended SHA-256, slot size): 422 with the reason | strict header (unknown columns rejected), per-row validation, all-or-nothing commit |
| Storage path | `<FIRMWARE_DIR>/<sha256>.bin`, named from the content, never from user input, so path traversal is impossible | not stored |
| Access to stored files | downloads only through the device API, only for the version pushed to that device (`test_ota_download_gating.py`) | — |
| Error messages | the reason (wrong chip, bad version…), no internals | per-row reasons |
| Formula injection on export | — | exported cells that start with `=`, `+`, `-` or `@` are escaped (`test_export_round_trips_and_escapes_formulas`) |

## Firmware

| Item | Result |
|---|---|
| Compatibility checks | ✅ an image is registered for exactly one target (chip and project from the image) and offered only to devices of that type; the device's `esp_ota_end` rejects a foreign chip |
| Integrity | ✅ the SHA-256 is checked at upload and given to the device with the offer; the gateway compares it before installing (#34) and the bootloader checks the appended hash |
| **Authenticity** | ❌ **images are not signed.** A device installs any image that passes the integrity checks. Tracked in [#66](https://github.com/Kush-Kelaiya22/imPress/issues/66); the procedure is in the [OTA guide](../guides/ota-updates.md#signing-images) |
| Transport | ⚠️ device traffic is plain HTTP; TLS is recommended at the reverse proxy for browsers, and for devices in [#66](https://github.com/Kush-Kelaiya22/imPress/issues/66) |
| Replay and stale offers | ✅ a device is offered only its deployment's version; the state machine is forward-only, so a replayed or out-of-order report is ignored (`test_progress_is_forward_only_and_duplicates_are_harmless`); success needs the expected version |
| Downgrade policy | ✅ refused unless the operator confirms (`allow_downgrade`); recorded as a rollback deployment |
| Audit log | ✅ uploads, approvals, deprecations, deployments, prompts and device results are written to the activity log and shown in the image's history |
| Existing protections weakened | none. Secure boot and flash encryption were not enabled before and are not disabled now |

## Findings

| # | Finding | Severity | Status |
|---|---|---|---|
| S1 | Firmware images are not signed; device traffic is unencrypted; one shared device key | high for production | [#66](https://github.com/Kush-Kelaiya22/imPress/issues/66), open |
| S2 | A database error on commit escaped as a 500 with a stack trace in the log | low | fixed in #64 (503, nothing saved) |
| S3 | Databases with user and session data were committed to git history before `v2` | high if the repository is published | documented in the [go-live checklist](../guides/deployment.md#4-go-live-checklist); purging history needs a force-push, which only the owners may do |

No exploit-level detail is recorded here or in the public issues.
