# Deployment

This guide puts imPress into real classrooms: one backend server, and one S3 + C6 pair plus student modules per room.

## 1. Server

### Host and process
```bash
git clone … imPress && cd imPress/backend
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then edit, see below
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers
```
- **One worker only.** WebSocket rooms live in process memory ([backend scaling](../architecture/backend.md#scaling-and-limits)).
- Run it under a supervisor (systemd unit below) and start it **from `backend/`**.

```ini
# /etc/systemd/system/impress.service
[Unit]
Description=imPress backend
After=network.target

[Service]
WorkingDirectory=/opt/imPress/backend
EnvironmentFile=/opt/imPress/backend/.env
ExecStart=/opt/imPress/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers
Restart=always
User=impress

[Install]
WantedBy=multi-user.target
```

### `.env` for production
```bash
IMPRESS_DEBUG=false
IMPRESS_JWT_SECRET=<python -c "import secrets;print(secrets.token_urlsafe(32))">
IMPRESS_DEVICE_API_KEY=<another random value — also goes into every gateway>
IMPRESS_INITIAL_ADMIN_PASSWORD=<strong, change after first login>   # or leave empty and read it from the log once
IMPRESS_CORS_ORIGINS=["https://impress.example.edu"]
```
With `DEBUG=false` and default secrets the service **won't start**. The error names the variables to set.

### TLS reverse proxy (WebSockets included)
```nginx
server {
    listen 443 ssl;
    server_name impress.example.edu;
    # ssl_certificate …; ssl_certificate_key …;

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        access_log off;            # teacher tokens travel in the WS query string
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Gateways currently speak plain `http://`/`ws://` to `BACKEND_HOST:BACKEND_PORT`. Either expose an internal HTTP listener on the classroom VLAN, or add TLS to the firmware HTTP clients first ([security model](../design/security-model.md#residual-risks-and-recommended-hardening)).

### Backups
- `impress.db` is a single SQLite file: back it up with `sqlite3 impress.db ".backup '/backups/impress-$(date +%F).db'"` (safe while running).
- Also back up `firmware_bins/` and `.env` (store `.env` separately, it holds secrets).

## 2. First-run administration

1. Log in as `admin`, change the password, and create other admins (as super admin) and teachers.
2. Create courses, then classes (with `classroom_code` = the physical room label, e.g. `RM-201`, and the meeting schedule).
3. Import students via CSV (`roll_number,student_name,email,phone,program,enrollment_year,graduation_year`) and enroll them into classes.
4. **Activate** a class when it's in session; gateways only auto-link to active classes.

## 3. Per-room hardware

1. **Wire the S3 and C6** ([hardware reference](../reference/hardware.md#s3--c6-wiring)) and power both from a stable 5 V supply (brownout detection is on).
2. **Configure the C6:** `WIFI_SSID`/`WIFI_PASSWORD` (2.4 GHz, WPA2+), `BACKEND_HOST`/`BACKEND_PORT`, `DEVICE_API_KEY` = the server's key. Flash it.
3. **Configure the S3:** the same Wi-Fi, backend and key (used for OTA), and `MESH_WIFI_CHANNEL`. Flash the **full** image once over serial (it has the rollback bootloader).
4. **Link the room:** either set the class's `classroom_code` and register the C6 with that code, or let the C6 auto-link to the single active class without a gateway. Check it in the admin "modules" view or `GET /api/classes/{id}/presence`.
5. **Student modules:** flash `firmware/student` (with the same `MESH_WIFI_CHANNEL`) and provision each module's enrollment number (buttons or serial). Hand modules out; re-provision with CONFIRM + C at boot.

## 4. Go-live checklist

- [ ] `GET /health` OK through the proxy; HTTPS valid.
- [ ] Admin password changed; `IMPRESS_DEBUG=false`; secrets not default.
- [ ] Each room's gateway shows **online** and is linked to the right class.
- [ ] A test quiz shows on a student module, and an answer increments the live count.
- [ ] Backups scheduled.
- [ ] (Recommended) OTA signing enabled ([OTA guide](ota-updates.md#signing-images)).
- [ ] **Git history purged** of the databases committed before v2, and the passwords that were in them rotated:
  ```bash
  pip install git-filter-repo
  git filter-repo --invert-paths --path backend/impress.db --path backend/impress.db.bak-pre-ist --path impress.db
  git push --force --all && git push --force --tags      # coordinate: everyone re-clones
  ```

## 5. Upgrading

1. Back up the DB.
2. `git pull`, then `pip install -r requirements.txt`.
3. Restart the service. `init_db()` adds new tables and columns automatically; read the release notes for anything that needs a manual migration.
4. Update firmware: the S3 via [OTA](ota-updates.md); the C6 and students over serial for now.
