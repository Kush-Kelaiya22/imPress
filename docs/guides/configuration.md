# Configuration reference

## Backend (`backend/app/config.py`)

Environment variables with prefix **`IMPRESS_`**, or a `.env` file in the working directory. A template is in `backend/.env.example`. Lists use JSON syntax.

| Variable | Default | Description |
|---|---|---|
| `IMPRESS_DEBUG` | `false` | Development mode. With default secrets, `false` **refuses to start**; `true` logs a warning instead. |
| `IMPRESS_SQL_ECHO` | `false` | Log all SQL with parameters. Never enable in production. |
| `IMPRESS_APP_NAME` | `imPress Backend` | Cosmetic. |
| `IMPRESS_DATABASE_URL` | `sqlite+aiosqlite:///./impress.db` | SQLAlchemy async URL. |
| `IMPRESS_JWT_SECRET` | public default | Must be set in production. Legacy JWT helpers only (sessions are opaque). |
| `IMPRESS_JWT_ALGORITHM` | `HS256` | Legacy. |
| `IMPRESS_JWT_EXPIRE_MINUTES` | `1440` | Legacy. |
| `IMPRESS_SESSION_IDLE_MINUTES` | `60` | Idle timeout. |
| `IMPRESS_SESSION_HARD_MINUTES` | `360` | Absolute session lifetime. |
| `IMPRESS_SESSION_WARNING_MINUTES` | `5` | `session-status.warning_active` window. |
| `IMPRESS_DEVICE_API_KEY` | public default | The shared **provisioning** key: must be set in production and equal every device's `api_key`. Devices register with it and are issued their own key (#66). |
| `IMPRESS_DEVICE_KEYS_REQUIRED` | `false` | `true`: the shared key works for registration only, so every device must use its own key. Firmware older than v2.1 per-device keys then stops working. |
| `IMPRESS_INITIAL_ADMIN_PASSWORD` | empty | First-run admin password; empty = random, logged once. |
| `IMPRESS_FIRMWARE_DIR` | `./firmware_bins` | OTA image store. |
| `IMPRESS_WS_REQUIRE_AUTH` | `true` | Disable only for isolated debugging. |
| `IMPRESS_CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed browser origins. |

Generate secrets: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

Fixed internal timings (code constants): presence sweep 15 s, offline after 30 s, session cleanup every 5 min.

---

## C6 gateway (`firmware/class_c6`)

`idf.py menuconfig` → **imPress C6 Gateway Configuration**. Values are written to NVS namespace **`impress`** on first boot; **NVS wins afterwards**. Empty or oversized NVS values are ignored and the Kconfig default is kept (#18).

| Kconfig | Default | NVS key | Notes |
|---|---|---|---|
| `WIFI_SSID` | `impress-hotspot` | `wifi_ssid` (≤ 32) | 2.4 GHz, WPA2-PSK or better |
| `WIFI_PASSWORD` | `impress123` | `wifi_pass` (≤ 64) | |
| `WIFI_MAX_RETRY` | 10 | – | |
| `BACKEND_HOST` | `192.168.137.1` | `backend_h` (≤ 127) | IP or hostname |
| `BACKEND_PORT` | 8000 | `backend_p` (u16, 0 ignored) | |
| `DEVICE_API_KEY` | `impress-device-key-2024` | `api_key` (≤ 127) | the shared provisioning key: sent as `X-API-Key` until the device is issued its own |
| — | — | `dev_key` | the device's own key from `/register` (#66); once present it is sent instead of `api_key`. Erased when the backend answers 401 (an admin reset it) |
| `CLASS_SESSION_ID` | 0 (= auto) | `class_id` (i32) | updated from register / WS assignment |
| `HEARTBEAT_INTERVAL_S` | 15 | – | 5–300 |
| `WS_PING_INTERVAL_S` | 30 | – | 10–120 |
| `STATUS_PING_INTERVAL_S` | 120 | – | 60–600 |
| `SPI_BATCH_MAX_WAIT_MS` | 500 | – | batch flush after this idle time |
| `BATCH_MAX_SIZE` | 20 | – | messages per batch POST |
| `BATTERY_ADC_EN` / `BATTERY_ADC_GPIO` | n / 4 | – | optional supply monitor |

## S3 hub (`firmware/class_s3`)

Kconfig menu **imPress S3 Class Module Configuration** → NVS namespace **`s3_cfg`**.

| Kconfig | Default | NVS key | Notes |
|---|---|---|---|
| `WIFI_SSID` / `WIFI_PASSWORD` | `impress-hotspot` / `impress123` | `wifi_ssid` / `wifi_pass` | used only for the OTA hop |
| `WIFI_MAX_RETRY` | 5 | – | |
| `BACKEND_HOST` / `BACKEND_PORT` | `192.168.1.100` / 8000 | `backend_host` / `backend_port` | OTA hop target; **set to the same server as the C6** |
| `DEVICE_API_KEY` | `impress-device-key-2024` | `api_key` | shared provisioning key |
| — | — | `dev_key` | the hub's own key, issued when it registers during its OTA hop (#66) |
| `HEARTBEAT_INTERVAL_MS` | 5000 | – | S3 → C6 heartbeat + student sweep |
| `STUDENT_TIMEOUT_MS` | 60000 | – | silence before `STUDENT_LEAVE` |
| `SPI_POLL_INTERVAL_MS` | 50 | – | max wait between link checks |
| `MESH_WIFI_CHANNEL` | 1 | – | must equal the students' `MESH_WIFI_CHANNEL` |

`sdkconfig` also enables `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` (see [OTA](ota-updates.md)).

## Student module (`firmware/student/main/config.h`)

Compile-time constants (no menuconfig menu):

| Constant | Default | Meaning |
|---|---|---|
| `MESH_WIFI_CHANNEL` | 1 | must match the S3 |
| `MESH_RELAY_TTL` | 5 | max hops |
| `STUDENT_HAS_DISPLAY` / `STUDENT_HAS_LED` | 0 / 0 | board variant |
| `PIN_BTN_1..4`, `PIN_BTN_CONFIRM` | 4, 16, 18, 22, 23 | buttons A–D, confirm |
| `PIN_I2C_SDA` / `SCL` | 8 / 9 | SSD1306 OLED |
| `HEARTBEAT_INTERVAL_MS` | 30000 | student heartbeat |
| `DEBOUNCE_MS` | 50 | button debounce |
| `DEFAULT_ENROLLMENT` | `0000000000` | "unprovisioned" placeholder |

NVS namespace **`impress`**: `enroll` (identity), `s_name`, `s_program`, `s_email` (local profile cache, never transmitted), `init_done`.

## Changing configuration on a deployed device

| Option | How |
|---|---|
| Re-flash | `idf.py menuconfig` + flash (resets NVS only if you erase flash) |
| Edit NVS | write the keys above with an NVS partition image (`nvs_partition_gen.py`) or a provisioning tool; takes effect on the next boot |
| Class assignment | via the backend (`classroom_code` on register, or admin linking); no device change needed |
