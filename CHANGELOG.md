# Changelog

All notable changes to imPress, for the people who install and use it. Each pull request adds its entries here; how to write them is in [CONTRIBUTING §14.4](CONTRIBUTING.md#144-recording-changes).

- **Sections:** `[Unreleased]` collects the changes on the integration line. Every push that passes CI is released as the next patch (for example `varun/v2.1.4`), and its release page lists the entries that are new since the previous release. A section per release keeps the history from before this file existed.
- **Categories:** **Added** (new capability), **Changed** (different behaviour of something that exists), **Removed** (no longer available), **Fixed** (a defect repaired), **Security** (a protection added or a vulnerability fixed).
- **Detail:** the per-issue engineering history, with the tests for each change, is in [`docs/reference/changelog-v2.1.md`](docs/reference/changelog-v2.1.md).

## [Unreleased]

### Added

- **A new web app experience.** A minimal redesign: a centred sign-in card, flat surfaces with hairline borders, one typeface (Inter), smaller and quieter controls and plain wording ("Add account", "Disable", students are added, not invited); more icons; a collapsible sidebar; skeletons while a page loads; an animated light/dark change; a **guided tour** and a welcome set-up on first sign-in (password, display name, look); a **notification tray**; a **command palette** (Ctrl/⌘ K) that searches classrooms, students, quizzes, accounts and devices (scoped by permission) and shows settings as live widgets; **personalization** (accent colours, text size, density, date, time and number formats, start page) and **accessibility** (reduced motion, high contrast, colour-vision modes, screen-reader support, skip link); **dashboards of widgets** you add, remove, resize and drag, with an **advanced mode** for administrators; an icon and colour for every class; accounts with **safety badges**, **active now**, per-account **activity charts**, teaching assistants, role changes with confirmation and a **30-day trash**; a System page with **features**, **requirements**, **backups** and **security** tabs. [Personalization](docs/guides/personalization.md), [accounts](docs/guides/accounts-and-onboarding.md).
- **More capable root console and log screen.** Root can inspect or reset the protected default super-admin password, use grouped commands for classroom data, and invoke the application's own routes in-process with normal authorization and validation. The root screen keeps bounded log history and supports `scroll up`, `scroll down`, `scroll top` and `scroll live`.
- **Notices that cover the page:** the page blurs and explains when your account is disabled while you use it, while an update is running, and after a restart.
- **Root screen and launch flags.** Started from a terminal, imPress shows its logo and version (with the patch number), the live log and a command line (`root@impress:~>`); in a container, `docker run -it` shows it and `-d` prints a plain log. Flags: `--test-mode` (forced, cannot be turned off), `--no-test-mode`, `--no-ota`, `--rehash`, `--bypass-iips`, `--feature NAME=VALUE`. [Console and screen](docs/guides/console.md), [launch flags](docs/guides/launch-flags.md).
- **Features and authority.** Every small capability is a switch; administrator, super admin, root and TrustedInstaller may set it in that order and a lower level cannot undo a higher one; every change is logged with who and when. 
- **TrustedInstaller start-up verification.** imPress is locked until the host (operating system, Python, SQLite, data folder, clock, processor, memory, disk) is verified; features the host cannot carry are switched off and return when it can; inside a container the separate root console is closed. [Trusted boot](docs/design/trusted-boot.md). ([#230](https://github.com/Kush-Kelaiya22/imPress/issues/230))
- **imPress Integrity Protection Service.** The program's own files and folder structure are hashed at first start; a difference disables imPress until root runs with `--rehash`; `--bypass-iips` shows a warning on every page. [Integrity protection](docs/design/integrity-protection.md). ([#231](https://github.com/Kush-Kelaiya22/imPress/issues/231))
- **Traffic monitor and account safety.** Per-endpoint limits per origin and per account; a DoS or DDoS suspicion alerts administrators with the origin, pages and account, without blocking anyone; every account has a *Safe* / *Potentially Unsafe* / *Likely Compromised* badge and a 0 to 100 score; only super admins can sign an account out. [Traffic monitor](docs/design/traffic-monitor.md). ([#232](https://github.com/Kush-Kelaiya22/imPress/issues/232))
- **1PSID.** Session identifiers are bound to the server run that issued them, so a restart ends every session. ([#234](https://github.com/Kush-Kelaiya22/imPress/issues/234))
- **Backups** of the database and system state: save, view and restore from the web app; a super admin can reset the system. [Backups](docs/guides/backups.md).
- **Accounts, onboarding and the root console (backend):** new accounts start with a temporary password (generated or typed) and must choose their own at first sign-in; a password rule for admin and faculty (8+ characters, lower and upper case, a number, a special character) with a strength score; display names separate from user names; a teaching-assistant designation with faculty permissions; faculty and admin swap by a super admin; a protected default super admin `impress.default.superAdmin` with a new random password at every start; global deadlock prevention (rollback, then a recovery account); super admins are created only from the interactive root console (`scripts/console.sh`, `console.bat`); launch flags `--test-mode`, `--no-test-mode`, `--no-ota`; a 30-day trash for deleted accounts; per-account preferences (theme, accent, accessibility, advanced mode, dashboard layout); global search limited to what the caller may see; who is active now and per-account activity summaries; named backups with restore and a system reset; an icon and colour for each class.
- **Motion and materials** for the web app, following Apple's Human Interface Guidelines for layout, type and translucent materials and Material 3 Expressive for movement: springy button presses whose corners tighten, dialogs that spring in (a bottom sheet on a phone), cards and rows that rise in with a stagger, figures that count up, a visible keyboard focus ring and 44 pt touch targets. Entry plays only when you change page, never when data refreshes under you; with *reduce motion* set nothing moves. [Design notes](docs/design/ui-design.md). ([#206](https://github.com/Kush-Kelaiya22/imPress/issues/206))
- **README redesigned**: a short front page with screenshots, a start-here table per role, the security and privacy story, and a map of the documentation. ([#208](https://github.com/Kush-Kelaiya22/imPress/issues/208))
- **Global policy control (GPC):** the security and integrity switches belong to root. Typed flags with safe defaults for a *standard* and a *hardened* profile, an optional **root-signed policy file** (Ed25519, with a serial that only goes up) and inline overrides on the start command (in the hardened profile they may only tighten). The System page shows the effective policy and where each value came from; nothing in the web app or the API can change it. The hardened profile **refuses to start** below its floor (debug off, real secrets, HTTPS, per-device keys, signed firmware, an external audit sink). Root's tool: `scripts/gpc.py`. See [global policy control](docs/design/gpc.md) and [production hardening](docs/guides/production-hardening.md). ([#204](https://github.com/Kush-Kelaiya22/imPress/issues/204), [#198](https://github.com/Kush-Kelaiya22/imPress/issues/198), [#199](https://github.com/Kush-Kelaiya22/imPress/issues/199))
- **Dual control** for accepting a changed database and for clearing or resetting data: one super admin requests, a different one approves, each re-entering their password, then a delay, an expiry and a single use. Every step is logged and alerted. ([#196](https://github.com/Kush-Kelaiya22/imPress/issues/196))
- **External audit trail:** every activity entry is also written to a hash-chained file and/or a signed webhook that the application cannot rewrite; `python -m app.manage audit-verify FILE` checks the chain. Students' personal data is never written to it. ([#196](https://github.com/Kush-Kelaiya22/imPress/issues/196), [#202](https://github.com/Kush-Kelaiya22/imPress/issues/202))
- **Signed code manifest** (root signs, the server verifies its own files at start-up) and **signed exports** (a signature a receiver checks with `scripts/verify_export.py`). ([#205](https://github.com/Kush-Kelaiya22/imPress/issues/205))
- A **privacy and compliance toolkit** in the docs: data inventory, privacy notice template, retention schedule, data-rights runbook, incident response, control mapping and a risk register. `scripts/backup.sh` makes a checksummed, optionally encrypted off-host backup. ([#200](https://github.com/Kush-Kelaiya22/imPress/issues/200), [#202](https://github.com/Kush-Kelaiya22/imPress/issues/202))
- A new look for the web app, closer to a modern dashboard: a sidebar with Overview, Classrooms, Quizzes & polls, Students, Courses and, for administrators, Devices, Firmware & OTA, User access, Activity log and System; a top bar with search, notifications and the light/dark switch; stat cards, classroom cards with filters, a students page with attendance and participation per student, a combined user access and activity log page with filters and CSV export, and a new sign-in page.
- Pages update on their own when the data changes (a class goes live, a device comes online, someone answers, a user is added): no more reloading. An update waits while you are typing, have a dialog open or have unsaved input, and keeps your tab, filters and scroll position.
- `./launcher.sh` (macOS, Linux) and `launcher.bat` (Windows) set up and start the server without Docker, in one step: they install Python 3.12+ if it is missing, create the virtual environment, install the dependencies, write `backend/.env` with generated secrets, stop whatever is using the port, and start imPress.
- **Debug mode and test data** for super admins (*Administration → Test data*): the real database is copied aside (after it verifies) and everyone sees a test banner while you work on a copy. Sheets per table that work like a spreadsheet (type, paste from Google Sheets or Excel, upload CSV), a generator of realistic, unique and consistent data from a seed, all-or-nothing import with per-cell errors, and optional simulated activity. Turning it off restores the real database and lets you save, export or delete the test data. See [debug mode and test data](docs/guides/test-mode.md).
- **System** page for administrators: the database's integrity status, the temporary backups, *Verify now*, and *Clear data* (class data, or a full reset) for super admins, with a typed confirmation and a backup first.
- *End sessions* on a user (User access page) signs that user out everywhere.

- More detailed documentation: 14 new diagrams (scheduling, deployment topology, firmware versions, recovery, configuration, WebSocket connection, sign-in and session, hardware test order, test layers, imports, development loop, the classroom node), a 2.1 → 2.2 upgrade procedure, the protection of every communication path, and a [placeholders](docs/reference/placeholders.md) page. The guides no longer show real addresses or ports; they use placeholders such as `<SERVER_IP>` and `<SERIAL_PORT>`.
- A design proposal for authenticating the radio messages between student modules and the hub, for review before it is built: [mesh frame authentication](docs/design/mesh-authentication.md). ([#187](https://github.com/Kush-Kelaiya22/imPress/issues/187))
- Every release now says what its firmware is and is not: each board's folder has `BUILD_INFO.json` (commit, ESP-IDF version, chip, flash settings, image checksum) and `FLASHING.txt` (esptool commands with the offsets of that build), every download has a signed build-provenance attestation (`gh attestation verify <file> -R Kush-Kelaiya22/imPress`), and the release page states that a release image is not approved for over-the-air updates until the server's TrustedInstaller has qualified it and an administrator has approved it.
- A classroom simulator for developers (`firmware/sim/classroom_sim.py`): student modules, a hub and a gateway exchange frames through the firmware's own protocol code, with repeatable radio and SPI faults (loss, duplicates, corruption, reordering). Its tests run in CI, including a simulated room feeding the real server. It found two ways answers can be lost ([#181](https://github.com/Kush-Kelaiya22/imPress/issues/181), [#182](https://github.com/Kush-Kelaiya22/imPress/issues/182)).
- Quiz answers from a student module now carry the time the student took to answer, measured on the module from the moment the question arrived (it was always 0).
- A gateway can be built with its classroom code (`CLASSROOM_CODE` in menuconfig) so the server links it to the class held in that room when it first registers. Empty by default: gateways are linked in the admin page as before.
- `firmware/activate_idf.ps1` finds and activates an ESP-IDF installation in PowerShell on Windows. ([#114](https://github.com/Kush-Kelaiya22/imPress/issues/114))

### Changed

- Test-data copies are now treated as sensitive: the folders are private (0700/0600), pending and saved copies expire by policy, every enable, save, export, delete and expiry is audited, and root can switch debug mode and exports off. The copy taken before a clear expires after 30 days (14 in the hardened profile). ([#201](https://github.com/Kush-Kelaiya22/imPress/issues/201))
- When a failed database is restored automatically, the failed file is first kept for investigation, and the alert says how old the restored backup was. ([#203](https://github.com/Kush-Kelaiya22/imPress/issues/203))
- Sessions end after **5 minutes** without activity (was 60). A teacher whose class is in session (activated, or in its timetable slot) gets **30 minutes**, so a lecture is not interrupted. The settings are `IMPRESS_SESSION_IDLE_MINUTES` and `IMPRESS_SESSION_CLASS_IDLE_MINUTES`.
- A class with a roster now counts only its enrolled students' answers and votes. An answer from anyone else is not counted, and the teacher sees who it was on the live page, to enrol them if they belong there. A class with no enrolled students at all counts everyone, as before. ([#186](https://github.com/Kush-Kelaiya22/imPress/issues/186))
- The launchers and server runner now use the fixed `0.0.0.0:8000` listener. When port 8000 is busy, launchers identify the owner and ask before requesting a graceful stop; force-killing requires a second confirmation. Other host/port settings are refused.

### Fixed

- **Upgrading an existing database no longer stops imPress from starting.** The schema upgrade changes every row's seal; imPress took that for tampering, restored an older backup that lacked the new tables, and failed with a database error. An upgrade is now sealed again as it is, and a backup made by an older version is brought up to date when it is restored.
- The Overview's *Classrooms today* table no longer cuts off its right-hand columns on a laptop-sized window: secondary columns step aside first.
- The server now starts on Windows: it needs the `tzdata` package there for the India time zone, which is now installed with the other dependencies.
- An unconfigured hub now looks for its updates on the same server as its gateway: the hub's built-in default server address differed from the gateway's. `firmware/activate_idf.ps1` no longer searches one developer's own drive.
- A transfer error between the hub and the gateway no longer loses the answers it carried: each side keeps what it sent until the other confirms it, and sends it again otherwise. Works with older hubs and gateways (they keep the old behaviour). ([#182](https://github.com/Kush-Kelaiya22/imPress/issues/182))
- A student's answer or vote lost on the radio is now sent again until the hub confirms it (at most three more times), and the module shows *Answer received*, or *Not delivered: press again* if it never got through. Before, a lost answer was silently missing from the results. Needs the v2.2 hub and module firmware; older hubs and modules keep working as before. ([#181](https://github.com/Kush-Kelaiya22/imPress/issues/181))

### Security

- A teacher can now edit or deactivate only the students they registered or who are enrolled in a class they teach, and sees their e-mail and phone only for those students; before, any teacher could change any student and read every student's contact details. A teacher can still find any student by name or number to enrol them. ([#207](https://github.com/Kush-Kelaiya22/imPress/issues/207))
- The web app's Content-Security-Policy no longer allows inline scripts or inline event handlers (`script-src 'self'`, `script-src-attr 'none'`): every button, field and link now uses delegated events, and a browser blocks, and reports, any injected script. ([#197](https://github.com/Kush-Kelaiya22/imPress/issues/197))
- Erasing a student now also removes their name and enrollment number from the activity log (they were left in some entries), and the erase entry keeps only a keyed reference. ([#200](https://github.com/Kush-Kelaiya22/imPress/issues/200))
- The integrity state, the policy and the audit trail are controlled by root, not by an application super admin; accepting a changed database or clearing data needs a second super admin. See *Added*.
- Names with quotes can no longer break out of the web app's HTML (a teacher could create a class, or a device could register with a name, that ran script in an administrator's browser). Quotes are escaped everywhere, and inline handlers receive names as JSON.
- The database's integrity state (*Degraded*) is no longer public: it is sent to administrators only. Debug mode's generated teacher accounts get a random password for each debug-mode session instead of a fixed one.
- **One device per account:** while an account is signed in on one device, signing in from another device (another address, browser or system) is refused, written to the activity log as flagged, and shown to administrators as a notification. `IMPRESS_SINGLE_SESSION=false` turns it off.
- Passwords are hashed with SHA-256 and then salted bcrypt (no length limit on passphrases). Existing passwords keep working and are upgraded at the next sign-in.
- Every database write now passes a **database gateway** that checks the account's permission for that table; a refused write is flagged in the activity log and administrators are notified. Every row is sealed (HMAC-SHA256): a change made outside imPress (for example with an `sqlite3` command) is detected within 5 minutes, the last good temporary backup is restored automatically, the database is marked **Degraded**, and administrators get a notification. Temporary backups are kept in `IMPRESS_TEMP_BACKUP_DIR` (default: the system temporary folder). See [data integrity](docs/design/data-integrity.md).
- Clearing or resetting the database is possible only from the System page, by a super admin, with a typed confirmation; a backup is taken first.

- A gateway with its own device key now records answers, votes, attendance and room links only for the class it is linked to; for any other class they are skipped or refused.
- A firmware image's qualification report is now sealed by the server and bound to the image's exact bytes and build. A report edited in the database, or copied from another image, is no longer trusted: the TrustedInstaller recomputes it from the image before approval, offers and downloads.
- The web app no longer keeps the login token where page scripts can read it: the session is an `HttpOnly`, `SameSite=Strict` cookie (`Secure` over HTTPS). Changes made with it need the app's `X-Impress-Request` header (cross-site request forgery). After upgrading, everyone signs in once more. Scripts keep using `Authorization: Bearer`.
- The live class page's connection no longer carries the session token in its URL, where proxies and servers log it; it uses the cookie, and a connection opened from another website is refused.
- Logging out now ends the session on the server; it used to be forgotten only by the browser, and the token stayed valid until it expired.
- A gateway no longer trusts a radio frame's enrollment number to be terminated: a malformed or spoofed frame could make it read past the field.

## [varun/v2.1.64] - 2026-10-13

### Fixed

- A batch answer that identifies a student by firmware module UID now resolves through the module inventory instead of failing with HTTP 500. ([#179](https://github.com/Kush-Kelaiya22/imPress/issues/179))
- A gateway refused because it joins a class it is not linked to no longer reports only a key problem: its message now names both causes and where to fix the link. ([#159](https://github.com/Kush-Kelaiya22/imPress/issues/159))
- The live class page no longer keeps trying to reconnect after the server ended the teacher's access: a teacher who was signed out or deactivated is sent to the login page, and a teacher without access to the class is told so. ([#160](https://github.com/Kush-Kelaiya22/imPress/issues/160))
- The student mesh now refuses a message that would be too large for one ESP-NOW frame, instead of the radio dropping it; today's messages are all well within the limit. ([#170](https://github.com/Kush-Kelaiya22/imPress/issues/170))
- The container package page shows the image description and the guide link again for multi-architecture tags: images are now pushed in OCI format, whose index can carry them. ([#136](https://github.com/Kush-Kelaiya22/imPress/issues/136))
- A brief registry error while uploading the container image no longer fails the whole release; the upload is retried. ([#136](https://github.com/Kush-Kelaiya22/imPress/issues/136))
- A gateway that cannot reach the server now says why in its serial log (server unreachable: address, 127.0.0.1 or firewall; connection refused; TLS handshake failed; device key refused) and prints the server address and TLS mode it uses at boot. A build with TLS on port 8000 shows a warning, `scripts/start.sh` warns when only the local computer can connect, and the troubleshooting guide covers the Windows Mobile Hotspot firewall. ([#132](https://github.com/Kush-Kelaiya22/imPress/issues/132))
- Pages load faster for teachers with many quizzes: every request used to read the teacher's entire quiz and answer history, and class lists loaded every quiz just to count them. In a local measurement with 3,000 answers, a typical request went from 42 ms to 3 ms. ([#133](https://github.com/Kush-Kelaiya22/imPress/issues/133))
- A super admin can no longer lock everyone out by deactivating their own account (or the last active super admin) through any API route; the request is refused with an explanation, and the database itself refuses a change that would leave no active super admin. ([#116](https://github.com/Kush-Kelaiya22/imPress/issues/116))
- The Read the Docs graph now renders at its intended `/graph/` subpage instead of colliding with Sphinx's generated page.
- Graphify now treats graph-only automation commits as derived output, preventing a manual unchanged rerun from creating another graph commit.
- A release line created on the same commit as an older release no longer gates that older release: a line's test issues apply only to releases built on it after it existed. ([#107](https://github.com/Kush-Kelaiya22/imPress/issues/107))

### Added

- Step-by-step first-run, administrator and teacher guides; Windows/macOS/Linux native installation and firmware flashing paths; a classroom glossary and FAQ, linked from the documentation navigation. ([#137](https://github.com/Kush-Kelaiya22/imPress/issues/137))
- A Read the Docs-ready Sphinx/MyST documentation site with responsive navigation, full-text search, Mermaid diagrams, local build commands and an embedded revision-matched Graphify visualization.
- A public `/graph` engineering documentation portal with searchable Markdown guides and the interactive Graphify architecture map.
- A keyless, committed Graphify knowledge graph with Codex guidance, local hooks, validation, and automated GitHub synchronization for `varun/v2.1`.
- `CHANGELOG.md`, kept by every pull request. A CI check fails a pull request that doesn't add an entry, unless it has the `no-changelog` label. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- Releases for every owner's integration line (`kush/v2.1`, `aamna/v2.1`, `encrypted/v2.1`), not only `varun/v2.1`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- A "Setup problems" section in the troubleshooting guide, linked from the release page. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- Test issues for a release line also gate every release built on top of it, by any owner. Closing such an issue updates all of those releases at once. Issues inherited from another line are marked *from* in the release's test table. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The first release of a line creates its milestone (for example `aamna/v2.4`) automatically. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- A new release page is complete from the start: status badges, the Beta or Stable box, the test-issue table, the install guide and the changes. Later edits outside the status section are kept. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- A container image tag per release line (`varun-2.1`, `aamna-2.4`) that points at the line's newest release. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- A refactor audit and roadmap (`docs/engineering/REFACTOR_ROADMAP.md`) covering account lifecycle, lockout prevention, the privilege-ring authorization model, AURIS-aligned scheduling and the OTA redesign, with the planned work tracked in GitHub issues. ([#115](https://github.com/Kush-Kelaiya22/imPress/issues/115))
- Separate *Deactivate*, *Reactivate*, *Change role* and *Delete permanently* actions for user accounts, in the web app and as API endpoints (`/deactivate`, `/reactivate`, `/role`). The user list only shows the actions you are allowed to take, and a refused action says why. ([#119](https://github.com/Kush-Kelaiya22/imPress/issues/119))
- `python -m app.manage restore-super-admin --username <name>`: a server-side command that restores administrator access to an installation where no super admin can log in. It prints a one-time password and is logged; there is no web route for it. ([#120](https://github.com/Kush-Kelaiya22/imPress/issues/120))
- The backend container image now runs natively on 64-bit ARM (Apple silicon Macs, Raspberry Pi 4/5 with a 64-bit OS, ARM servers) as well as x86_64: every tag covers `linux/amd64` and `linux/arm64`. The package page describes the image and links to a new step-by-step [container guide](docs/deployment/container.md) (network, data, configuration, Compose, TLS, backups, upgrades, recovery). ([#136](https://github.com/Kush-Kelaiya22/imPress/issues/136))
- **Schedule changes** on the class page: cancel a class on one date, move it to another time or room, or add an extra session. imPress uses the weekly timetable together with these changes to tell when a room is in use, and administrators can view a room's bookings. See [scheduling](docs/design/scheduling.md). ([#126](https://github.com/Kush-Kelaiya22/imPress/issues/126))
- Hub and gateway firmware updates wait for the room's free time: before the first class, after the last, or in a long enough gap, checked again right before each device. A device that must wait shows *deferred* with the reason and starts by itself later. A super admin can start at once when the building is empty. ([#128](https://github.com/Kush-Kelaiya22/imPress/issues/128))
- Every release now has one complete firmware file per board (gateway, hub, student module) that flashes a new board with a single `esptool … write-flash 0x0 …` command; their checksums are in `SHA256SUMS.txt`. See [flash prebuilt images](docs/guides/releases.md#flash-prebuilt-images). ([#155](https://github.com/Kush-Kelaiya22/imPress/issues/155))
- The TrustedInstaller qualifies every firmware image before it can be approved or sent to a device: it checks that the chip's bootloader would load it, and simulates the device's update client, which must install it and refuse corrupted or interrupted copies. The Firmware page shows the report. Every change to the hub and student firmware is also booted in an emulator in CI. See [OTA architecture](docs/firmware/OTA_ARCHITECTURE.md). ([#154](https://github.com/Kush-Kelaiya22/imPress/issues/154))
- Gateways and hubs tell the server what board they are (flash and PSRAM size, OTA slot, whether they can roll back an update); *Diagnostics* shows it, and an update built for a different board (for example the 32 MB hub image on an 8 MB hub) or too large for the board is not sent to it. ([#129](https://github.com/Kush-Kelaiya22/imPress/issues/129))
- The Firmware page has a tab per device family (gateways, hubs, student modules) showing only that family's images and deployments together with its rules, and deployments show how many devices are waiting for a free room. ([#131](https://github.com/Kush-Kelaiya22/imPress/issues/131))
- A design for updating student modules over the air through the hub ([student module OTA](docs/design/student-ota.md)), with the transfer core already tested against a simulated lossy radio link. Student modules are still updated over USB until the hub and module firmware use it. ([#130](https://github.com/Kush-Kelaiya22/imPress/issues/130))

### Changed

- Recorded the UI boundary: the backend-served SPA is the sole product UI; `frontend/` remains an optional, non-shipped React/Vite reference dashboard, is excluded from feature-parity requirements, and is build-checked only as a smoke test. ([#134](https://github.com/Kush-Kelaiya22/imPress/issues/134))

- Releases are named after their integration line and owner, for example `varun/v2.1.4`. Download files are `impress-varun-2.1.4.zip`, and container image tags are `varun-2.1.4`, `varun-2.1`, `varun-latest` and `varun-beta`. The earlier releases were renamed to `varun/v2.1.0`, `varun/v2.1.2` and `varun/v2.1.3`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The release page has a fixed structure that puts installation, setup, first use and setup troubleshooting first. Its change summary lists what was added, changed, removed and fixed, taken from `CHANGELOG.md`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The release test table is more compact, and its columns are now **No.**, **Issue**, **Assigned to** and **Status**. A Stable release shows a **Note** box. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The milestone that gates a release is named after its line, for example `varun/v2.1`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The line of a release comes from its branch name, and the release rules and page templates always come from the default branch, so any owner's line releases without extra setup. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- Deleting a user now removes the account permanently (it used to only deactivate it). Classes, students and firmware they created are kept; the activity log keeps their name. Deleting the primary teacher of a class is refused until another teacher is assigned. Use *Deactivate* to keep an account but block access. ([#117](https://github.com/Kush-Kelaiya22/imPress/issues/117))
- `PUT /api/admin/users/{id}` (now also `PATCH`) only edits the name and email; send status and role changes to the new endpoints. A body with `is_active` or `role` is refused with `USE_LIFECYCLE_ENDPOINT`. ([#119](https://github.com/Kush-Kelaiya22/imPress/issues/119))
- Who may do what is now decided in one place, with a named permission for every action and a published permission matrix ([authorization model](docs/design/authorization.md)). Access is unchanged; refused requests now carry a code (for example `FORBIDDEN`) next to the message. ([#122](https://github.com/Kush-Kelaiya22/imPress/issues/122))
- A site without a firmware signing key no longer deploys unsigned firmware by default: set up signing, or set `IMPRESS_FIRMWARE_ALLOW_UNSIGNED=true` to keep deploying unsigned images. A site with a single administrator sets `IMPRESS_FIRMWARE_SINGLE_APPROVER=true` to approve its own uploads. ([#123](https://github.com/Kush-Kelaiya22/imPress/issues/123))
- A server opened with `http://` from another computer now shows *HTTPS required* instead of the login page. Use HTTPS (see the container guide), or set `IMPRESS_REQUIRE_HTTPS=false` on an isolated lab network. ([#152](https://github.com/Kush-Kelaiya22/imPress/issues/152))
- Co-faculty of a class can now enrol and remove its students, see its roster and its students' participation, like the primary teacher. ([#146](https://github.com/Kush-Kelaiya22/imPress/issues/146))

### Removed

- The *Unreleased changes* list in `CONTRIBUTING.md`. Its entries moved to this file. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))

### Security

- Passwords and class data are no longer accepted over unencrypted connections: logins, the web app and teacher live pages require HTTPS when opened from another computer, and every response carries browser security headers (HSTS, content security policy, no framing). The [container guide](docs/deployment/container.md) shows a ready HTTPS setup with Caddy. Gateways and hubs are not affected. ([#152](https://github.com/Kush-Kelaiya22/imPress/issues/152))
- Password guessing is slowed down: after several failed logins for one account (or from one address) the server makes the next attempt wait, doubling up to 15 minutes, without locking the real user out for good. New passwords must have at least 10 characters and must not be a common password or the username; existing passwords keep working. ([#153](https://github.com/Kush-Kelaiya22/imPress/issues/153))
- Firmware is checked again right before a device is offered or downloads it: it must be approved, built for that device's type and chip, signed with the site key, and its stored file must be unchanged. An image you uploaded must be approved by another administrator. ([#123](https://github.com/Kush-Kelaiya22/imPress/issues/123))
- Live-class connections are limited to the classes a user may open: a teacher can no longer join another teacher's class room, a gateway with its own device key can only join the class it is linked to, and browser pages can no longer send commands to classroom devices. The server refuses to start with WebSocket authentication turned off unless debug mode is on. ([#121](https://github.com/Kush-Kelaiya22/imPress/issues/121))
- Deactivating a user, changing their role or resetting their password now signs them out everywhere, including open live-class pages; reactivating an account no longer brings back its old sessions. Changing your own password signs out your other sessions. ([#118](https://github.com/Kush-Kelaiya22/imPress/issues/118))

## [varun/v2.1.3] - 2026-10-10

### Fixed

- Status badges on the release page could show *invalid* when shields.io was rate-limited. The release workflow now draws them. ([#102](https://github.com/Kush-Kelaiya22/imPress/issues/102))

## [varun/v2.1.2] - 2026-10-10

### Added

- Automatic patch releases: every push to the integration line that passes CI is published as the next patch release. The version is written into the server, the container image and the firmware. ([#100](https://github.com/Kush-Kelaiya22/imPress/issues/100))
- A status section on the release page: Beta or Stable, how many release test issues are closed, and a table of those issues. ([#100](https://github.com/Kush-Kelaiya22/imPress/issues/100))

### Changed

- The release page text is one template per release line, with the pull requests merged since the previous release. ([#100](https://github.com/Kush-Kelaiya22/imPress/issues/100))
- The prebuilt-firmware instructions use esptool 5 commands (`erase-flash`, `write-flash`). ([#96](https://github.com/Kush-Kelaiya22/imPress/issues/96))

## [varun/v2.1.0] - 2026-10-10

The first published release of the v2.1 line. The full list is in [`docs/reference/changelog-v2.1.md`](docs/reference/changelog-v2.1.md).

### Added

- Over-the-air updates for the gateway and the hub: a firmware registry that reads each image's target, chip and version; staged deployments (canary, batches, pause, resume, cancel); automatic rollback of an image that does not start. ([#33](https://github.com/Kush-Kelaiya22/imPress/issues/33), [#34](https://github.com/Kush-Kelaiya22/imPress/issues/34), [#35](https://github.com/Kush-Kelaiya22/imPress/issues/35), [#36](https://github.com/Kush-Kelaiya22/imPress/issues/36), [#37](https://github.com/Kush-Kelaiya22/imPress/issues/37), [#38](https://github.com/Kush-Kelaiya22/imPress/issues/38))
- Device health states and diagnostics (uptime, reset reason, boot count, free memory, hub link), and a list of every student module. ([#39](https://github.com/Kush-Kelaiya22/imPress/issues/39), [#40](https://github.com/Kush-Kelaiya22/imPress/issues/40))
- CSV import of quiz questions, courses and sections, with a preview before anything is saved. ([#31](https://github.com/Kush-Kelaiya22/imPress/issues/31), [#32](https://github.com/Kush-Kelaiya22/imPress/issues/32))
- Timed quizzes advance and end automatically; modules with a display show a countdown. ([#73](https://github.com/Kush-Kelaiya22/imPress/issues/73))
- Versioned database migrations with a backup before each upgrade. ([#41](https://github.com/Kush-Kelaiya22/imPress/issues/41))
- A tested install script, published releases with firmware and documentation files, and a backend container image. ([#42](https://github.com/Kush-Kelaiya22/imPress/issues/42), [#96](https://github.com/Kush-Kelaiya22/imPress/issues/96))
- The hardware validation plan: one test issue per area. ([#94](https://github.com/Kush-Kelaiya22/imPress/issues/94), [#95](https://github.com/Kush-Kelaiya22/imPress/issues/95))
- Contribution guide, label taxonomy and Code of Conduct. ([PR #74](https://github.com/Kush-Kelaiya22/imPress/pull/74), [PR #75](https://github.com/Kush-Kelaiya22/imPress/pull/75))

### Changed

- Quizzes and polls accept 2 to 4 options, one per module button. ([#49](https://github.com/Kush-Kelaiya22/imPress/issues/49))
- The hub no longer needs PSRAM. ([#30](https://github.com/Kush-Kelaiya22/imPress/issues/30))
- Diagrams in the README and the docs use mermaid syntax that renders on GitHub. ([#79](https://github.com/Kush-Kelaiya22/imPress/issues/79))

### Removed

- The unused `services/participation.py` module. ([#77](https://github.com/Kush-Kelaiya22/imPress/issues/77))

### Fixed

- A completed quiz or a closed poll could be started again with its old answers; a draft could be stopped. ([#76](https://github.com/Kush-Kelaiya22/imPress/issues/76))
- The hub and the gateway used incompatible SPI modes. ([#29](https://github.com/Kush-Kelaiya22/imPress/issues/29))
- A page left before it finished loading could paint over the next page. ([#51](https://github.com/Kush-Kelaiya22/imPress/issues/51))

### Security

- Each device gets its own key. Firmware signing and TLS between the devices and the server are available (both off by default). ([#66](https://github.com/Kush-Kelaiya22/imPress/issues/66))

## [2.0]

The October 2026 audit fixes (#1–#25), the test suite, CI and documentation. Details: [`docs/reference/changelog-v2.md`](docs/reference/changelog-v2.md).
