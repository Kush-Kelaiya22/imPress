# Development setup

## Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| Python | 3.12+ (3.14 tested locally) | backend, tests |
| Node.js | 20 | React dev UI (optional) |
| C compiler (clang or gcc) | any recent | firmware **host** tests (no ESP-IDF needed) |
| ESP-IDF | **v6.1** | building/flashing firmware; or use the Docker image `espressif/idf:v6.1` |
| Docker | any | IDF builds without installing IDF |

## 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                      # runtime deps + pytest/httpx

cat > .env <<'EOF'
IMPRESS_DEBUG=true                       # allows the published default secrets locally
IMPRESS_INITIAL_ADMIN_PASSWORD=dev-admin # first-run admin password (else random, printed once)
IMPRESS_SQL_ECHO=false
EOF

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **UI:** <http://localhost:8000>. Log in as `admin` with your `IMPRESS_INITIAL_ADMIN_PASSWORD`.
- **API explorer:** <http://localhost:8000/docs> (Swagger) or `/redoc`.
- **Database:** `backend/impress.db` (git-ignored). Delete it for a fresh start; tables and the admin are recreated on boot.
- Always start uvicorn **from `backend/`**: the DB path, `.env` and `firmware_bins/` are relative to the working directory.

### Seed some data quickly

```bash
TOKEN=$(curl -s localhost:8000/api/auth/login -H 'content-type: application/json' \
  -d '{"username":"admin","password":"dev-admin"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
H="Authorization: Bearer $TOKEN"
curl -s localhost:8000/api/admin/classes -H "$H" -H 'content-type: application/json' -d '{"name":"Physics","code":"PHY101"}'
curl -s -X POST localhost:8000/api/classes/1/activate -H "$H"
curl -s localhost:8000/api/students/ -H "$H" -H 'content-type: application/json' -d '{"roll_number":"ABCDE12345","student_name":"Asha Rao"}'
```

### Simulate a gateway without hardware

```bash
K='X-API-Key: impress-device-key-2024'   # the debug default; use your IMPRESS_DEVICE_API_KEY otherwise
curl -s localhost:8000/api/device/register -H "$K" -H 'content-type: application/json' \
  -d '{"mac_address":"48:F6:EE:00:00:01","device_type":"c6","device_name":"sim"}'
curl -s localhost:8000/api/device/batch -H "$K" -H 'content-type: application/json' \
  -d '{"device_type":"c6","messages":[{"type":"student_join","enrollment_number":"ABCDE12345","device_mac":"48:F6:EE:00:00:01"}]}'
```

To receive commands like a C6, connect a WebSocket client to `ws://localhost:8000/ws/class/1?role=device` with the `X-API-Key` header (e.g. `websocat -H "X-API-Key: …" ws://…`), then start a quiz in the UI.

## 2. React dev UI (optional)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 — proxies /api and /ws to :8000
```
`IMPRESS_CORS_ORIGINS` already includes `http://localhost:5173`.

## 3. Firmware

### Build without installing ESP-IDF
```bash
docker run --rm -v "$PWD/firmware":/project -w /project/class_c6 espressif/idf:v6.1 idf.py build
# repeat with class_s3 / student
```

### Native ESP-IDF
```bash
. $IDF_PATH/export.sh
cd firmware/class_c6
idf.py menuconfig        # "imPress C6 Gateway Configuration": Wi-Fi, backend host/port, API key
idf.py -p /dev/ttyUSB0 flash monitor
```
- Point `BACKEND_HOST` at your laptop's LAN IP, not `localhost`.
- The C6 console is on its **UART** port (GPIO16/17); GPIO12/13 (native USB) are used as SPI ready lines (see [hardware](../reference/hardware.md)).
- `firmware/read_serial.ps1` / `send_serial.ps1` are Windows helpers for COM ports.

### Host tests (fast, no IDF)
```bash
firmware/run_host_tests.sh            # all C suites with ASan/UBSan
python -m pytest -q firmware/tests    # structural guards
```

## 4. Before you push

```bash
python -m pytest -q backend/tests firmware/tests && firmware/run_host_tests.sh
```
CI runs the same suites plus IDF builds and the frontend build (see [testing](testing.md)).

## Repository hygiene

- Never commit `*.db`, `.env`, `firmware/*/build/`, `node_modules/` or logs. `.gitignore` covers them, and a backend test fails if a database becomes tracked.
- Line endings are LF (`.gitattributes`); keep editors from converting `*.sh` to CRLF.
