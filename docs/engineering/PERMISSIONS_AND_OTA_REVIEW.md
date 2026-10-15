# Permissions and OTA review (v2.2)

Audit step 6 of the v2.2 security audit ([#207](https://github.com/Kush-Kelaiya22/imPress/issues/207)): confirm that every route's permission is intended and tested, and that the OTA path works end to end in software. Done by reading the generated route matrix by hand (not just regenerating the snapshot), then running the OTA suites. **Software evidence only**: board-level OTA is tracked in #88, #89, #164 and #175.

## Method

`backend/tests/test_route_matrix.py` records the HTTP status of every route for five callers: anonymous, a teacher who owns the class, a teacher who does not, an admin and a super admin. The snapshot is `backend/tests/fixtures/route_matrix.json` (142 routes). For this review each row was read against the intended permission in [authorization](../design/authorization.md).

## Result

| Area | Finding | Outcome |
|---|---|---|
| Anonymous | every route is `401`, except the deliberately public ones: sign-in, `GET /api/system/status`, `GET /api/system/signing-key`, `POST /api/system/csp-report`, the CSV templates, and the device-key routes (which answer `422` without their key) | as intended |
| Class routes (quizzes, polls, results, presence, exceptions, activate) | owner `200`, other teacher `403`, admin `200` | as intended |
| Administration (users, deployments, firmware, modules, test mode, system) | teachers `403`; admin where `users.manage`, `devices.manage`, `firmware.*` apply; test mode, approvals, policy-clear and role changes super admin only | as intended |
| New in v2.2: approvals | super admin only (`users.assign_role`); admins and teachers `403` | as intended |
| New in v2.2: `GET /api/admin/system/policy` | admins and super admins may read it (`audit.read`); nobody can write it: there is no write route | as intended |
| `students/summary`, `students/{id}/participation`, `quizzes/overview` | scoped to the caller's classes inside the handler (a teacher with no classes gets an empty result, not an error) | as intended |
| **`PUT` and `DELETE /api/students/{id}`** | **any teacher could edit or deactivate any student in the institution** (200 for a teacher unrelated to the student) | **defect, fixed**: now `403 STUDENT_OUT_OF_SCOPE` outside the student scope |
| **`GET /api/students/` and `/{id}`** | **any teacher could read every student's e-mail and phone** | **defect, fixed**: contact details are returned empty outside the scope; name, number and programme stay visible so a teacher can still find a student to enrol |
| `student.update` activity entries | carry the new values (name, e-mail, phone) | kept in the database log (scrubbed when the student is erased); never copied to the external audit trail |

The fix is in `services/records.student_scope` with tests in `backend/tests/test_student_scope.py`; the matrix snapshot now shows `403` for the unrelated teacher.

**Judgement calls left as they are** (a decision, not a defect): a teacher may *find* any student by name or number, because enrolling a student requires it; any signed-in staff member can read the list of courses; an administrator who is not a super admin may run *Verify now* and acknowledge a Degraded flag (accepting a changed database still needs a second super admin).

## OTA path, in software

| Step | Where it is tested | Result |
|---|---|---|
| Upload: image parsed, chip, version and integrity checked; foreign or corrupt images refused | `test_firmware_registry`, `test_firmware_upload` | pass |
| Signed images: signature verified against the site key; unsigned refused when a key is set | `test_firmware_signing`, `test_trusted_installer` | pass |
| Qualification: analysis and OTA-client simulation; a null or failed stage never counts as a pass | `test_qualification`, `test_trusted_installer` | pass |
| Approval: separation of uploader and approver; refused without qualification | `test_trusted_installer` | pass |
| Offer and download gating: an image is offered and served only if approved and qualified for that exact image | `test_ota_download_gating` | pass |
| Deployment engine: canary, batches, concurrency, retries, timeouts, pause on failure, resume, cancel | `test_deployments`, UI `test_deployments` | pass |
| Maintenance windows: no update during a class, unknown timetable fails closed | `test_maintenance_windows` | pass |
| Results and rollback reporting: success, failure, `rolled_back` | `test_ota_results`, `test_e2e_ota` | pass |
| Student-module inventory and per-family firmware views | `test_student_modules`, UI `test_firmware_tabs`, `test_student_modules` | pass |
| C host tests (protocol, OTA logic) with AddressSanitizer and UBSan | `run_tests.py -s host` | pass (56 tests) |

## What is not covered

- **Exact-image emulation** of the uploaded C6 and S3 binaries is not implemented ([#176](https://github.com/Kush-Kelaiya22/imPress/issues/176)): the qualification's emulator stage reports *not run*, which is never treated as a pass.
- **Anything on real boards**: reboot and health check, the 120 s watchdog rollback, power loss mid-update, the S3 hop, TLS and signed OTA on silicon.
- **Student-module OTA over ESP-NOW** ([#130](https://github.com/Kush-Kelaiya22/imPress/issues/130)) and **authenticated mesh frames** ([#187](https://github.com/Kush-Kelaiya22/imPress/issues/187)) need firmware changes and are outside this round.
