# Launch flags, features and the global policy

Root decides **how imPress starts**. These decisions are made where the server is started, and nothing in the web app or the API can undo them. There are three layers, from the most fixed to the most flexible:

| Layer | Who sets it | Where | Can be changed from the web app? |
|---|---|---|---|
| **Launch flags** and the **global policy** | root | **`backend/impress.flags.json`**, the start command, a root-signed `global_policy_control.json`, `IMPRESS_GPC` | no |
| **TrustedInstaller's decisions** | the system | at every start, from what it finds on the host | no (an administrator cannot override it) |
| **Features** | administrators, super admins (and root) | *System → Features* | yes, within the authority rules below |

> **Two kinds of switch.** This page is about **feature flags** (test mode, OTA, the traffic monitor, features): a plain file you may edit by hand. The security and integrity switches are **policy** (global policy control): kept in a *sealed* store that a hand edit breaks, changed only with `policy set` in the console (root's password) or, for four operational flags, by a super admin on the System page, and recorded with who, how and when. See [global policy control](../design/gpc.md#the-policy-store).

## The flags file

Flags no longer have to be remembered and typed at every start. They live in one file, **`backend/impress.flags.json`**, and every flag explains itself next to its value:

```json
"test_mode.forced": {
  "value": false,
  "about": "Test mode is forced on by root (launch flag --test-mode) and nobody can turn it off; the default super admin then signs in with a fixed lab password.",
  "type": "bool",
  "standard": false,
  "hardened": false,
  "how": "Lab use. Same as the command line's --test-mode. Not allowed in the hardened profile. Cannot be true while test_mode.allowed is false."
}
```

The file is written the first time imPress starts (or with `python -m app.flagsfile write`) and is part of the repository, so you can read it before you run anything. **Only `value` is read**; `about`, `type`, `standard`, `hardened`, `how` and `choices` are there for the person editing it. The complete list is in the [flags reference](../reference/flags.md).

To change how imPress starts: edit a `value`, save, and **restart** (in the root screen, type `restart`; the file is read again each time). That is all: `./launcher.sh` needs no arguments.

| Section | What it holds |
|---|---|
| `profile` | `standard` (a classroom or lab) or `hardened` (a production server that refuses to start below its floor) |
| `flags` | the **feature flags**: `test_mode.allowed`, `test_mode.forced`, `test_mode.export_allowed`, `ota.enabled`, `features.disabled`, `traffic.monitor`. A *policy* flag named here is refused (`FLAG_IS_POLICY`): use `policy set` |
| `features` | every web-app feature by name; `false` switches it off for everybody (administrators cannot switch it back on) |

**Rules that keep it safe**

- **A value left as shipped is not an override.** The profile's own default applies, so one file serves both profiles and an untouched file never loosens the hardened profile. If you set a flag to the value the file shipped with, nothing changes; that is by design.
- **In the hardened profile an edit may only make a flag safer**, exactly like the command line. To loosen one, sign a policy file with `scripts/gpc.py`.
- **A mistake never half-applies.** An unknown flag, a value of the wrong kind, invalid JSON: imPress says which flag and does not start (exit code 2; the root screen stays open and says `Fix the file and type restart`). `python -m app.flagsfile check` validates the file without starting anything.
- **Order of precedence**, lowest first: the profile's defaults, a root-signed `global_policy_control.json`, **the flags file**, `IMPRESS_GPC` in the environment, **the command line**. Later wins.
- Put the file somewhere else with `IMPRESS_FLAGS_FILE=/path/impress.flags.json` (a container keeps it in its data volume).
- The file is not part of the program's integrity check, so editing it never trips [integrity protection](../design/integrity-protection.md).

**Common edits**

| I want | Edit |
|---|---|
| a lab server where nobody can leave test mode | `flags` → `test_mode.forced` → `true` |
| no test-data menu at all | `flags` → `test_mode.allowed` → `false` |
| no over-the-air firmware updates | `flags` → `ota.enabled` → `false` |
| a production server | `profile` → `hardened`, then satisfy its floor ([production hardening](production-hardening.md)) |
| the search box off for everybody | `features` → `search` → `false` |
| an approval to wait before it can run | `policy set dual_control.delay_minutes 30` (policy, not a feature flag) |
| keep what I passed on this start for every start | add `--save`: `./launcher.sh --no-ota --save` |

## Changing flags while it runs, and keeping them

| Command | What it does |
|---|---|
| `flags show` | every feature flag: value, where it came from (default, file, launch, session) |
| `flags set NAME VALUE` | change one **for this run only**; takes effect within seconds and is forgotten when the server restarts. A change that makes flags conflict is refused |
| `flags unset NAME` | drop one session change |
| `flags save` | write this run's changes into `impress.flags.json` (the explanations are kept): every later start uses them |
| `flags reset` / `flags reset --file` | drop the session's changes / also restore the shipped file (root's password) |
| `--save` (command line only) | write the feature flags given on this start into the file before starting: `./launcher.sh --test-mode --save`. Policy flags cannot be saved this way |

Test mode that is *forced* begins at server start: changing `test_mode.forced` for a session affects what is refused from then on, not the start-up switch.

## Flags that conflict

Some flags cannot be combined. imPress checks this **first**: before the integrity check, the database, TrustedInstaller or the hardened floor. If it fails the program prints each conflict, **which flags are involved and why**, and exits with code 2; nothing else is started. The checks (a rule that needs an explicit flag never fires on defaults alone, so `--no-test-mode` is always fine):

| Flags | Why they conflict |
|---|---|
| `test_mode.forced` + `test_mode.allowed=false` | test mode would be forced on and not allowed to exist (`--test-mode` with `--no-test-mode`) |
| `test_mode.forced` + the hardened profile | the hardened profile cannot force test mode |
| `iips.enabled=false` + the hardened profile | the hardened profile cannot run without integrity protection |
| `backups.restore_requires_approval` + `dual_control.enabled=false` | no restore could ever be approved |
| `dual_control.mfa_required` + `dual_control.enabled=false` | a second factor for steps that do not exist |
| `audit.purge_days` below `audit.min_retention_days` | entries deleted sooner than they must be kept |
| `iips.device_binding=enforce` + `iips.enabled=false` | binding belongs to the integrity check that is off |
| `firmware.signing_required` + `ota.enabled=false` | signing images that can never be deployed |
| `--rehash` + `--bypass-iips`; `--test-mode` + `--no-test-mode` | on the command line |

## Command-line flags

The same decisions can be given on the start command. They **win over the file** for that start (and over `IMPRESS_GPC`), which is handy for a one-off: `./launcher.sh --no-ota`.

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
| `--feature NAME=VALUE` | set any [policy flag](../design/gpc.md) (the flags file does the same for good); repeatable. In the hardened profile an override may only make a flag safer. Example: `--feature features.disabled=search,backups` |
| `--profile standard\|hardened` | the policy profile |
| `--host H`, `--port N` | fixed listener `0.0.0.0:8000`; any other host or port is refused |
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
