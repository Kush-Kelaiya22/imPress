# Refactor audit and roadmap (v2.1)

This document records an audit of the `varun/v2.1` line (at `f7b37ad`, 2026-10-13). The audit checked the code against the refactor brief: account lifecycle, lockout prevention, ring-based authorization, AURIS scheduling, OTA redesign and simplification. Every actionable finding is a GitHub issue under the tracking issue [#115](https://github.com/Kush-Kelaiya22/imPress/issues/115). The issues are the source of truth for scope, acceptance criteria and status. This page explains the reasoning and the order of work.

Nothing in this document has been implemented yet. Statements about current behaviour come from the code. The one performance figure comes from a local measurement, described in [#133](https://github.com/Kush-Kelaiya22/imPress/issues/133).

## Baseline

| Item | State at audit |
| --- | --- |
| Standard test runner | `python run_tests.py`: 11 suites, 750 passed, 0 failed (5 individual tests skipped inside suites), 2026-10-13 |
| Roles | `super_admin`, `admin`, `teacher`. Students have no login accounts |
| Authorization | Route dependencies `require_admin` / `require_super_admin` / `require_teacher_or_admin`, plus inline role and ownership checks in routers and the WebSocket handler |
| Account deletion | `DELETE /api/admin/users/{id}` only sets `is_active = false` |
| Scheduling | Weekly `meeting_schedule` per class. Clash *warnings* only. No dated exceptions. No AURIS integration |
| OTA | Staged deployments with canary, batches, durable state machine, signed images, device TLS (#34–#38, #66). Hubs and gateways only. Updates start immediately |

## Findings by priority

| Pri | Issue | Finding | Milestone |
| --- | --- | --- | --- |
| P0 | [#116](https://github.com/Kush-Kelaiya22/imPress/issues/116) | A super admin can deactivate itself through `PUT /api/admin/users/{id}`. No route enforces "at least one active super admin", and two super admins can disable each other concurrently | M1 |
| P1 | [#117](https://github.com/Kush-Kelaiya22/imPress/issues/117) | `DELETE` user is a soft delete reported as a delete | M1 |
| P1 | [#118](https://github.com/Kush-Kelaiya22/imPress/issues/118) | Deactivation, password reset and role change do not revoke sessions or close sockets. Reactivation revives old tokens | M1 |
| P1 | [#119](https://github.com/Kush-Kelaiya22/imPress/issues/119) | No reactivate endpoint, mixed `PUT` semantics, free-text errors | M1 |
| P2 | [#120](https://github.com/Kush-Kelaiya22/imPress/issues/120) | No safe recovery for an installation that is already locked out (startup seeds only an empty table) | M1 |
| P1 | [#121](https://github.com/Kush-Kelaiya22/imPress/issues/121) | Class WebSocket rooms check the role, not class assignment (details withheld, CONTRIBUTING §16) | M2 |
| P1 | [#122](https://github.com/Kush-Kelaiya22/imPress/issues/122) | Role checks are scattered and have drifted. Admins can manage other admins | M2 |
| P1 | [#123](https://github.com/Kush-Kelaiya22/imPress/issues/123) | Firmware signing is opt-in (fail-open). One admin can upload, approve and deploy | M2 |
| P2 | [#124](https://github.com/Kush-Kelaiya22/imPress/issues/124) | Decision: student accounts (Ring 3) or device-mediated identity only | M2 |
| P3 | [#125](https://github.com/Kush-Kelaiya22/imPress/issues/125) | Admin authority is global. Scoped grants only if a site needs them | M2 |
| P1 | [#126](https://github.com/Kush-Kelaiya22/imPress/issues/126) | No record of cancelled, moved or extra sessions. No reliable "room in use?" query | M3 |
| P2 | [#127](https://github.com/Kush-Kelaiya22/imPress/issues/127) | No AURIS import. Blocked until the AURIS owners provide an authorized export format | M3 |
| P1 | [#128](https://github.com/Kush-Kelaiya22/imPress/issues/128) | Hub and gateway updates can start during a class | M4 |
| P2 | [#129](https://github.com/Kush-Kelaiya22/imPress/issues/129) | Compatibility is checked only by `device_type`. Rollback capability is not recorded (the student bootloader has rollback disabled) | M4 |
| P2 | [#130](https://github.com/Kush-Kelaiya22/imPress/issues/130) | Student modules cannot be updated over the air | M4 |
| P2 | [#131](https://github.com/Kush-Kelaiya22/imPress/issues/131) | Firmware UI mixes all three device families | M4 |
| P1 | [#132](https://github.com/Kush-Kelaiya22/imPress/issues/132) | C6 gateway cannot reach the backend (TCP connect timeout over HTTPS/WSS). The default server bind and the default firmware host do not match | `varun/v2.1` |
| P2 | [#133](https://github.com/Kush-Kelaiya22/imPress/issues/133) | Loading the current user eagerly loads the teacher's whole quiz history (measured: 9 queries, 3,000 rows) | M5 |
| P3 | [#134](https://github.com/Kush-Kelaiya22/imPress/issues/134) | Two web UIs (served vanilla app and optional React dashboard) | M5 |

Milestone names begin with `Refactor M…` and so do not match the `<owner>/vX.Y` pattern. As a result, they never gate releases ([releases guide](../guides/releases.md)).

## Order of work

```text
#116 lockout invariant ─┬─► #117 real delete ─┐
                        │                     ├─► #119 lifecycle API + UI
#118 session revocation ┴─────────────────────┘
#116 ─► #122 central policy ─┬─► #123 TrustedInstaller
                             └─► #125 scoped admins
#121 WebSocket class binding        (independent, do early)
#126 class occurrences ─┬─► #127 AURIS import (externally blocked)
                        └─► #128 OTA maintenance windows ─► #131 firmware UI
#129 hardware metadata ─► #130 student OTA
#132, #133, #134                     (independent)
```

## Design decisions proposed in the issues

These are proposals until a maintainer approves them in the issue.

**Lockout invariant in the database.** SQLite triggers abort any `UPDATE` or `DELETE` on `users` that would leave no other active super admin. The trigger runs in the same statement as the write, and SQLite serialises writers, so concurrent requests cannot both pass. A lifecycle service maps the abort to `409 LAST_SUPER_ADMIN`. The UI explains the refusal but does not enforce it. Recovery is an offline command that needs shell access to the host. It is never an HTTP endpoint (#120).

**Deletion keeps evidence, not accounts.** Deleting a user removes the row and its sessions and co-faculty links. Provenance columns are set to NULL. Activity-log rows are kept with the deleted username in `details`. Deletion is refused while the user is still the primary teacher of a class.

**Rings are a model, not inheritance.**

| Ring | Identity | Can log in | Holds user-facing permissions |
| --- | --- | --- | --- |
| −2 | TrustedInstaller: firmware verification and offer service | No | No. Firmware checks only |
| −1 | Root: integrity rules inside the policy module | No | No. Vetoes only |
| 0 | `super_admin` | Yes | All user-facing permissions, subject to Root |
| 1 | `admin` | Yes | Administration, optionally scoped (#125) |
| 2 | `teacher` (faculty) | Yes | Assigned classes only |
| 3 | student | No accounts (decision in #124) | Device-mediated answers and votes |
| 4+ | unauthenticated | — | None (default deny) |

Lower ring numbers do not imply every permission of higher rings. Root cannot deploy firmware, and TrustedInstaller cannot change accounts. A super admin can request a deployment but cannot skip TrustedInstaller verification.

**OTA states.** The existing state machine (`services/deployments.py`) already matches the brief: `queued → precheck → downloading → verifying → installing → rebooting → health_check → success`, plus `failed`, `timed_out`, `unreachable`, `incompatible`, `cancelled` and `rolled_back`. The only new state is `deferred` (#128). The timetable is checked again before each target is offered. When the timetable is stale or unknown, the update is deferred (fail closed).

**Student OTA needs one serial flash.** `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` is a bootloader option. It is not set for student modules, and it cannot be enabled over the air. Until each module has been re-flashed once, the system must not claim automatic rollback for student modules.

## Not changed by this plan

- The existing OTA engine, signing and TLS work. The plan extends it.
- AURIS functionality outside scheduling. imPress stays focused on participation, assessment and device administration.
- No new frameworks or background services. The policy layer is plain Python, and scheduling reuses the existing deployment loop.

## Verification status

No hardware was tested for this audit. The firmware issues (#129, #130, #132) carry `needs:hardware` where final verification needs boards, and results will be recorded according to [CONTRIBUTING §10.3](https://github.com/Kush-Kelaiya22/imPress/blob/varun/v2.1/CONTRIBUTING.md#103-hardware-verification-status).
