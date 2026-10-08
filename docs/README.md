# imPress documentation

This folder is the long-form documentation for imPress. The [project README](../README.md) gives the one-page overview and quick start; everything detailed lives here.

## Map

| Section | Read it when you want to… |
|---|---|
| **[Architecture](architecture/)** | understand how the system is put together |
| ↳ [System overview](architecture/overview.md) | see every component, how they connect, and why it's split this way |
| ↳ [Backend architecture](architecture/backend.md) | work on the FastAPI service: layers, request lifecycle, background tasks |
| ↳ [Firmware architecture](architecture/firmware.md) | work on the ESP32 code: tasks, priorities, memory, state machines per board |
| ↳ [Data flows](architecture/data-flows.md) | follow a quiz, an answer, a join, presence or an OTA end to end (sequence diagrams) |
| **[Design](design/)** | understand *why* things work the way they do |
| ↳ [Wire protocols](design/protocols.md) | encode or decode any byte on any link |
| ↳ [Mesh design](design/mesh.md) | understand ESP-NOW relaying, root discovery, de-duplication, timing |
| ↳ [Security model](design/security-model.md) | reason about threats, auth, keys, sessions, OTA integrity |
| ↳ [Design decisions](design/decisions.md) | read the decision records behind non-obvious choices |
| **[API](api/)** | integrate with the backend |
| ↳ [REST API](api/rest-api.md) | call any HTTP endpoint (request/response contracts, errors) |
| ↳ [WebSocket API](api/websocket-api.md) | consume or produce live class events |
| ↳ [Device API](api/device-api.md) | implement or change gateway ↔ backend communication |
| **[Guides](guides/)** | get something done |
| ↳ [Development setup](guides/development-setup.md) | run the backend, UIs and firmware builds locally |
| ↳ [Configuration](guides/configuration.md) | look up any backend setting or device Kconfig/NVS key |
| ↳ [Deployment](guides/deployment.md) | put imPress in a real classroom |
| ↳ [CSV imports](guides/csv-imports.md) | bulk-create quiz questions, courses and sections from a spreadsheet; export sections |
| ↳ [OTA updates](guides/ota-updates.md) | ship firmware to deployed hubs and gateways |
| ↳ [Testing](guides/testing.md) | run, read or write tests; understand CI |
| ↳ [Troubleshooting](guides/troubleshooting.md) | diagnose resets, connectivity and data problems |
| **[Reference](reference/)** | look up facts |
| ↳ [Data model](reference/data-model.md) | every table, column and relationship |
| ↳ [Hardware](reference/hardware.md) | boards, pins, wiring, partitions |
| ↳ [Known issues](reference/known-issues.md) | open observations not yet fixed |
| ↳ [Changelog: v2](reference/changelog-v2.md) | what the audit fixed (#1–#25) |
| ↳ [Changelog: v2.1](reference/changelog-v2.1.md) | what v2.1 changes, issue by issue, with upgrade notes |
| **[Testing](testing/)** | understand what is tested and what isn't |
| ↳ [Test strategy](testing/TEST_STRATEGY.md) | test layers, coverage, faults covered, rules for new tests |
| ↳ [Hardware validation](testing/HARDWARE_VALIDATION.md) | bench checks per feature and their status (all *not run* so far) |
| **[Hardware](hardware/)** | choose boards for a classroom |
| ↳ [Classroom node requirements](hardware/CLASSROOM_NODE_REQUIREMENTS.md) | measured footprints; minimum, reduced-flash and high-capacity configurations; pending bench figures |
| ↳ [Device compatibility](hardware/DEVICE_COMPATIBILITY.md) | which image runs where, what OTA can and can't change, firmware ↔ backend version mixes |
| **[Firmware](firmware/)** | understand firmware delivery |
| ↳ [OTA architecture](firmware/OTA_ARCHITECTURE.md) | image validation, registry, deployment state machine, staged rollout, per-device paths |
| **[Engineering](engineering/)** | see the evidence behind the v2.1 work |
| ↳ [System audit](engineering/SYSTEM_AUDIT.md) | the v2 baseline: architecture map, device matrix, measured footprints, defects, test baseline |
| ↳ [v2/v3 comparison](engineering/V2_V3_COMPARISON.md) | what `v3` changed, why its CI failed, what v2.1 adopts or rejects |
| ↳ [Database migrations](engineering/DATABASE_MIGRATIONS.md) | how the schema is versioned and upgraded, enforced constraints, backups and restore |

## Conventions used in these docs

- **Paths** are relative to the repository root (`backend/app/routers/device.py`).
- **"Gateway"** = the ESP32-C6 (`firmware/class_c6`); **"hub"/"root"** = the ESP32-S3 (`firmware/class_s3`); **"student module"/"node"** = `firmware/student`.
- **Enrollment number** = the student's 10-character alphanumeric identity, called `roll_number` in the database and `enrollment` in firmware structs.
- **Times** in the backend are naive **IST** (UTC+05:30) unless stated otherwise.
- Diagrams are [Mermaid](https://mermaid.js.org/), which GitHub renders inline.
