# Launch flags reference

Generated from the flag catalogue by `python -m app.flagsfile docs`; do not edit by hand. How to use the file: [launch flags](../guides/launch-flags.md).

## Feature flags (`impress.flags.json`, editable by hand)

| Flag | Type | Standard | Hardened | What it does |
|---|---|---|---|---|
| `test_mode.allowed` | bool | `true` | `false` | Debug mode and test data (copies of the database) may be used at all. **false = the test-data menu and routes do not exist (the command line's --no-test-mode).** |
| `test_mode.forced` | bool | `false` | `false` | Test mode is forced on by root (launch flag --test-mode) and nobody can turn it off; the default super admin then signs in with a fixed lab password. **Lab use. Same as the command line's --test-mode. Not allowed in the hardened profile. Cannot be true while test_mode.allowed is false.** |
| `ota.enabled` | bool | `true` | `true` | Over-the-air firmware updates exist at all (off with --no-ota): uploads, deployments and pushes are refused and devices are offered nothing. **false = no firmware uploads, deployments or pushes, and devices are offered nothing (--no-ota).** |
| `features.disabled` | str | `""` | `""` | Comma-separated features switched off by root; administrators cannot switch them on (see the System page for the list). **Prefer the "features" section below: it lists every feature by name.** |
| `traffic.monitor` | bool | `true` | `true` | Watch request rates per endpoint, address and account and alert administrators to unusual traffic. |
| `test_mode.export_allowed` | bool | `true` | `false` | Test-data copies may be exported as CSV files. |

## Policy flags (the sealed store: `policy set` in the console, or the System page)

Sealed, recorded with who and when; administrators and faculty can never change them. *Changed by* says who may.

| Flag | Type | Standard | Hardened | Changed by | What it does |
|---|---|---|---|---|---|
| `dual_control.enabled` | bool | `true` | `true` | root | Destructive or baseline-changing actions (accepting the current database state, clearing data) need a second super admin's approval. |
| `dual_control.single_operator_ok` | bool | `true` | `false` | root | Allow the requester to approve their own action when they are the only active super admin. |
| `dual_control.mfa_required` | bool | `false` | `true` | root | Every step of dual control (request, approve, restore a backup) also needs a code from the super admin's authenticator app (TOTP); a super admin who has not set one up cannot take part. A super admin who has set one up is always asked for the code, whatever this says. |
| `dual_control.delay_minutes` | int | `0` | `15` | root | Minutes between an approval and the earliest moment the action may run. |
| `dual_control.expiry_minutes` | int | `240` | `30` | root | Minutes an approval stays usable after its delay has passed. |
| `system.reset_everything_allowed` | bool | `true` | `false` | root | Allow the 'reset everything' clear scope in the web app at all. |
| `audit.sink_path` | str | `""` | `""` | root | Hash-chained, append-only audit file outside the database (put it on a WORM or remote-logged volume). |
| `audit.sink_url` | str | `""` | `""` | root | HTTP(S) endpoint that also receives every audit event, signed with an HMAC (off-host copy). |
| `audit.min_retention_days` | int | `0` | `180` | root | A clear or reset never deletes activity-log entries younger than this many days. |
| `audit.purge_days` | int | `0` | `365` | root | Activity-log entries in the database older than this many days are deleted (0 = never; never sooner than audit.min_retention_days). The external audit sink is not touched. Only a signed policy can change it in the hardened profile. |
| `integrity.forensic_copies` | int | `3` | `10` | super admin | How many copies of a failed database are kept before an automatic restore replaces it. |
| `integrity.before_clear_days` | int | `30` | `14` | super admin | Days the full copy taken before a clear or reset is kept (0 = never deleted). It is your way back, and a copy of the data. |
| `root.allow_access` | bool | `true` | `true` | root | Whether the separate root console may be opened (ssh, docker exec). TrustedInstaller switches it off inside a container: use the console attached to the container instead. |
| `iips.enabled` | bool | `true` | `true` | root | imPress Integrity Protection Service: refuse to start when the program's own files changed since the last baseline. |
| `iips.auto_accept_updates` | bool | `true` | `false` | root | When the program was updated (a different release or git commit than the one the baseline was made from), its new files become the reference by themselves instead of locking imPress. Files edited by hand under the same release still lock it. Off in the hardened profile: root accepts an update with --rehash. |
| `iips.device_binding` | enum (off / warn / enforce) | `"warn"` | `"enforce"` | root | Bind the integrity reference to this machine (its hardware identity: not the address, system version or folder). Code or a reference copied to another machine is flagged: 'warn' alerts, 'enforce' locks imPress until root re-hashes there with root's password. |
| `deadlock_prevention.enabled` | bool | `true` | `true` | root | If no active super admin exists, roll the database back and create a recovery account (global_deadlock_prevention). |
| `backups.restore_requires_approval` | bool | `false` | `true` | root | Restoring a backup needs a second super admin's approval (so only a super admin can request it). |
| `test_mode.pending_ttl_hours` | int | `168` | `24` | super admin | Hours a finished test database waits for a decision before it is deleted (0 = never). |
| `test_mode.dataset_ttl_days` | int | `0` | `30` | super admin | Days a saved test dataset is kept (0 = never). |
| `code.verify_manifest` | enum (off / warn / enforce) | `"warn"` | `"enforce"` | root | Check the server's own files against the root-signed MANIFEST.json at start-up. |
| `device.https_required` | bool | `false` | `true` | root | Gateways and hubs must use HTTPS/WSS (same effect as IMPRESS_DEVICE_HTTPS_ONLY). |
| `device.keys_required` | bool | `false` | `true` | root | The shared device key may only enrol; every device must use its own key (same as IMPRESS_DEVICE_KEYS_REQUIRED). |
| `firmware.signing_required` | bool | `false` | `true` | root | A site firmware signing key must be configured and unsigned images are never accepted. |

## Web-app features

Set `false` under `"features"` to switch one off for everybody (root outranks administrators).

| Feature | Group | What it is |
|---|---|---|
| `search` | Interface | Global search. Search over classes, students, devices, accounts and settings. |
| `notifications` | Interface | Notification tray. The bell with alerts and updates. |
| `tutorial` | Interface | Guided tour. The interactive tour offered on first sign-in and from the Tutorial button. |
| `onboarding` | Interface | Welcome set-up. The first sign-in questions: name, password, theme. |
| `sidebar_collapse` | Interface | Collapsible sidebar. Let people collapse the sidebar to icons. |
| `help_menu` | Interface | Help and documentation. The documentation menu for administrators. |
| `password_meter` | Interface | Password strength meter. The strength bar under password fields. |
| `dashboard_widgets` | Personalization | Dashboard widgets. Editable dashboard: add, remove and move widgets. |
| `personalization` | Personalization | Personalization. Accent colours, date and time formats. |
| `accessibility` | Personalization | Accessibility settings. Colour-vision modes, contrast, motion and text size. |
| `advanced_mode` | Personalization | Advanced mode. Detailed statistics for administrators. |
| `class_icons` | Classes | Class icons and colours. Choose an icon and colour for a class. |
| `ta_designation` | Accounts | Teaching assistants. The TA designation for faculty accounts. |
| `trash` | Accounts | Deleted accounts (30 days). Restore a deleted account within 30 days. |
| `presence` | Accounts | Active users. Who is signed in now, last activity and activity graphs. |
| `backups` | System | Backups and restore. Save, view and restore backups of the database and system state. |
| `activity_charts` | System | Activity graphs. Charts of an account's activity over time. |
| `traffic_monitor` | Security | Traffic monitor. Detect unusual request rates and alert administrators. |
| `risk_scores` | Security | Account risk badges. A safety badge and score for every account. |
| `disabled_overlay` | Security | Disabled-account notice. Blur the page and explain when the signed-in account is disabled. |
| `update_overlay` | System | Update notice. Blur the page and explain while the system is being updated. |
