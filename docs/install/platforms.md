# Install imPress on a server

Choose this guide for a native Python install. For Docker Compose, persistent storage, TLS and upgrades, use the [container guide](../deployment/container.md). For a classroom, do not expose the browser interface over plain HTTP: use HTTPS as described in the [deployment guide](../guides/deployment.md#tls-reverse-proxy-websockets-included).

## Before you begin

- Use a supported 64-bit Windows, macOS or Linux computer with Python 3.12 or newer.
- For a classroom network, give the server a stable hostname or address. The gateway and hub must be able to reach it over the device API port (8000 by default).
- Keep the server on one application worker. The live classroom WebSocket rooms are in process memory.
- Back up `backend/.env`, the database, and `backend/firmware_bins/` separately. They contain secrets, classroom data and firmware artifacts.

## Linux and macOS

Open a terminal in the directory where you want the repository:

```sh
git clone https://github.com/Kush-Kelaiya22/imPress.git
cd imPress
scripts/install.sh
```

`scripts/install.sh` creates `backend/.venv`, installs backend requirements and creates `backend/.env` with random JWT and device secrets when they are missing. It preserves existing values, sets restrictive permissions on the environment file, and checks that the application imports. It is safe to rerun after an update.

Start a local-only instance for the first login and smoke check:

```sh
scripts/start.sh
```

Expected result: the server reports that it is listening on all interfaces at `0.0.0.0:8000`. Open <http://127.0.0.1:8000> locally, sign in as `admin` using the one-time first-start password in the server log (unless you set `IMPRESS_INITIAL_ADMIN_PASSWORD` before the first start), and change it in **Settings**. In a second terminal, verify the local service:

```sh
scripts/smoke_test.py --base http://127.0.0.1:8000 --password '<current admin password>'
```

Expected result: health, login, classroom, device-registration and web-app checks pass. If startup says a secret is missing/default, rerun the installer or set the required `IMPRESS_*` values in `backend/.env`; do not enable debug mode on a classroom server.

For other computers to use the UI, deploy behind an HTTPS reverse proxy before opening the firewall. The local-only startup check does not configure TLS, a service supervisor, backups or a production firewall.

## Windows PowerShell

The installer and launcher are POSIX shell scripts. For a native Windows Python install, use PowerShell from the repository root:

```powershell
git clone https://github.com/Kush-Kelaiya22/imPress.git
Set-Location imPress
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install --upgrade pip
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

Open `backend/.env` in a text editor and set distinct random values for `IMPRESS_JWT_SECRET` and `IMPRESS_DEVICE_API_KEY`. Generate a value with:

```powershell
py -3.12 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set a strong `IMPRESS_INITIAL_ADMIN_PASSWORD` before the first start, or leave it empty and capture the randomly generated password from the first-start output. Keep `.env` private; do not commit it or send it to students.

Start the server from the backend directory:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Expected result: uvicorn listens on all interfaces at `0.0.0.0:8000`; `/health` returns a healthy status and the browser login page opens. Run the smoke check in a second PowerShell window from the repository root:

```powershell
& backend/.venv/Scripts/python.exe scripts/smoke_test.py --base http://127.0.0.1:8000 --password '<current admin password>'
```

The command above is deliberately local-only. For a classroom, configure the supported deployment topology first: the backend must be reachable by room devices, the host firewall must allow the device port, and staff browsers must use HTTPS through a reverse proxy or directly served TLS. Follow the [Windows firewall and Mobile Hotspot steps](../deployment/container.md#network-requirements) and [TLS setup](../guides/deployment.md#tls-reverse-proxy-websockets-included). If a remote browser reports **HTTPS required**, that is the expected protection; do not turn it off on a shared network.

## Next steps

1. Follow the [first-run administrator path](../user-guide/administrator.md) to create the course, class, teacher and roster.
2. Follow [hardware configuration and flashing](../guides/deployment.md#3-per-room-hardware); the first full v2.1 flash of a gateway and hub is serial, not OTA.
3. Complete the [go-live checklist](../guides/deployment.md#4-go-live-checklist), including HTTPS, changed passwords, device connectivity and backups.
4. Use the [troubleshooting guide](../guides/troubleshooting.md) if the observed result differs.
