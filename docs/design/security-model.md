# Security model

## Assets

| Asset | Why it matters |
|---|---|
| Student PII (names, emails, phones, enrollment numbers) | privacy, regulatory exposure |
| Quiz and poll results, attendance | academic integrity |
| Admin and teacher accounts | full control of classes, users and firmware |
| Device API key | lets its holder impersonate every gateway (submit data, download firmware) |
| Firmware images | code execution on classroom hardware |

## Trust boundaries

```mermaid
flowchart LR
    subgraph Untrusted["Untrusted radio (anyone nearby)"]
        M["ESP-NOW mesh"]
    end
    subgraph LAN["Classroom Wi-Fi (semi-trusted)"]
        GW["C6 gateway"]
        HUB["S3 hub (OTA hop)"]
    end
    subgraph Internet["Network to the server"]
        BR["Browsers"]
    end
    subgraph Server["Backend host (trusted)"]
        API["FastAPI"] --- DB[("SQLite")]
    end
    M -- "no authentication on air" --> HUB
    GW -- "X-API-Key (own device key; shared key only to enrol)" --> API
    HUB -- "X-API-Key" --> API
    BR -- "session token (TLS)" --> API
```

## Authentication and authorization

| Principal | Mechanism | Details |
|---|---|---|
| Users | Opaque server-side **sessions** | `POST /api/auth/login` issues `impress_<urlsafe 64>`. Only `sha256(token)` is stored (`user_sessions.token_hash`; the legacy `session_token` column also holds the hash, #12). Validation checks revoked → hard expiry (6 h) → idle expiry (60 min) → user active. Logout revokes. |
| Roles | `teacher` < `admin` < `super_admin`, closed `Literal` set | Only a super admin can grant or remove admin-level roles; nobody changes their own role (#10). Teachers only see and operate their classes: one access rule (primary teacher, co-faculty, admin) for class, quiz, poll and results routes (#20, #21). |
| Gateways and hubs | Shared `X-API-Key` | Constant-time comparison (`secrets.compare_digest`). WebSocket: `X-API-Key` header (the legacy `?api_key=` still accepted) (#11). |
| Teacher WebSocket | `?token=` = the login session token | Same validator as REST, no activity refresh (#8). Requires `wss://` in deployment, because browsers can't set WS headers. |
| Students | **None on air** | ESP-NOW frames are unauthenticated; identity is the enrollment number inside the payload. |

## Threats and mitigations

| # | Threat | Mitigation | Status |
|---|---|---|---|
| T1 | Default credentials (`admin`/`admin123`, published secrets) | Random first-run admin password; startup **refuses** default `JWT_SECRET` / `DEVICE_API_KEY` unless `DEBUG` (#11) | ✅ |
| T2 | Session theft from a DB copy / backup / git history | Hash-only token storage; legacy raw rows revoked at startup (#12) | ✅ (history purge pending, see the [deployment guide](../guides/deployment.md)) |
| T3 | Privilege escalation admin → super_admin | Closed role set + grant rules (#10) | ✅ |
| T4 | Ballot stuffing via anonymous endpoints | `/vote`, `/answer` require the device key and a registered device; option range checked (#9) | ✅ |
| T5 | Duplicate or forged answers via the gateway path | Backend validates active quiz/poll, question, option, known student; one row per student (#6) | ✅ |
| T6 | Cross-origin requests from malicious sites | CORS restricted to `CORS_ORIGINS` (#11); bearer tokens are not cookies, so CSRF doesn't apply | ✅ |
| T7 | Secrets in logs | SQL echo off by default; the C6 no longer logs the API key (#11) | ✅ |
| T8 | Malicious firmware via OTA | Download only of the version an admin pushed to that device (#13); app **rollback** on boot failure (#13); **signed images** (#66): with the signed-app profile each device verifies every update's RSA-3072 signature against the site key in `esp_ota_end()`, and with `IMPRESS_FIRMWARE_SIGNING_KEY` the backend refuses unsigned or foreign images at upload | ✅ with the signed profile and site key in use (both opt-in: the key is each site's own). Physical attacks need hardware Secure Boot (not enabled) |
| T9 | Radio spoofing: a rogue device sends answers with someone else's enrollment number | Answers count only for enrolled students and only once each. **No cryptographic protection on air.** | ⚠️ accepted risk |
| T10 | Radio flooding / jamming | De-dup and bounded queues keep nodes alive; jamming can't be prevented in 2.4 GHz | ⚠️ accepted risk |
| T11 | Path traversal via firmware version/type | Stored files are named by their SHA-256 only (`artifact_path` refuses anything else); versions are strict semver; tested | ✅ |
| T14 | Wrong, corrupt or foreign image offered to devices | Uploads are parsed as ESP-IDF app images (chip, project, semver version, appended SHA-256, slot size) and registered immutably (#35); downloads come from the registry, for the device's own type, with `X-Firmware-SHA256` | ✅ (authenticity: T8) |
| T12 | Teacher takes over another teacher's class with its join code | Joining by code only adds co-faculty; the primary teacher is never replaced (#19) | ✅ |
| T13 | Reading other classes' questions, answers and results by enumerating ids | Quiz/poll details and results require class access (#20) | ✅ |
| T15 | Impersonating a device with the shared key (a leaked key, or one read from any device's flash) | Per-device keys (#66): a device registers with the shared key and is issued its own; once used, only that key can act for its MAC, and only for that MAC. Admins can reset one device's key or disable one device without touching the others. `IMPRESS_DEVICE_KEYS_REQUIRED=true` limits the shared key to registration | ✅ (an unclaimed or reset device can still be claimed by whoever holds the shared key first) |

## Residual risks and recommended hardening

1. ~~Sign OTA images~~: done in #66 (T8): `scripts/firmware_key.sh`, `scripts/build_signed.sh`, `IMPRESS_FIRMWARE_SIGNING_KEY`. See the [OTA guide](../guides/ota-updates.md#signing-images). Hardware Secure Boot V2 (irreversible) remains an option against physical attackers.
2. **TLS everywhere:** a reverse proxy for the backend, plus `cert_pem` in the firmware HTTP clients.
3. ~~Per-device API keys~~: done in #66 (T15). Turn on `IMPRESS_DEVICE_KEYS_REQUIRED` once every device runs firmware with per-device keys.
4. **Message authentication on the mesh** (e.g. a per-class key and HMAC over the frame) if answer spoofing becomes a concern. ESP-NOW also supports encrypted unicast peers, but not encrypted broadcast.
5. **Purge git history** of the databases committed before v2 and rotate the affected passwords.

## Data handling

- Runtime data (`*.db`, `firmware_bins/`, `.env`, logs) is git-ignored. CI fails if a database is tracked (`test_session_token_storage.py::test_no_databases_tracked_in_git`).
- Activity logs record actor, action, entity and small detail dicts. They don't contain passwords or tokens.
- The student firmware caches name/program/email in NVS but only ever **transmits** the enrollment number.
