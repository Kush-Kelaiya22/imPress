# Design decisions

Short records of the non-obvious choices: the context, the decision, and its consequences. New decisions go at the end.

---

### D1: Students use ESP-NOW, not Wi-Fi
**Context:** 30–300 devices per room; school APs limit clients and need credentials on every device.
**Decision:** connectionless ESP-NOW broadcast with student-to-student relaying ([mesh design](mesh.md)).
**Consequences:** no AP, no per-device credentials, instant start. Frames are unauthenticated on air (see [security model](security-model.md) T9). Payload ≤ 250 bytes.

### D2: Two radios per room (S3 root + C6 gateway) joined by SPI
**Context:** an associated Wi-Fi station must follow the AP's channel; the mesh needs a fixed channel.
**Decision:** the S3 stays on the mesh channel; the C6 does Wi-Fi; they exchange 4 KB SPI slots at 80 MHz.
**Consequences:** reliable mesh timing and burst capacity (136 answers per slot). There are two firmwares to maintain and a hardware link that needs a careful protocol ([protocols](protocols.md) ③④).

### D3: Fixed 4096-byte full-duplex slots with two ready lines
**Context:** both sides may have data at any time; variable-length SPI with a slave is error-prone.
**Decision:** every exchange is one fixed slot in both directions; ready lines signal pending data; LEN + CRC frame the payload.
**Consequences:** a simple, verifiable protocol. An exchange clocked while the C6 has no slot armed is lost (no flow control yet; [known issues](../reference/known-issues.md)).

### D4: One shared C implementation per wire format
**Context:** the S3 and C6 had diverging hand-written framing (#2).
**Decision:** `firmware/protocol` owns the frame codec, SPI records and mesh de-dup; the JSON ↔ frame mapping lives in one pure function (`ws_command.c`).
**Consequences:** host-testable (no hardware), and a change on one side can't silently break the other.

### D5: The backend ↔ firmware JSON contract is a committed fixture
**Context:** the backend renamed fields for the UI and the hardware path broke without anyone noticing (#3).
**Decision:** `firmware/contract/device_ws_frames.json` is generated from real backend output by `test_device_ws_contract.py` and consumed by the C host test `test_ws_command.c`.
**Consequences:** any contract change fails CI on whichever side changed. Intentional changes regenerate the fixture (`IMPRESS_UPDATE_CONTRACT=1`).

### D6: Enrollment number is the only student identity
**Context:** devices get swapped, lost and re-flashed.
**Decision:** the 10-alphanumeric enrollment number (stored in device NVS, `students.roll_number` in the DB) identifies the student; MAC-derived ids are routing-only.
**Consequences:** any module can be given to any student by re-provisioning (CONFIRM + C at boot). The format rule is identical in firmware (`config.c`) and backend (`schemas._valid_enrollment_number`) and tested on both sides.

### D7: Opaque server-side sessions instead of JWTs
**Context:** idle timeouts, logout and forced revocation are required.
**Decision:** random opaque tokens; only their SHA-256 is stored; validation is a DB lookup.
**Consequences:** instant revocation, idle and hard expiry. Every request costs one indexed lookup. `JWT_SECRET` remains only for legacy helpers.

### D8: Status/polling endpoints never extend a session
**Context:** the SPA polls session status; refreshing on poll would keep idle sessions alive forever.
**Decision:** a single activity refresh in middleware, skipped for `/session`, `/session-status`, `/activity`, `/login`, `/logout`; auth dependencies never refresh.
**Consequences:** idle timeout means *user* idle. Explicit `POST /api/auth/activity` exists for "I'm still here".

### D9: Naive IST timestamps everywhere
**Context:** a single-timezone (India) deployment and SQLite without timezone support.
**Decision:** store naive IST (`timeutil.istnow()`), convert with explicit helpers.
**Consequences:** human-readable DB values. Multi-timezone deployments would need a migration (`migrate_utc_to_ist.py` shows the pattern).

### D10: De-duplicate at every layer
**Context:** flooding creates copies; network retries create copies.
**Decision:** students de-dup relays, the root de-dups before the gateway, and the backend enforces one answer per (quiz, question, student) / (poll, student).
**Consequences:** each layer stays correct even if another misbehaves (#6).

### D11: Secure by default; developer convenience is explicit
**Context:** published default credentials made every default deployment open (#11).
**Decision:** `DEBUG=false` by default; startup refuses public secrets unless `DEBUG=true`; the first admin password is random.
**Consequences:** a fresh checkout needs `IMPRESS_DEBUG=true` (or real secrets) to start, as documented in the [development setup](../guides/development-setup.md).

### D12: OTA rollback without (yet) signing
**Context:** a bad image must not brick a hub; signing needs keys the project must manage outside git.
**Decision:** S3 app rollback with mark-valid after mesh + SPI init; images not signed by default; signing documented as a deployment step.
**Consequences:** resilience against broken builds now; integrity against malicious images once maintainers enable signing.

### D13: Single-owner rule for non-thread-safe state
**Context:** a shared cJSON tree mutated by two tasks (#4).
**Decision:** shared mutable state has one owner task; other tasks hand off via flags or queues. This is enforced by structural tests.
**Consequences:** no locks to forget, and no lock held across network I/O.
