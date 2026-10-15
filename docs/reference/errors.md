# Error reference

Generated from `backend/impress.errors.json` by `python -m app.errors`; do not edit by hand. Every error response carries `error.code` and the `X-Impress-Error` header; the console explains one with `errors CODE`.

## Http

Generic HTTP outcomes, used when a route gives no more specific code.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `BAD_REQUEST` | 400 | **The request could not be understood.** The request was malformed or a value was not acceptable. | Read the message, correct the request and send it again. |
| `UNAUTHENTICATED` | 401 | **Not signed in.** The request carries no valid session or token, or the session ended (idle limit, hard limit, signed out, server restarted: 1PSID). | Sign in again. |
| `FORBIDDEN` | 403 | **Not allowed.** You are signed in, but your role does not hold the permission this needs. | Ask an administrator, or use an account with the right role. |
| `NOT_FOUND` | 404 | **Not found.** The thing asked for does not exist, or you may not know that it exists. | Check the identifier. |
| `METHOD_NOT_ALLOWED` | 405 | **Method not allowed.** The route exists, but not for this HTTP method. | Use the method the API reference lists. |
| `CONFLICT` | 409 | **Conflict with the current state.** The request cannot be done in the state things are in (a duplicate, or someone else changed it first). | Reload and try again. |
| `GONE` | 410 | **No longer available.** It existed and was removed (for example a one-time link that was used). | Request it again. |
| `PAYLOAD_TOO_LARGE` | 413 | **Too large.** An upload or request body is larger than the limit. | Send less data, or split it. |
| `VALIDATION_FAILED` | 422 | **A value is not valid.** A field is missing, has the wrong type or is outside its allowed range. `detail` lists each field. | Correct the listed fields. |
| `RATE_LIMITED` | 429 | **Too many requests.** Too many attempts in a short time (sign-in, step-up, an unusually busy client). | Wait for the time in the Retry-After header. |
| `INTERNAL_ERROR` | 500 | **Something went wrong inside imPress.** An unexpected fault. Nothing was partly saved: database work is transactional. The server log has the trace under the reference shown. | Retry once; if it repeats, give the reference to whoever runs the server. |
| `NOT_IMPLEMENTED` | 501 | **Not implemented.** The server does not support what was asked. | Use a supported operation. |
| `SERVICE_UNAVAILABLE` | 503 | **Temporarily unavailable.** The server cannot serve this right now (start-up checks, a lock-down, the database busy). | Retry in a few seconds. |

## Authentication

Signing in and out, passwords and sessions.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `INVALID_CREDENTIALS` | 401 | **Wrong username or password.** The pair does not match an account. The response never says which one is wrong. | Check both; after several failures there is a wait (TOO_MANY_ATTEMPTS). |
| `TOO_MANY_ATTEMPTS` | 429 | **Too many failed sign-ins.** The username or the client address has failed too often in 15 minutes; the wait doubles with each failure (no permanent lock-out). | Wait the number of seconds in Retry-After. |
| `ACCOUNT_DISABLED` | 403 | **Account is disabled.** An administrator disabled this account. | Ask an administrator to enable it. |
| `ALREADY_SIGNED_IN` | 409 | **Already signed in on another device.** One device per account: another live session exists. The attempt is flagged and administrators are told. | Sign out on the other device, wait for it to expire, or ask a super admin to end sessions. |
| `PASSWORD_CHANGE_REQUIRED` | 403 | **Choose your own password first.** The account has temporary credentials (pending set-up); only the first-sign-in steps are allowed. | Complete the welcome set-up. |
| `PASSWORD_TOO_WEAK` | 422 | **That password is not acceptable.** It breaks the password rule for the role (length, upper and lower case, a number, a special character, not common, not the username). | Choose a stronger password; the strength meter shows what is missing. |
| `SESSION_EXPIRED` | 401 | **The session ended.** Idle limit (15 minutes, 60 for faculty in class), the 6-hour hard limit, a sign-out, a role change or a server restart ended it. | Sign in again. |
| `HTTPS_REQUIRED` | 403 | **Use HTTPS.** Staff traffic must arrive over HTTPS unless the client is on the server itself (REQUIRE_HTTPS). | Use the https:// address. |

## Authorization

Who may do what.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `FORBIDDEN_ROLE` | 403 | **Only a super admin can change roles.** Granting or removing an administrative role needs users.assign_role. | Ask a super admin. |
| `FORBIDDEN_TARGET` | 403 | **Only a super admin can manage a super admin.** Administrators cannot touch super admin accounts. | Ask a super admin. |
| `PROTECTED_ACCOUNT` | 403 | **A protected account.** The default super admin is managed by root: it cannot be deleted, demoted, deactivated or have its password reset through the API. | Root uses the console (password reset). |
| `SELF_LOCKOUT` | 403 | **You cannot do that to your own account.** Deactivating, deleting or demoting yourself would lock you out. | Ask another administrator. |
| `SUPER_ADMIN_VIA_CONSOLE` | 403 | **Super admins are created in the console.** The web app and the API cannot create a super admin. | Root runs `superadmin create USER` in the console. |
| `STUDENT_OUT_OF_SCOPE` | 403 | **Not a student you teach.** Faculty see and change only students enrolled in their classes. | Ask an administrator. |
| `DB_WRITE_REFUSED` | 403 | **The database gateway refused the write.** The signed-in principal may not write that table. It is logged and administrators are alerted. | Use the proper feature; if it was legitimate, an administrator should look at the activity log. |
| `LAST_SUPER_ADMIN` | 409 | **That would leave no active super admin.** The database itself refuses to remove the last active super admin. | Create or reactivate another super admin first. |

## Two step verification

TOTP second factor for super admins' dangerous actions.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `MFA_CODE_REQUIRED` | 403 | **A code is needed.** Two-step verification applies to this account: enter the authenticator code (or a recovery code) as well as the password. | Send `code`. |
| `MFA_CODE_WRONG` | 403 | **That code is not right.** The code does not match the secret, or the phone's clock is off. | Use the newest code; check the phone's time. |
| `MFA_ENROLLED` | 409 | **Already set up.** Turn it off before setting it up again. | Use disable first. |
| `MFA_NOT_PENDING` | 409 | **No set-up in progress.** Finish needs a started set-up. | Call setup first. |
| `MFA_ENROLMENT_REQUIRED` | 403 | **Set up two-step verification first.** Policy dual_control.mfa_required: a super admin who has not enrolled cannot request or approve. | Settings > Security > Set up. |
| `MFA_REQUIRED_BY_POLICY` | 403 | **It cannot be turned off.** Policy dual_control.mfa_required makes it mandatory. | Only root's policy can change this. |

## Dual control

Requests that need a second super admin.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `APPROVAL_REQUIRED` | 403 | **A second super admin's approval is needed.** This action needs an approved request first (policy dual_control.enabled). | Request it on the System page; another super admin approves. |
| `APPROVAL_MISMATCH` | 403 | **That approval is not for this action.** The approval is for a different action or parameters, or was requested by someone else. | Request a new one for this exact action. |
| `NOT_APPROVED` | 409 | **Not approved yet.** The request is still pending or was denied. | Wait for approval. |
| `NOT_YET` | 409 | **The delay has not passed.** Policy dual_control.delay_minutes holds an approved action back. | Retry after the time shown. |
| `EXPIRED` | 409 | **The approval expired.** It was not used within dual_control.expiry_minutes. | Request it again. |
| `NOT_PENDING` | 409 | **Already decided.** The request is already approved, denied or executed. | Nothing to do. |
| `SELF_APPROVAL` | 403 | **A different super admin must approve.** You cannot approve your own request unless you are the only active super admin and policy allows it. | Ask another super admin. |
| `STEP_UP_FAILED` | 403 | **Password or code not correct.** The re-entered password, the authenticator code, or an already used code was wrong. Counts towards the lock-out. | Try again. |
| `STEP_UP_LOCKED` | 429 | **Step-up is locked for a while.** Five wrong passwords or codes in 15 minutes. | Wait 15 minutes. |
| `UNKNOWN_ACTION` | 422 | **Unknown action.** The action name is not one dual control knows. | Use one of the listed actions. |
| `UNKNOWN_BACKUP` | 422 | **Choose an existing backup.** The backup named in the request does not exist. | List the backups first. |
| `POLICY_DISABLED` | 403 | **Switched off by root's policy.** A policy flag (for example system.reset_everything_allowed) forbids this. | Only root's policy can change it. |
| `CONFIRM` | 422 | **Type the confirmation.** A dangerous action needs the exact phrase or name typed. | Type it as shown. |

## Policy and flags

Global policy control, launch flags and features.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `FEATURE_DISABLED` | 403 | **Switched off.** A feature (or OTA) was switched off by root or an administrator. | Ask who switched it off; root's launch flags cannot be undone from the web. |
| `FEATURE_LOCKED` | 403 | **Locked at a higher level.** Whoever set the feature last has more authority than you, or locked it. | Ask someone with that authority. |
| `POLICY_UNKNOWN_FLAG` | 422 | **Unknown policy flag.** No flag has that name. | `policy show` lists them. |
| `POLICY_BAD_VALUE` | 422 | **Not a valid value for that flag.** The value has the wrong type or is outside the flag's range. | See docs/reference/flags.md. |
| `POLICY_FORBIDDEN` | 403 | **You may not change this flag.** Only root changes policy flags; super admins may change the few marked operational; administrators and faculty none. | Ask root. |
| `POLICY_LOOSENING` | 403 | **That would loosen the hardened profile.** In the hardened profile an override may only make a flag safer. | Sign a policy file with scripts/gpc.py. |
| `POLICY_CONFLICT` | 409 | **Flags that cannot work together.** Two or more flags contradict each other. At start-up this stops imPress before anything else. | Change one of the named flags. |
| `POLICY_TAMPERED` | 500 | **The policy store was edited outside imPress.** The sealed policy file did not verify. It was set aside and the defaults restored; an alert and an audit entry were made. | Change policy through the console or the System page only. |
| `POLICY_FILE_INVALID` | 500 | **A signed policy file was refused.** Bad signature, wrong key, an old serial, or an unknown flag. Never half-applied. | Re-sign it with scripts/gpc.py. |
| `FLAGS_FILE_INVALID` | 500 | **The flags file cannot be applied.** impress.flags.json is not valid JSON, names an unknown flag, or has a wrong value. imPress does not start. | `python -m app.flagsfile check` names the flag. |
| `FLAG_IS_POLICY` | 422 | **That is a policy flag.** Security and integrity flags are kept in the sealed policy store, not in the flags file. | Use `policy set NAME VALUE`. |

## Root

The root screen and console.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `ROOT_PASSWORD_REQUIRED` | 403 | **Root's password is needed.** This is a sensitive root action (rehash, policy change, reset, ...). | Enter root's password when asked. |
| `ROOT_PASSWORD_WRONG` | 403 | **Root's password is not correct.** Wrong password. Repeated failures slow down. | Try again. |
| `ROOT_CONSOLE_CLOSED` | 403 | **The separate root console is closed here.** Policy root.allow_access is off (TrustedInstaller closes it in a container). | Use the console on the container's own screen. |
| `ROOT_COMMAND_FAILED` | 400 | **A console command failed.** The command's message says why; nothing was half-done. | Read the message; `help COMMAND`. |
| `ROOT_UNKNOWN_COMMAND` | 400 | **Unknown console command.** No such command. | `help` lists them. |

## Database integrity

Seals, verification, backups and test mode.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `DB_NOT_VERIFIED` | 409 | **The database does not verify.** A seal does not match: something changed the database outside imPress. It is Degraded. | Resolve the Degraded state first (System page). |
| `DB_DEGRADED` | 503 | **The database is Degraded.** An automatic restore or an unresolved alarm is pending acknowledgement. | A super admin acknowledges it on the System page. |
| `DB_LOCKED` | 503 | **The database is busy.** Another process holds a write lock longer than the busy timeout; nothing was saved. | Retry. |
| `DB_SEAL_KEY_CHANGED` | 500 | **The sealing key changed.** IMPRESS_JWT_SECRET was rotated; the database is re-sealed as it is and an alert is raised. | Check the rotation was intended. |
| `BACKUP_DOES_NOT_VERIFY` | 409 | **That backup does not verify.** The copy's seals do not match: it is never accepted. | Choose another backup. |
| `BACKUP_UNREADABLE` | 409 | **That backup cannot be used.** SQLite cannot read it, or its own integrity check failed. | Choose another backup. |
| `NO_BACKUP` | 404 | **No such backup.** The id does not exist. | List the backups. |
| `NOT_DELETABLE` | 409 | **Only saved backups can be deleted.** Automatic copies manage themselves. | Delete only the ones you saved. |
| `BAD_NAME` | 422 | **That name is not allowed.** 1-48 letters, digits, spaces, dot, underscore, dash. | Choose another name. |
| `NAME_TAKEN` | 409 | **That name exists already.** A backup or dataset has that name. | Choose another name. |
| `TEST_MODE` | 409 | **No backups in test mode.** Backups are neither made nor restored while test mode is on. | Turn test mode off first. |
| `TEST_MODE_OFF` | 409 | **Test mode is off.** Test data routes need test mode. | A super admin turns test mode on. |
| `TEST_MODE_FORCED` | 403 | **Test mode was enabled by root.** It cannot be turned off from the web app. | Root removes `test_mode.forced`. |
| `ALREADY_ON` | 409 | **Test mode is already on.** Nothing to do: test mode is already in the state you asked for. | Nothing: reload the page. |
| `ALREADY_OFF` | 409 | **Test mode is not on.** Nothing to do: test mode is already in the state you asked for. | Nothing: reload the page. |
| `SNAPSHOT_CHANGED` | 500 | **The saved real database was changed.** Its checksum no longer matches; test mode stays on. | Restore the real data from a backup. |
| `RESTORE_FAILED` | 500 | **The restore does not verify.** The real database was put back but fails verification: Degraded. | See the integrity panel. |
| `NO_DATASET` | 404 | **No such saved dataset.** The name does not exist. | List the datasets. |
| `NO_PENDING` | 404 | **No such test data.** Nothing waits under that id. | List pending test data. |
| `INVALID_ROWS` | 422 | **Rows are not valid.** Per-cell errors are listed; nothing was imported (all or nothing). | Fix the listed cells. |

## Integrity protection

IIPS: the program's own files, and the device they belong to.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `INTEGRITY_VIOLATION` | 503 | **imPress is disabled by Root.** The program's files differ from the reference (changed, added, removed or moved). | Restore the files, or root restarts with --rehash (root's password). |
| `IIPS_DEVICE_MISMATCH` | 503 | **The files were made on another device.** The reference was sealed for a different machine: the code or its reference was copied. | Root re-hashes on this machine (root's password). |
| `IIPS_BASELINE_EDITED` | 503 | **The integrity reference was edited.** Its seal does not verify. | Root re-hashes (root's password). |
| `IIPS_BYPASSED` | 200 | **Integrity protection is off.** Started with --bypass-iips or iips.enabled=false: every page shows a warning. | Remove the flag. |
| `LOCKED_DOWN` | 503 | **Locked: the host is being verified.** TrustedInstaller has not finished, or a critical requirement fails. | `requirements` shows the failing check. |
| `MANIFEST_MISMATCH` | 500 | **The code differs from the signed manifest.** A file does not match MANIFEST.json (policy code.verify_manifest). | Reinstall, or root signs a new manifest. |

## Accounts

Users, trash and imports.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `USER_EXISTS` | 409 | **That username or email is taken.** Usernames and emails are unique. | Choose another. |
| `USER_NOT_FOUND` | 404 | **No such account.** The id or name does not exist. | List accounts. |
| `TRASH_EXPIRED` | 410 | **Past the 30 days.** A deleted account can be restored for 30 days only. | Create it again. |
| `IMPORT_INVALID` | 422 | **The CSV could not be imported.** A header is missing or a row is invalid; nothing was imported. | Fix and upload again. |

## Classroom

Classes, courses, students, quizzes and polls.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `CLASS_NOT_FOUND` | 404 | **No such class.** It does not exist, or you have no access. | Check the id / classroom code. |
| `CLASS_CODE_TAKEN` | 409 | **Class code in use.** Class codes are unique. | Choose another. |
| `CLASS_NOT_ACTIVE` | 409 | **The class is not active.** Quizzes, polls and device traffic need an activated class. | Activate it. |
| `STUDENT_NOT_FOUND` | 404 | **No such student.** The id or roll number does not exist. | Check it. |
| `ROLL_NUMBER_TAKEN` | 409 | **Roll number in use.** Roll numbers are unique. | Check it. |
| `QUIZ_NOT_FOUND` | 404 | **No such quiz.** Does not exist or not yours. | Check the id. |
| `QUIZ_STATE` | 409 | **The quiz is not in that state.** For example starting a quiz that is already running or finished. | Reload. |
| `POLL_STATE` | 409 | **The poll is not in that state.** For example voting on a closed poll. | Reload. |
| `ALREADY_ANSWERED` | 409 | **Already answered.** One press is one stored answer. | - |
| `SCHEDULE_UNKNOWN` | 503 | **The timetable is unknown or stale.** Room-occupancy questions fail closed when the timetable is older than SCHEDULE_MAX_AGE_HOURS. | Re-import the timetable. |

## Devices and firmware

Gateways, hubs, student modules, firmware and OTA.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `DEVICE_KEY_INVALID` | 401 | **Bad device key.** A device presented a wrong or unknown key. | Re-register the device. |
| `DEVICE_KEYS_REQUIRED` | 403 | **The shared device key may only enrol.** Policy device.keys_required. | Re-enrol the device to get its own key. |
| `DEVICE_HTTPS_ONLY` | 403 | **Devices must use TLS.** Policy device.https_required. | Flash firmware built with BACKEND_TLS. |
| `FIRMWARE_NOT_SIGNED` | 422 | **Image is not signed with the site key.** A site signing key is configured and the image lacks a valid signature. | Sign it (scripts/firmware_key.sh). |
| `NOT_QUALIFIED` | 409 | **TrustedInstaller has not qualified this image.** Only qualified images can be approved or deployed. | Run qualification. |
| `SEPARATION_OF_DUTIES` | 403 | **The uploader cannot approve.** Another administrator must approve (unless FIRMWARE_SINGLE_APPROVER). | Ask another administrator. |
| `SOURCE_MANAGED` | 409 | **Managed by an authoritative source.** The timetable source owns that data. | Change it at the source. |
| `OTA_DISABLED` | 403 | **Over-the-air updates are off.** Policy ota.enabled is false (--no-ota). | Root turns it on. |
| `OTA_WINDOW_CLOSED` | 409 | **Outside the maintenance window.** S3/C6 updates wait for classroom downtime unless a super admin overrides. | Wait, or override. |
| `DEPLOYMENT_STATE` | 409 | **The deployment is not in that state.** For example pausing a finished deployment. | Reload. |

## Transport and traffic

Network-level protections.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `TRAFFIC_ALERT` | 200 | **Unusual traffic.** A rate limit per endpoint, address or account was exceeded; administrators are alerted. Nobody is blocked. | Check the alert on the System page. |
| `WS_UNAUTHORIZED` | 401 | **WebSocket refused.** A live connection without a valid token or device key (close code 4401). | Reconnect with credentials. |
| `WS_CLASS_FORBIDDEN` | 403 | **WebSocket not allowed for that class.** A live connection is bound to classes you may access (close code 4403). | Connect to your own class. |

## Startup

Why imPress did not start. Exit codes of `python -m app.serve`.

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `EXIT_2_CONFIG` | - | **Exit code 2: configuration refused.** A flag, the flags file or the policy cannot be applied; a conflict between flags; default secrets outside debug mode; the hardened profile below its floor. | Read the message printed before exit; fix and restart. |
| `EXIT_3_INTEGRITY` | - | **Exit code 3: integrity lock.** The program's files changed, were copied from another device, or the reference was edited. | Root restarts with --rehash and enters root's password. |
| `EXIT_4_CONSOLE_CLOSED` | - | **Exit code 4: the console is closed.** Policy root.allow_access is off here. | Use the console on the container's screen. |
| `FLAG_CONFLICT` | - | **Flags that conflict.** Two or more flags contradict each other. This is checked before anything else; nothing else is verified or started. | Change one of the named flags. |
| `HARDENED_FLOOR` | - | **Below the hardened floor.** The hardened profile refuses to start with debug on, default secrets, no HTTPS, an unsigned-firmware allowance, no audit sink and so on. | Fix the listed items or run the standard profile. |
| `DEFAULT_SECRETS` | - | **Default secrets.** IMPRESS_JWT_SECRET or IMPRESS_DEVICE_API_KEY is still the public default. | Run the launcher (it generates them) or set your own. |
| `PORT_IN_USE` | - | **Port 8000 is busy.** Another process listens there. | The launcher shows it and asks before stopping it. |
| `MIGRATION_FAILED` | - | **A schema migration could not apply.** Start-up stops rather than run on a half-migrated database; a copy was made first. | Restore the copy named in the log. |
| `HOST_REQUIREMENT` | - | **The host does not meet a requirement.** Python, SQLite or a writable data folder are critical; memory, disk, cores switch features off. | `requirements` shows the check. |

## Hardware

Faults reported by gateways, hubs and student modules (shown on the Devices page and in diagnostics).

| Code | HTTP | Meaning | What to do |
|---|---|---|---|
| `HW_LINK_LOST` | - | **S3-C6 link lost.** The SPI link between hub and gateway stopped answering. | Check wiring and power; the gateway reports reset reasons. |
| `HW_BROWNOUT` | - | **Brown-out reset.** The supply dipped below the brown-out threshold. | Use a better supply or cable. |
| `HW_WATCHDOG` | - | **Watchdog reset.** The firmware did not feed the watchdog. | Report the boot counter and reset reason. |
| `HW_OTA_ROLLBACK` | - | **An OTA image was rolled back.** The new image did not report healthy within 120 s. | Check the image; try again. |
| `HW_MESH_FRAME_TOO_BIG` | - | **Mesh frame over the payload budget.** ESP-NOW payload limit (238 bytes) exceeded. | Shorten the message. |
| `HW_FLASH_FAILED` | - | **Flashing failed.** esptool could not write the image (port busy, wrong chip, a boot-mode button). | Hold BOOT, check the port with `ports`, retry. |
