# Changelog

All notable changes to imPress, for the people who install and use it. Each pull request adds its entries here; how to write them is in [CONTRIBUTING §14.4](CONTRIBUTING.md#144-recording-changes).

- **Sections:** `[Unreleased]` collects the changes on the integration line. Every push that passes CI is released as the next patch (for example `varun/v2.1.4`), and its release page lists the entries that are new since the previous release. A section per release keeps the history from before this file existed.
- **Categories:** **Added** (new capability), **Changed** (different behaviour of something that exists), **Removed** (no longer available), **Fixed** (a defect repaired), **Security** (a protection added or a vulnerability fixed).
- **Detail:** the per-issue engineering history, with the tests for each change, is in [`docs/reference/changelog-v2.1.md`](docs/reference/changelog-v2.1.md).

## [Unreleased]

### Added

- `CHANGELOG.md`, kept by every pull request. A CI check fails a pull request that doesn't add an entry, unless it has the `no-changelog` label. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- Releases for every owner's integration line (`kush/v2.1`, `aamna/v2.1`, `encrypted/v2.1`), not only `varun/v2.1`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- A "Setup problems" section in the troubleshooting guide, linked from the release page. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- Test issues for a release line also gate every release built on top of it, by any owner. Closing such an issue updates all of those releases at once. Issues inherited from another line are marked *from* in the release's test table. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The first release of a line creates its milestone (for example `aamna/v2.4`) automatically. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- A container image tag per release line (`varun-2.1`, `aamna-2.4`) that points at the line's newest release. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))

### Changed

- Releases are named after their integration line and owner, for example `varun/v2.1.4`. Download files are `impress-varun-2.1.4.zip`, and container image tags are `varun-2.1.4`, `varun-2.1`, `varun-latest` and `varun-beta`. The earlier releases were renamed to `varun/v2.1.0`, `varun/v2.1.2` and `varun/v2.1.3`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The release page has a fixed structure that puts installation, setup, first use and setup troubleshooting first. Its change summary lists what was added, changed, removed and fixed, taken from `CHANGELOG.md`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The release test table is more compact, and its columns are now **No.**, **Issue**, **Assigned to** and **Status**. A Stable release shows a **Note** box. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The milestone that gates a release is named after its line, for example `varun/v2.1`. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))
- The line of a release comes from its branch name, and the release rules and page templates always come from the default branch, so any owner's line releases without extra setup. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))

### Removed

- The *Unreleased changes* list in `CONTRIBUTING.md`. Its entries moved to this file. ([#104](https://github.com/Kush-Kelaiya22/imPress/issues/104))

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
