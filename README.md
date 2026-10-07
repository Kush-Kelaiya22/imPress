# imPress — ESP32 Classroom Participation System

imPress lets students answer live quizzes and polls from small ESP32 "clicker" modules. The modules form an ESP-NOW mesh inside the classroom. A classroom hub (ESP32-S3) collects their traffic and hands it over a 4 KB SPI link to a gateway (ESP32-C6), which talks to a FastAPI backend over Wi-Fi. Teachers run the class from a browser dashboard that updates in real time over WebSockets.

> **About this branch (`v2`).** `v2` is `main` plus every fix from the October 2026 repository audit (GitHub issues #1–#16). Each fix lives on its own `fix/*` branch and is merged here with `--no-ff`. `v2` is **not** merged into `main`. See [What changed in v2](#what-changed-in-v2) for the full list.

---

## Table of contents

1. [How it works](#how-it-works)
2. [Repository layout](#repository-layout)
3. [Quick start (backend + UI on a laptop)](#quick-start-backend--ui-on-a-laptop)
4. [Backend](#backend)
   - [Configuration reference](#configuration-reference)
   - [Authentication, sessions and roles](#authentication-sessions-and-roles)
   - [HTTP API reference](#http-api-reference)
   - [WebSocket API](#websocket-api)
   - [Data model](#data-model)
5. [Frontends](#frontends)
6. [Hardware](#hardware)
   - [Boards and roles](#boards-and-roles)
   - [S3 ↔ C6 wiring](#s3--c6-wiring)
   - [Student module pins](#student-module-pins)
7. [Firmware](#firmware)
   - [Toolchain](#toolchain)
   - [Building and flashing](#building-and-flashing)
   - [Device configuration (menuconfig + NVS)](#device-configuration-menuconfig--nvs)
   - [Provisioning a student module](#provisioning-a-student-module)
8. [Wire protocols](#wire-protocols)
9. [End-to-end flows](#end-to-end-flows)
10. [Over-the-air updates (OTA)](#over-the-air-updates-ota)
11. [Testing](#testing)
12. [Continuous integration](#continuous-integration)
13. [Security model and deployment checklist](#security-model-and-deployment-checklist)
14. [Troubleshooting](#troubleshooting)
15. [What changed in v2](#what-changed-in-v2)
16. [Known limitations and follow-ups](#known-limitations-and-follow-ups)

---

## How it works

```
 ┌──────────────┐  ESP-NOW broadcast, multi-hop relay (TTL 5)
 │ Student ESP32│◄───────────────────────────────────────────┐
 │ buttons A–D, │                                             │
 │ OLED (opt.)  │──────────────┐                              │
 └──────────────┘              ▼                              │
 ┌──────────────┐     ┌──────────────────┐   4096-byte    ┌───┴──────────────┐   Wi-Fi    ┌──────────────────┐
 │ Student ESP32│────►│ ESP32-S3 (hub)   │  full-duplex   │ ESP32-C6         │  HTTP +    │ FastAPI backend  │
 │   (relays)   │     │ mesh root (id 0) │◄─SPI slots────►│ gateway          │◄──────────►│ SQLite, WS hub   │
 └──────────────┘     │ SPI master       │  + 2 ready     │ SPI slave        │ WebSocket  │ vanilla SPA      │
                      │ OTA via Wi-Fi hop│    lines       │ Wi-Fi STA        │            └────────▲─────────┘
                      └──────────────────┘                └──────────────────┘                     │ HTTPS/WS
                                                                                         ┌─────────┴────────┐
                                                                                         │ Teacher browser  │
                                                                                         └──────────────────┘
```

| Component | Hardware | Responsibility |
|---|---|---|
| **Student module** (`firmware/student`) | ESP32 (target `esp32`) | Shows the question or poll, reads buttons A–D + CONFIRM, sends the answer/vote, relays other students' packets. Identity = a 10-character **enrollment number** stored in NVS. |
| **Classroom hub** (`firmware/class_s3`) | ESP32-S3 | ESP-NOW mesh **root**: tracks students, de-duplicates relayed copies, batches student messages into SPI slots, broadcasts backend commands to the mesh, and performs OTA by briefly joining Wi-Fi. |
| **Gateway** (`firmware/class_c6`) | ESP32-C6 | SPI **slave** to the S3. Turns student frames into JSON and POSTs them to `/api/device/batch`, keeps a device WebSocket to the backend, and turns backend commands into mesh frames. Sends heartbeats and status pings. |
| **Backend** (`backend/`) | Any host with Python 3.12+ | REST API, WebSocket rooms per class, SQLite storage, auth, the admin/teacher SPA, firmware store for OTA. |
| **React frontend** (`frontend/`) | Browser | Optional Vite/React dashboard (development UI). The production UI is the vanilla SPA served by the backend. |

---

## Repository layout

```
backend/
  app/
    main.py              app factory, lifespan (secure-config check, DB init, admin seed), middleware
    config.py            all settings (IMPRESS_* env vars), check_secure(), api_key_ok()
    database.py          async engine, lightweight column migrations, legacy session-token scrub
    models.py            SQLAlchemy models
    schemas.py           Pydantic request/response models (Role = teacher|admin|super_admin)
    auth.py              opaque server-side sessions (hash-only storage), role dependencies
    routers/             auth, admin, classes(+/api/devices), courses, students, quizzes, polls, device
    services/            presence (online/offline sweeps), sessions cleanup, firmware store, mesh bridge
    ws/                  /ws/class/{id} handler + connection manager (role-aware)
    static/, templates/  the vanilla single-page app served at /
  tests/                 pytest suite (fresh SQLite DB per test, in-process TestClient)
  requirements.txt       runtime deps        requirements-dev.txt  + pytest/httpx
  .env.example           every setting with guidance
  migrate_utc_to_ist.py  one-time timestamp migration (historical)
firmware/
  protocol/              shared C: frame codec, SPI batch records, mesh de-dup  (+ test_host/)
  class_c6/              gateway firmware (ESP-IDF project)                     (+ test_host/)
  class_s3/              hub firmware (ESP-IDF project)
  student/               student module firmware (ESP-IDF project)
  contract/              device_ws_frames.json — backend↔C6 WebSocket contract fixture
  tests/                 source-level structural guards (pytest, no toolchain)
  run_host_tests.sh      runs every */test_host/run*.sh
  read_serial.ps1, send_serial.ps1   Windows serial helpers
frontend/                React + Vite development UI
logs/                    serial monitor captures used in the reset investigation (#1)
.github/workflows/ci.yml CI: backend, firmware static/host tests, IDF builds, frontend build
```

---

## Quick start (backend + UI on a laptop)

Requires **Python 3.12+**. All commands run from `backend/`: the default database path (`./impress.db`), the `.env` file and the firmware store are resolved relative to the working directory.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Local development: allow the published default secrets and pick an admin password.
export IMPRESS_DEBUG=true
export IMPRESS_INITIAL_ADMIN_PASSWORD='choose-something'

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> and sign in as `admin` with the password you set.

- **No `IMPRESS_INITIAL_ADMIN_PASSWORD`?** On the **first** start (empty users table) a random password is generated and printed **once** in the server log: `Initial super admin created: username=admin password=… (shown once — change it now)`.
- **Production:** don't use `IMPRESS_DEBUG=true`. Instead copy `.env.example` to `.env` and set real secrets (see [Configuration reference](#configuration-reference)). With `DEBUG=false` and default secrets the server **refuses to start** and tells you which variables to set.

For the gateway to reach the backend, run uvicorn on an address reachable from the classroom Wi-Fi (`--host 0.0.0.0`). Put that host and port into the C6 configuration (`BACKEND_HOST`/`BACKEND_PORT`).

---

## Backend

### Configuration reference

Settings come from environment variables with the `IMPRESS_` prefix, or from a `.env` file in the working directory (`backend/.env.example` documents all of them). Lists use JSON syntax.

| Variable | Default | Meaning |
|---|---|---|
| `IMPRESS_DEBUG` | `false` | Development mode. **Only** this allows the published default secrets (with a warning). |
| `IMPRESS_SQL_ECHO` | `false` | Log every SQL statement (very noisy; includes data). |
| `IMPRESS_DATABASE_URL` | `sqlite+aiosqlite:///./impress.db` | SQLAlchemy async URL. |
| `IMPRESS_JWT_SECRET` | *public default* | **Required in production.** Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. (Login sessions are opaque tokens; this secret remains for legacy JWT helpers.) |
| `IMPRESS_DEVICE_API_KEY` | *public default* | **Required in production.** Shared secret for all device endpoints and the device WebSocket. Must equal the key configured on every C6 (and S3 for OTA). |
| `IMPRESS_INITIAL_ADMIN_PASSWORD` | *(empty)* | Password for the first super admin. Empty means random, printed once. Ignored once any user exists. |
| `IMPRESS_SESSION_IDLE_MINUTES` | `60` | A session expires after this much inactivity. |
| `IMPRESS_SESSION_HARD_MINUTES` | `360` | Absolute session lifetime. |
| `IMPRESS_SESSION_WARNING_MINUTES` | `5` | The UI warns this long before the hard limit. |
| `IMPRESS_JWT_ALGORITHM` / `IMPRESS_JWT_EXPIRE_MINUTES` | `HS256` / `1440` | Legacy JWT helpers only. |
| `IMPRESS_WS_REQUIRE_AUTH` | `true` | Require auth on `/ws/class/*`. Only disable for isolated LAN debugging. |
| `IMPRESS_CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Browser origins allowed by CORS. The vanilla UI is same-origin and needs none. |
| `IMPRESS_FIRMWARE_DIR` | `./firmware_bins` | Where uploaded OTA images are stored (`<type>-<version>.bin`). |

**Background tasks** start with the app: a presence sweep every 15 s (a device is offline after 30 s without traffic) and expired-session cleanup every 5 min. All timestamps are stored as naive **IST** (`Asia/Kolkata`, UTC+05:30; see `app/timeutil.py`).

### Authentication, sessions and roles

- **Login:** `POST /api/auth/login {username, password}` returns `{access_token, token_type: "bearer", ...}`. The token is an **opaque** random string (`impress_…`). The server stores only its **SHA-256 hash**; the raw token exists only in the client. Send it as `Authorization: Bearer <token>`.
- **Expiry:** sessions expire after `SESSION_IDLE_MINUTES` of inactivity or `SESSION_HARD_MINUTES` total. Expired requests get `401` with `detail: "SESSION_EXPIRED"` and an `X-Session-Code: idle|hard` header. Ordinary API calls refresh activity; the status/polling endpoints (`/api/auth/session`, `/session-status`, `/activity`) deliberately don't, so an idle tab doesn't keep a session alive.
- **Logout** revokes the session server-side.
- **Roles:** `teacher` < `admin` < `super_admin` (closed set; anything else gets a 422).
  - Admins create and manage teachers and classes.
  - Only a **super admin** can grant or remove `admin`/`super_admin`.
  - Nobody can change their own role.
- **Devices** authenticate with the shared device key in an `X-API-Key` header (compared in constant time).

### HTTP API reference

Guard legend: **public** = no auth · **session** = any logged-in user · **teacher+** = teacher/admin/super_admin · **admin** = admin/super_admin · **device** = `X-API-Key`.

<details><summary><b>Auth</b> — <code>/api/auth</code></summary>

| Method | Path | Guard | Notes |
|---|---|---|---|
| POST | `/api/auth/login` | public | returns the session token |
| GET / PUT | `/api/auth/me` | session | profile |
| POST | `/api/auth/change-password` | session | |
| POST | `/api/auth/logout` | session | revokes the session |
| GET | `/api/auth/session`, `/api/auth/session-status` | bearer token | session info / remaining time; no activity refresh |
| POST | `/api/auth/activity` | session | explicit "user is active" ping |
</details>

<details><summary><b>Admin</b> — <code>/api/admin</code></summary>

| Method | Path | Guard |
|---|---|---|
| POST, GET | `/api/admin/users` | admin |
| POST | `/api/admin/users/import` (CSV) | admin |
| PUT, DELETE | `/api/admin/users/{user_id}` | admin |
| POST | `/api/admin/users/{user_id}/deactivate`, `/reset-password` | admin |
| POST, GET | `/api/admin/classes` | admin |
| PUT, DELETE | `/api/admin/classes/{class_id}` | admin |
| POST | `/api/admin/classes/{class_id}/assign-teacher` | admin |
| PUT | `/api/admin/classes/{class_id}/faculty` | admin |
| POST | `/api/admin/classes/{class_id}/import-students` | admin |
| GET | `/api/admin/activity` | admin |
| POST | `/api/admin/students`, `/api/admin/students/bulk` | teacher+ |
| POST | `/api/admin/classes/{class_id}/enroll`, `/enroll-bulk` | teacher+ |
| DELETE | `/api/admin/classes/{class_id}/unenroll/{student_id}` | teacher+ |
| GET | `/api/admin/students/class/{class_id}`, `/api/admin/students/{student_id}/participation` | teacher+ |
| GET | `/api/admin/modules`, `/api/admin/modules/{device_id}`, `/api/admin/classes/{class_id}/devices` | admin |
| POST | `/api/admin/modules/{device_id}/access`, `/verify`, `/unlink`, `/api/admin/modules/{node_id}/link-device` | admin |
| POST | `/api/admin/modules/{device_id}/ota` `{version}` | admin (queues OTA; prompts an S3 via its C6) |
| POST | `/api/admin/firmware/upload` (multipart `device_type`, `version`, `file`) | admin |
</details>

<details><summary><b>Classes, courses, students, live devices</b></summary>

| Method | Path | Guard |
|---|---|---|
| GET, POST | `/api/classes/` | teacher+ |
| GET, DELETE | `/api/classes/{class_id}` | teacher+ |
| GET | `/api/classes/{class_id}/presence` | teacher+ |
| POST | `/api/classes/{class_id}/activate`, `/deactivate`, `/api/classes/join` | teacher+ |
| GET | `/api/devices/live`, `/api/devices/tree` | teacher+ |
| POST | `/api/courses/` · PUT, DELETE `/api/courses/{course_id}` | admin |
| GET | `/api/courses/`, `/api/courses/{course_id}` | teacher+ |
| GET, POST | `/api/students/` · POST `/api/students/bulk`, `/api/students/import` | teacher+ |
| GET, PUT, DELETE | `/api/students/{student_id}` · DELETE `/hard-delete` · GET `/classes` | teacher+ |
| POST | `/api/students/classes/{class_id}/import-students` | teacher+ |
</details>

<details><summary><b>Quizzes and polls</b></summary>

| Method | Path | Guard | Notes |
|---|---|---|---|
| POST | `/api/quizzes/` | teacher+ | `{class_session_id, title, questions[{question_text, options[2..6], correct_option}], quiz_mode, timing_mode, question_time_limit, total_time_limit}` |
| GET | `/api/quizzes/class/{class_id}` | teacher+ | |
| GET | `/api/quizzes/{quiz_id}`, `/results` | session | |
| POST | `/api/quizzes/{quiz_id}/start`, `/next`, `/stop` | teacher+ | broadcasts `quiz_question` / `quiz_end` |
| POST | `/api/quizzes/{quiz_id}/answer` | **device** | `{device_id, selected_option}`; the device must be registered and the option in range |
| POST | `/api/polls/` | teacher+ | `{class_session_id, title, options[2..6], poll_mode: live|planned}` |
| GET | `/api/polls/class/{class_id}` | teacher+ | |
| GET | `/api/polls/{poll_id}`, `/results` | session | |
| POST | `/api/polls/{poll_id}/start`, `/end` | teacher+ | broadcasts `poll_start` / `poll_end` |
| POST | `/api/polls/{poll_id}/vote` | **device** | same validation as answers |
</details>

<details><summary><b>Device (gateway) endpoints</b> — <code>/api/device</code>, all require <code>X-API-Key</code></summary>

| Method | Path | Body / notes |
|---|---|---|
| POST | `/register` | `{mac_address, device_type: c6|s3|student, device_name, firmware_version?, classroom_code?}` returns `{device_id, status, class_id}`. A gateway auto-links to the class matching `classroom_code`, else to the first **active** class. |
| POST | `/heartbeat` | `{mac_address, battery_pct, rssi, firmware_version, student_count, free_heap, total_flash}` |
| POST | `/ping` | 2-minute classroom status: `{mac_address, class_id, student_count, uptime_s, rssi, free_heap}` |
| POST | `/batch` | `{device_type, messages[]}`, where each message has a `type`: `heartbeat`, `student_join`, `student_leave`, `quiz_answer`, `poll_vote`. Answers/votes are stored only for a known student and an active quiz/poll with a valid question and option, **once** per student. Returns `{status, processed, skipped}`. |
| POST | `/attendance` | `{enrollment_number, class_code, mac_address?}` |
| POST | `/firmware/check` | `{mac_address, current_version}` returns `{update_available, version, ota_status, current_version}` |
| GET | `/firmware/download?mac_address=&version=` | only the version an admin pushed to **that** device (otherwise 403) |
| POST | `/firmware/applied` | `{mac_address, version}` |
</details>

`GET /health` returns `{"status":"healthy"}`. Every other non-API path serves the SPA (`templates/index.html`).

### WebSocket API

`ws(s)://<host>/ws/class/{class_id}?role=teacher|device`

| Role | Authentication |
|---|---|
| `teacher` | `?token=<login session token>`, validated exactly like the REST API (revoked, idle- or hard-expired sessions and inactive users are refused), plus role teacher/admin/super_admin |
| `device` | `X-API-Key: <device key>` header (preferred), or the legacy `?api_key=` query for old firmware |

A rejected socket is closed with code **4401** (or **4400** for an unknown role). After connecting, the server sends `{"event":"connected","class_id":…,"role":…}`.

**Server → clients** (every frame carries `type` for the vanilla UI; device-relevant ones also carry `event`):

| `event` | `type` | Key fields | Consumers |
|---|---|---|---|
| `quiz_question` | `quiz_question` | `quiz_id, question_order, question_text, options, time_limit_s` (+ `title, total_questions, timing_mode, time_limit`) | C6 → mesh, React, vanilla UI |
| `quiz_end` | `quiz_ended` | `quiz_id, title` | C6, UIs |
| `poll_start` | `poll_started` | `poll_id, title, options` | C6, UIs |
| `poll_end` | `poll_ended` | `poll_id, title, option_counts, total_votes` | C6, UIs |
| – | `quiz_answer` | `quiz_id, question_order, total_answers` | UIs (live counts) |
| – | `poll_vote` | `poll_id, selected_option, total_votes` | UIs |
| `presence` | `presence` | device online/offline snapshot | teachers only |
| `device_command` | – | `command, payload` (e.g. `ota_update {version, device_type, mac_address}`) | C6 |

**Clients → server:** `{"event":"ping"}` gets `{"event":"pong"}`; `broadcast_command` (teacher → devices); `device_data` (device → teachers). Any message from a device refreshes its presence.

The exact frames the C6 relies on are pinned in `firmware/contract/device_ws_frames.json`. `backend/tests/test_device_ws_contract.py` checks the backend against it, and `firmware/class_c6/test_host/test_ws_command.c` checks the firmware. A contract change fails CI on whichever side drifted. Regenerate the fixture after an intentional change with `IMPRESS_UPDATE_CONTRACT=1 pytest backend/tests/test_device_ws_contract.py`.

### Data model

`users` (role, is_active) · `user_sessions` (token_hash; `session_token` is a legacy column that holds the hash too) · `courses` · `class_sessions` (code, classroom_code, schedule, exam dates, `device_id` = linked gateway, `is_active`) · `class_faculty` · `students` (`roll_number` = enrollment number, primary identity) · `student_enrollments` · `quizzes` / `quiz_questions` / `quiz_answers` · `polls` / `poll_votes` · `attendance` · `esp_devices` (mac, type, firmware/pending version, OTA status, presence, `gateway_id`) · `activity_logs`.

Tables are created on startup. `database._migrate_columns()` adds known new columns to existing SQLite files. There is no Alembic, so destructive schema changes need a manual migration.

---

## Frontends

- **Vanilla SPA (production):** `backend/app/templates/index.html` + `backend/app/static/js/{api,app}.js`, served by the backend at `/`. It stores the session token in `localStorage['impress_token']` and opens the class WebSocket on the same host.
- **React dev UI (`frontend/`):** Vite + React 18.
  ```bash
  cd frontend && npm install && npm run dev      # http://localhost:5173, proxies /api and /ws to :8000
  npm run build                                  # production bundle in frontend/dist
  ```
  It stores the token in `localStorage['token']`, connects the WebSocket to the page's own host (through the Vite proxy in development) and sends `?token=`. Add its origin to `IMPRESS_CORS_ORIGINS` if it is served from a different origin than the API.

---

## Hardware

### Boards and roles

| Project | `CONFIG_IDF_TARGET` | Flash / partitions |
|---|---|---|
| `class_c6` | `esp32c6` (single-core RISC-V) | 8 MB: `nvs` 24 K, `otadata`, `phy_init`, `ota_0`/`ota_1` 3.875 MB each |
| `class_s3` | `esp32s3` | 32 MB: `ota_0`/`ota_1` 4 MB each; **app rollback enabled** |
| `student` | `esp32` | 4 MB: `ota_0`/`ota_1` 1.75 MB each |

### S3 ↔ C6 wiring

The SPI bus runs at 80 MHz (quad lines defined). Both sides exchange one fixed **4096-byte** slot per transaction. Two **active-high** ready lines tell the other side that a frame is waiting.

| Signal | S3 (master) GPIO | C6 (slave) GPIO |
|---|---|---|
| SCLK | 12 | 2 |
| MOSI | 11 | 7 |
| MISO | 13 | 6 |
| CS | 10 | 10 |
| WP / IO2 | 14 | 3 |
| HD / IO3 | 9 | 4 |
| READY S3→C6 ("S3 frame queued") | 16 (out) | 12 (in) |
| READY C6→S3 ("C6 frame queued") | 15 (in, pull-down, rising-edge IRQ) | 13 (out) |
| GND | GND | GND |

> ⚠️ On the ESP32-C6, **GPIO12/13 are the USB D-/D+ pins** of the built-in USB-Serial-JTAG. Configuring them as ready lines disconnects the native USB port at boot. **Use the UART (CP210x/CH34x) port** of the C6 board for flashing and the serial monitor (the console is on GPIO16/17), or move the ready lines in `class_c6/main/config.h` **and** `class_s3/main/config.h`.

### Student module pins

From `firmware/student/main/config.h`, for the buttons-only board:

| Function | GPIO |
|---|---|
| Button A / B / C / D | 4 / 16 / 18 / 22 |
| CONFIRM | 23 |
| Status LED (`STUDENT_HAS_LED`, default 0) | 2 |
| SSD1306 OLED SDA / SCL (`STUDENT_HAS_DISPLAY`, default 0) | 8 / 9 (I²C 400 kHz) |

Buttons are active-low with internal pull-ups. A pin the flash bus owns is detected and skipped at boot. **The pin map is for the classic ESP32**: GPIO22–25 don't exist on the ESP32-S3, so adjust the map if you build students for another target.

---

## Firmware

### Toolchain

All three projects target **ESP-IDF v6.1**, the version used in CI and by the `espressif/idf:v6.1` Docker image. The C6 depends on registry components `espressif/esp_websocket_client ^1.8.0` and `espressif/cjson ^1.7.19` (vendored under `managed_components/`, pinned by `dependencies.lock`). All projects pull the shared `firmware/protocol` component via `EXTRA_COMPONENT_DIRS`.

### Building and flashing

```bash
# Native ESP-IDF install
. $IDF_PATH/export.sh
cd firmware/class_c6        # or class_s3 / student
idf.py build
idf.py -p <PORT> flash monitor

# Or without installing anything (same image as CI)
docker run --rm -v "$PWD/firmware":/project -w /project/class_c6 espressif/idf:v6.1 idf.py build
```

The committed `sdkconfig` files are authoritative; `sdkconfig.defaults` only seeds a fresh configuration. After changing bootloader options (e.g. rollback on the S3), flash the **full** image over serial once (`idf.py flash`), because OTA cannot update the bootloader.

### Device configuration (menuconfig + NVS)

Kconfig values (`idf.py menuconfig` → *imPress … Configuration*) are written to NVS on first boot. **Values in NVS win afterwards**, so you can re-provision without reflashing.

| Setting | C6 Kconfig | C6 NVS key (`impress`) | S3 Kconfig | S3 NVS key (`s3_cfg`) |
|---|---|---|---|---|
| Wi-Fi SSID / password | `WIFI_SSID`, `WIFI_PASSWORD` | `wifi_ssid`, `wifi_pass` | same | `wifi_ssid`, `wifi_pass` |
| Backend host / port | `BACKEND_HOST` (`192.168.137.1`), `BACKEND_PORT` | `backend_h`, `backend_p` | `BACKEND_HOST` (`192.168.1.100`), `BACKEND_PORT` | `backend_host`, `backend_port` |
| Device API key | `DEVICE_API_KEY` | `api_key` | `DEVICE_API_KEY` | `api_key` |
| Class id | `CLASS_SESSION_ID` (0 = auto) | `class_id` | – | `class_id` |
| Timing | `HEARTBEAT_INTERVAL_S` (15), `STATUS_PING_INTERVAL_S` (120), `SPI_BATCH_MAX_WAIT_MS` (500), `BATCH_MAX_SIZE` (20), `WS_PING_INTERVAL_S` | – | `HEARTBEAT_INTERVAL_MS` (5000), `STUDENT_TIMEOUT_MS` (60000), `SPI_POLL_INTERVAL_MS` (50) | – |
| Mesh channel | – | – | `MESH_WIFI_CHANNEL` (1) | – |
| Battery ADC | `BATTERY_ADC_EN`, `BATTERY_ADC_GPIO` | – | – | – |

The Kconfig defaults (`impress-hotspot` / `impress123`, `impress-device-key-2024`) are **development values** published in this repository. Change them for any real deployment, and make `DEVICE_API_KEY` equal the backend's `IMPRESS_DEVICE_API_KEY`. The student mesh channel is `MESH_WIFI_CHANNEL` in `student/main/config.h` and must match the S3.

### Provisioning a student module

A student module is identified **only** by its 10-character alphanumeric enrollment number (`^[A-Za-z0-9]{10}$`, matching the backend's roll number), stored in NVS key `enroll`. `0000000000` is the "unprovisioned" placeholder. An unprovisioned device listens to the mesh but never joins or answers. Ways to set the number:

1. **Buttons:** A = next character, B = previous character, C = backspace, D = clear, CONFIRM = commit; the 10th CONFIRM saves.
2. **Serial:** type the enrollment number and press Enter on the USB console.
3. **Factory:** write the `enroll` NVS key in a batch (survives OTA).

To **re-provision**, hold **CONFIRM + C** for 2 s during boot. The identity is set-once and never overwritten silently.

---

## Wire protocols

All multi-byte payload fields are **little-endian packed structs** (`firmware/protocol/protocol.h`) unless stated otherwise.

1. **Protocol frame** (every hop): `[0xAA][TYPE:1][LEN:2 BE][PAYLOAD:LEN ≤ 240][CRC16:2 BE]`
   - CRC-16/CCITT (poly 0x1021, init 0xFFFF) over TYPE+LEN+PAYLOAD; maximum 246 bytes.
   - Types: `HEARTBEAT 0x01`, `STUDENT_JOIN 0x02`, `STUDENT_LEAVE 0x03`, `ATTENDANCE 0x04`, `QUIZ_START/QUESTION/ANSWER/END 0x10–0x13`, `POLL_START/OPTIONS/VOTE/END 0x20–0x23`, `ACK/NACK 0x30/0x31`, `SPI_AGGREGATE/COMMAND/STATUS 0x40–0x42`, `OTA_PROMPT/APPLIED 0x50/0x51`.
2. **Mesh header** (ESP-NOW, before the frame): `[TTL:1][SENDER_ID:4][HOPS:1]`, with TTL starting at 5.
   - `SENDER_ID` 0 = the S3 root; students use a MAC-derived id (routing only).
   - Students relay anything with TTL > 1 after a 10–60 ms random delay.
   - **De-duplication** uses `mesh_msg_id(sender_id, frame)`, never TTL/hops, with a 10 s window on every student and on the root. One press therefore costs N transmissions in an N-student room and reaches the backend **once**.
3. **SPI slot** (S3 ↔ C6, both directions): `[LEN:2 BE][PAYLOAD:LEN ≤ 4092][CRC16-XMODEM over payload:2 BE][zero padding to 4096]`. An all-zero slot means "nothing".
4. **SPI batch record** (inside an S3→C6 slot payload, repeated): `[FRAME_LEN:2 BE][SENDER_ID:4 LE][FRAME]`, where `FRAME_LEN` counts the frame **only**. It is produced and parsed exclusively by `spi_record_write()` / `spi_record_read()`. C6→S3 slot payloads are single protocol frames.
5. **Device WebSocket JSON:** see [WebSocket API](#websocket-api).
6. **C6 → backend:** HTTP JSON, `X-API-Key` header; see the device endpoints table.

---

## End-to-end flows

**Teacher starts a quiz question**
1. `POST /api/quizzes/{id}/start` → backend broadcasts `{"event":"quiz_question",…}` to the class room.
2. The C6's `ws_command_to_frame()` builds `MSG_QUIZ_QUESTION` (`payload_quiz_question_t`, options clamped to 4 buttons) and posts it in its SPI slot, raising READY C6→S3.
3. The S3 clocks the slot and `mesh_master_broadcast()` sends it with TTL 5.
4. Students deliver it (from `sender_id 0`, direct or relayed), show it on the OLED and arm the buttons.

**Student answers**
1. The button press triggers `MSG_QUIZ_ANSWER` `{quiz_id, question_num, selected_option, enrollment}` into the mesh.
2. The S3 receives one or more copies, refreshes its routing table, de-duplicates, and queues `[id][frame]`.
3. `mesh_master_flush_to_spi()` writes SPI batch records → the C6 parses them → JSON `quiz_answer` → batch → `POST /api/device/batch`.
4. The backend validates and de-duplicates, stores a `QuizAnswer`, and broadcasts `{"type":"quiz_answer","total_answers":n}` to teachers.

**Joining the mesh**
1. The student sends `MSG_STUDENT_JOIN` every 2 s.
2. The S3 replies with a root heartbeat (TTL 5), which sets `IS_CONNECTED` on the student. It also forwards the join to the backend (`student.connect` activity, class enrollment when a class code is known).
3. Students idle for `STUDENT_TIMEOUT_MS` are swept, producing `MSG_STUDENT_LEAVE` → `student.disconnect`.

---

## Over-the-air updates (OTA)

**S3 hub**
1. Admin: `POST /api/admin/firmware/upload` (multipart `device_type=s3`, `version=X.Y.Z`, `file`), which stores `s3-X.Y.Z.bin`.
2. Admin: `POST /api/admin/modules/{s3_id}/ota {"version":"X.Y.Z"}`. This sets `pending_version` and sends `device_command ota_update` to the class room of the S3's C6 gateway (`gateway_id`).
3. The C6 relays `MSG_OTA_PROMPT` to the S3. The S3 temporarily joins Wi-Fi, registers, calls `/firmware/check` and downloads `/firmware/download` (only the pending version is served), writes the inactive slot and reboots.
4. On first boot the new image is `PENDING_VERIFY`. `app_main` marks it valid **only after mesh + SPI init succeed**; otherwise the bootloader rolls back automatically.
5. With nothing pending, Wi-Fi unreachable, or a failed download, the S3 **does not reboot**: it detaches from Wi-Fi, restores the mesh channel and carries on.

**Hardening that is not enabled by default** (needs decisions and keys that must never be committed):
- **Signed apps:** `espsecure.py generate_signing_key --version 2 secure_boot_signing_key.pem` (keep it offline), then enable `CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT` (or Secure Boot v2, which burns eFuses irreversibly) and point `CONFIG_SECURE_BOOT_SIGNING_KEY` at the key. `esp_ota_end()` then rejects unsigned images.
- **HTTPS** for OTA/API: serve the backend behind TLS and give `esp_http_client` the CA certificate (`cert_pem`).

---

## Testing

```bash
# Backend (from repo root; uses a temp SQLite DB per test, no server needed)
pip install -r backend/requirements-dev.txt
python -m pytest -q backend/tests

# Firmware structural guards (pure Python, no toolchain)
python -m pytest -q firmware/tests

# Firmware host tests (cc/clang + AddressSanitizer/UBSan; real firmware sources, fake IDF where needed)
firmware/run_host_tests.sh

# Real firmware builds
docker run --rm -v "$PWD/firmware":/project -w /project/class_c6 espressif/idf:v6.1 idf.py build
```

| Suite | Files | What it covers |
|---|---|---|
| Backend (63 tests) | `backend/tests/test_*.py` | auth and WS auth (#8), role escalation (#10), secure defaults and CORS (#11), session-token storage (#12), vote/answer auth (#9), batch validation and de-dup (#6), OTA download gating (#13), firmware upload (#16), class creation (#15), device WS contract (#3), smoke tests |
| Firmware structural (14 tests) | `firmware/tests/test_*.py` | C6 batch single owner (#4), no WS self-destroy (#5), API key not logged (#11), S3 config order (#7), OTA rollback/no-reboot (#13) |
| Host C | `firmware/protocol/test_host`, `firmware/class_c6/test_host` | protocol frame codec and SPI records (#2), mesh de-dup + relay-storm simulation (#6), C6 SPI slave descriptor lifetime under ASan use-after-return (#1), C6 WS command translation against the contract fixture (#3) |

**Writing tests:** `backend/tests/conftest.py` sets `IMPRESS_*` before the app is imported. The `client` fixture gives you a fresh DB and a `TestClient`; `db(lambda s: …)` runs ORM code; `login()` / `auth()` produce headers. The seeded admin password in tests is `admin123` (via `IMPRESS_INITIAL_ADMIN_PASSWORD`), and the device key is `test-device-key`. When a test waits on a WebSocket, finish with a marker broadcast and read until you see it, so a missing frame fails instead of hanging.

---

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request:

| Job | Runs |
|---|---|
| Backend tests | Python 3.12, `pytest backend/tests` |
| Firmware structural tests | `pytest firmware/tests` |
| Firmware host tests | `firmware/run_host_tests.sh` (gcc + sanitizers) |
| ESP-IDF v6.1 build | `idf.py build` for `class_c6`, `class_s3`, `student` in `espressif/idf:v6.1` |
| Frontend build | Node 20, `npm install && npm run build` |

---

## Security model and deployment checklist

- [ ] `IMPRESS_JWT_SECRET` and `IMPRESS_DEVICE_API_KEY` set to fresh random values; `IMPRESS_DEBUG=false` (the server refuses to start otherwise).
- [ ] The same device key flashed or written to NVS (`api_key`) on every C6 and S3.
- [ ] The first-run admin password changed after the first login; additional admins created by a super admin only.
- [ ] Backend served over **TLS** (reverse proxy). The teacher WebSocket token travels in the query string, as browsers can't set WS headers, so `wss://` is required.
- [ ] `IMPRESS_CORS_ORIGINS` limited to the real UI origin(s).
- [ ] Classroom Wi-Fi credentials changed from the development defaults.
- [ ] Runtime data (`*.db`, `firmware_bins/`, `.env`) kept out of version control (`.gitignore` covers them).
- [ ] **History cleanup still pending:** databases containing user and session data were committed before v2. Purge them with `git filter-repo --invert-paths --path backend/impress.db --path backend/impress.db.bak-pre-ist --path impress.db`, force-push, have collaborators re-clone, and rotate the affected passwords. Legacy raw session tokens in an existing DB are revoked automatically at startup.
- [ ] Consider signed OTA images (see [OTA](#over-the-air-updates-ota)).

---

## Troubleshooting

**An ESP32 keeps resetting.** Read the reset reason first: `rst:0x…` on the boot banner, or log `esp_reset_reason()`. Then match it below.

| Symptom in the log | Cause | Status |
|---|---|---|
| `ESP_ERROR_CHECK failed: ESP_ERR_WIFI_NOT_STARTED … esp_wifi_set_channel` then `abort()`, repeating `RTC_SW_CPU_RST` | `esp_wifi_set_channel()` called before `esp_wifi_start()` in `mesh_init` (`logs/s3_com18_monitor.log`, 536 reboots) | fixed before v2; the call is now checked and logged instead of aborting (#7) |
| C6: random `Load/Store access fault`, `CORRUPT HEAP`, or `spi2http` stops flushing once the S3 link carries traffic | SPI slave transaction descriptor lived on the stack while the driver kept using it | **fixed (#1)** |
| C6: heap corruption around heartbeats | two tasks mutated the batch cJSON tree | **fixed (#4)** |
| C6 crash right after a class reassignment | WS client destroyed from its own task | **fixed (#5)** |
| S3 reboots after every "OTA" prompt | no-op OTA used to `esp_restart()` | **fixed (#13)** |
| `Brownout detector was triggered` | supply sags during Wi-Fi TX | power/USB cable issue (detector level 7 on C6/S3) |
| `Task watchdog got triggered` | a task hogging the CPU | capture the backtrace (`idf.py monitor` decodes it) |

**C6 log shows `WiFi disconnected — retrying` every ~2.4 s.** Wrong SSID or password, an AP weaker than WPA2-PSK (the C6's minimum auth mode), or a 5 GHz-only AP (ESP32 radios are 2.4 GHz). Check `wifi_ssid`/`wifi_pass` in NVS.

**The native USB port disappears when the C6 boots.** Expected, because GPIO12/13 are used as ready lines (see [wiring](#s3--c6-wiring)). Use the UART port.

**Teacher dashboard never updates live.** Check that the browser's WS URL carries `token=` and the backend log shows no `4401`. Behind a proxy, enable WebSocket upgrades for `/ws/`.

**Students never get "Connected!".** S3 and students must share `MESH_WIFI_CHANNEL`; the S3 log prints `Mesh master initialized, channel=N`. The student must have an enrollment number (it shows "NO ID" otherwise).

**Answers don't appear.** On the C6 log look for `Batch flush N items → /api/device/batch`. The backend's `/api/device/batch` response reports `skipped` for answers to inactive quizzes, unknown enrollment numbers, or duplicates.

**Server refuses to start: "Refusing to start with default secrets".** Set the listed variables, or `IMPRESS_DEBUG=true` for local development.

---

## What changed in v2

| Issue | Severity | Fix branch | Summary |
|---|---|---|---|
| #1 | critical | `fix/c6-spi-slave-dangling-descriptor` | C6 SPI slave: static transaction descriptor, reap before re-arm (memory corruption / resets) |
| #2 | critical | `fix/2-spi-batch-record-framing` | One shared S3→C6 SPI record codec; student messages now reach the backend |
| #3 | high | `fix/3-device-command-contract` | Backend/C6/student command contract aligned (`event` keys, poll start/end, quiz end); contract fixture |
| #4 | high | `fix/4-c6-batch-single-owner` | C6 batch accumulator owned by one task |
| #8 | high | `fix/8-ws-teacher-session-auth` | Teacher WebSocket accepts session tokens; roles recorded; React client sends token |
| #9 | high | `fix/9-vote-answer-auth` | Vote/answer endpoints require device key, registered device, valid option |
| #10 | high | `fix/10-role-escalation` | Closed role set; only super admins grant admin roles |
| #11 | high | `fix/11-secure-defaults` | No public creds by default, DEBUG off, CORS from settings, constant-time key compare, key in header |
| #12 | high | `fix/12-untrack-data-hash-only-tokens` | `.gitignore`, DBs untracked, raw session tokens never stored (legacy rows revoked) |
| #5 | medium | `fix/5-c6-ws-reassign-deferred` | C6 WS restart moved out of its own event handler |
| #6 | medium | `fix/6-dedup-mesh-and-batch` | Mesh de-dup by message id, Wi-Fi callback non-blocking, validated + de-duplicated batch ingestion |
| #13 | medium | `fix/13-ota-rollback-no-noop-reboot` | S3 app rollback + mark-valid, no reboot on no-op OTA, gated firmware downloads |
| #14 | medium | `fix/14-ci-and-test-infra` | Test infrastructure + GitHub Actions |
| #15 | medium | `fix/15-class-create-500` | `POST /api/classes/` no longer 500s |
| #16 | medium | `fix/16-firmware-upload-500` | Firmware upload no longer 500s; OTA prompt audit-logged |
| #7 | low | `fix/7-s3-config-before-mesh` | S3 loads config before mesh init; `set_channel` errors reported |

Every issue on GitHub has a resolution comment with the change, the tests run (before/after output) and the safety analysis.

**Upgrading from `main`:**
1. Set `IMPRESS_JWT_SECRET` and `IMPRESS_DEVICE_API_KEY` (or `IMPRESS_DEBUG=true` locally), and put the same device key on the gateways.
2. Flash **all three** firmware images. The S3 needs a full serial flash once for the rollback-capable bootloader.
3. Existing teachers are logged out once if their sessions predate the token-hash change.

---

## Known limitations and follow-ups

- **Hardware soak not yet run on v2:** the reset fixes are verified with host tests (ASan/UBSan) and real ESP-IDF builds, but not yet on boards. Recommended: a 2-hour classroom soak with `esp_reset_reason()` logged at boot and `CONFIG_HEAP_POISONING_COMPREHENSIVE` on the C6.
- **SPI flow control:** the S3 may clock while the C6 has no slot armed (e.g. during a long HTTP POST), and that exchange is lost. A "slot armed" handshake would make the link lossless.
- **Single shared device key:** per-device keys and rotation would limit the blast radius of a leaked key.
- **No migrations framework:** SQLite schema evolution is best-effort (`_migrate_columns`). Adopt Alembic before moving to PostgreSQL.
- **Signed OTA and TLS** need deployment-specific keys and certificates (see OTA section).
- **Pre-existing compiler warnings:** unused `s_adc`/`s_adc_ready` (C6 `wifi_client.c`), `_nvs_write_str` (S3 `config.c`), `s_student_id` (student `mesh_espnow.c`).
- **React `Classes` page** creates classes with a name only. The API also requires `code`, so use the vanilla admin UI to create classes.
