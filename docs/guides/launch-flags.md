# Launch flags, features and the global policy

Root decides **how imPress starts**. These decisions are made where the server is started (the command line, the container arguments, the environment), and nothing in the web app or the API can undo them. There are three layers, from the most fixed to the most flexible:

| Layer | Who sets it | Where | Can be changed from the web app? |
|---|---|---|---|
| **Launch flags** and the **global policy** | root | the start command, a root-signed `global_policy_control.json`, `IMPRESS_GPC` | no |
| **TrustedInstaller's decisions** | the system | at every start, from what it finds on the host | no (an administrator cannot override it) |
| **Features** | administrators, super admins (and root) | *System → Features* | yes, within the authority rules below |

## Launch flags

```bash
./launcher.sh [flags]          # macOS and Linux (also: scripts/start.sh, python -m app.serve)
launcher.bat [flags]           # Windows
docker run … IMAGE [flags]     # the container's arguments are the flags
```

| Flag | Effect |
|---|---|
| `--test-mode` | test mode is **on and cannot be turned off**, by anyone, from the web app (policy `test_mode.forced`). The default super admin then signs in with the lab password `imPress@2026` and a banner on every page says test mode is on. Attempting to turn it off answers: *Test mode was enabled by root and cannot be disabled. This is intentional application design.* The hardened profile refuses to start with it |
| `--no-test-mode` | test mode does not exist: no Test data page, no routes (policy `test_mode.allowed=false`). Cannot be switched on from the web app |
| `--no-ota` | over-the-air updates are off: no firmware uploads, deployments or pushes, and devices are offered nothing (policy `ota.enabled=false`) |
| `--rehash` | accept the program's files as they are now as the new reference for [integrity protection](../design/integrity-protection.md) |
| `--bypass-iips` | start although the integrity check failed (or without it). **Every page shows a red warning**: *imPress Integrity Protection Service is disabled. Proceed with caution.* Not allowed in the hardened profile |
| `--feature NAME=VALUE` | set any [policy flag](../design/gpc.md); repeatable. In the hardened profile an override may only make a flag safer. Example: `--feature features.disabled=search,backups` |
| `--profile standard\|hardened` | the policy profile |
| `--host H`, `--port N` | where to listen (default `127.0.0.1:8000`; or `IMPRESS_HOST`, `IMPRESS_PORT`) |
| `--plain` | no [root screen](console.md): the logo, then a plain log |

`--test-mode` and `--no-test-mode`, and `--rehash` and `--bypass-iips`, contradict each other and are refused. A mistake in `--feature` is an error when you start, not a stack trace later.

Every start prints the imPress logo and version, **with the patch number** (for example `v2.2.24`), then the log. Where the version comes from: a `RELEASE` file stamped by the build, else `git` (the commits since the line's `.0` tag, as the release workflow counts them), else `VERSION`.

## Features

Every small capability of the web app is a **feature** that can be switched off. They are listed, with who changed them and when, under *System → Features*; faculty never see that page.

| Group | Feature | What it is |
|---|---|---|
| Interface | `search` | global search (the command palette) |
| | `notifications` | the notification tray |
| | `tutorial` | the guided tour |
| | `onboarding` | the welcome set-up questions (the forced password change is never skipped) |
| | `sidebar_collapse` | collapsing the sidebar |
| | `help_menu` | the *Help & documentation* menu for administrators |
| | `password_meter` | the strength bar under password fields |
| Personalization | `dashboard_widgets` | the editable dashboard |
| | `personalization` | accent colours, date and time formats |
| | `accessibility` | colour-vision modes, contrast, motion, text size |
| | `advanced_mode` | detailed statistics for administrators |
| Classes | `class_icons` | an icon and colour for a class |
| Accounts | `ta_designation` | teaching assistants |
| | `trash` | the 30-day trash for deleted accounts (enforced by the server) |
| | `presence` | who is active now (enforced by the server) |
| System | `backups` | saved backups and restore (enforced by the server) |
| | `activity_charts` | activity history charts (enforced by the server) |
| | `update_overlay` | the *updating imPress* notice while a rollout runs |
| Security | `traffic_monitor` | unusual-traffic detection |
| | `risk_scores` | the safety badge on accounts |
| | `disabled_overlay` | the notice shown to someone whose account was disabled while they use imPress |

Features marked *enforced by the server* are refused by the API when off (`403 FEATURE_DISABLED`); the others are hidden by the web app.

### Who can change a feature

There are four levels of authority, from least to most: **administrator**, **super admin**, **root**, **TrustedInstaller**.

- A change is allowed only if the person's level is **at least the level of whoever set the feature last**, and at least the feature's *lock* level. An administrator cannot undo what a super admin set; nobody on the web can undo what root set; nobody can undo what TrustedInstaller set.
- Whoever sets a feature can **lock** it up to their own level, so lower levels cannot change it: a super admin can make a feature changeable by super admins only (the lock button on the row).
- Root's switches come from `--feature features.disabled=NAME,NAME` or the console's `feature NAME off --lock`.
- Every change is written to the **change log** (who, which level, what, when). The info icon on a row shows who last set it and when, in plain words: *Changed by Asha Rao, a super admin, at …*, *Set by root (launch flag)*, *Turned off by TrustedInstaller … because this server does not meet the minimum requirements*.

## Global policy

The policy flags are the security and integrity switches (`dual_control.*`, `audit.*`, `test_mode.*`, `ota.enabled`, `deadlock_prevention.enabled`, `backups.restore_requires_approval`, `code.verify_manifest`, `device.*`, `firmware.*`, `features.disabled`, `root.allow_access`, `iips.enabled`, `traffic.monitor`, ...). The full table with the standard and hardened defaults is in [global policy control](../design/gpc.md); `policy show` in the console and *System → Policy* show the values in force and where each came from.
