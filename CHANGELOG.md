# Changelog

All notable changes to imPress, for the people who install and use it. Each pull request adds its entries here; how to write them is in [CONTRIBUTING §14.4](CONTRIBUTING.md#144-recording-changes).

- **Sections:** `[Unreleased]` collects the changes on the integration line. Every push that passes CI is released as the next patch (for example `varun/v2.1.4`), and its release page lists the entries that are new since the previous release. A section per release keeps the history from before this file existed.
- **Categories:** **Added** (new capability), **Changed** (different behaviour of something that exists), **Removed** (no longer available), **Fixed** (a defect repaired), **Security** (a protection added or a vulnerability fixed).
- **Detail:** the per-issue engineering history, with the tests for each change, is in [`docs/reference/changelog-v2.1.md`](docs/reference/changelog-v2.1.md).

## [Unreleased]

### Fixed

- The live class page no longer keeps trying to reconnect after the server ended the teacher's access: a teacher who was signed out or deactivated is sent to the login page, and a teacher without access to the class is told so. ([#160](https://github.com/Kush-Kelaiya22/imPress/issues/160))
- The container package page shows the image description and the guide link again for multi-architecture tags: images are now pushed in OCI format, whose index can carry them. ([#136](https://github.com/Kush-Kelaiya22/imPress/issues/136))
- A brief registry error while uploading the container image no longer fails the whole release; the upload is retried. ([#136](https://github.com/Kush-Kelaiya22/imPress/issues/136))
- A gateway that cannot reach the server now says why in its serial log (server unreachable: address, 127.0.0.1 or firewall; connection refused; TLS handshake failed; device key refused) and prints the server address and TLS mode it uses at boot. A build with TLS on port 8000 shows a warning, `scripts/start.sh` warns when only the local computer can connect, and the troubleshooting guide covers the Windows Mobile Hotspot firewall. ([#132](https://github.com/Kush-Kelaiya22/imPress/issues/132))
- Pages load faster for teachers with many quizzes: every request used to read the teacher's entire quiz and answer history, and class lists loaded every quiz just to count them. In a local measurement with 3,000 answers, a typical request went from 42 ms to 3 ms. ([#133](https://github.com/Kush-Kelaiya22/imPress/issues/133))
- A super admin can no longer lock everyone out by deactivating their own account (or the last active super admin) through any API route; the request is refused with an explanation, and the database itself refuses a change that would leave no active super admin. ([#116](https://github.com/Kush-Kelaiya22/imPress/issues/116))
- The Read the Docs graph now renders at its intended `/graph/` subpage instead of colliding with Sphinx's generated page.
- Graphify now treats graph-only automation commits as derived output, preventing a manual unchanged rerun from creating another graph commit.
- A release line created on the same commit as an older release no longer gates that older release: a line's test issues apply only to releases built on it after it existed. ([#107](https://github.com/Kush-Kelaiya22/imPress/issues/107))

### Added

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

### Changed

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
