"""Application configuration loaded from environment variables."""

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings

# Public defaults shipped in this repo. Fine for local debugging, never for a
# real deployment: insecure_settings() refuses them unless DEBUG is on.
DEFAULT_JWT_SECRET = "CHANGE-ME-IN-PRODUCTION-use-a-real-secret"
DEFAULT_DEVICE_API_KEY = "impress-device-key-2024"


class Settings(BaseSettings):
    # ── App ──
    APP_NAME: str = "imPress Backend"
    DEBUG: bool = False          # dev conveniences; allows the public default secrets
    SQL_ECHO: bool = False       # log every SQL statement (very noisy, includes data)

    # ── Database ──
    DATABASE_URL: str = "sqlite+aiosqlite:///./impress.db"

    # ── JWT Auth ──
    JWT_SECRET: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Session Auth (server-side) ──
    SESSION_IDLE_MINUTES: int = 5        # inactivity timeout (v2.2: 5 minutes)
    SESSION_CLASS_IDLE_MINUTES: int = 30 # ... for faculty while one of their classes is in session
    SINGLE_SESSION: bool = True          # refuse a second sign-in of one account from another device
    TEMP_BACKUP_DIR: str = ""            # temporary integrity backups; "" = <system temp>/impress-backups
    INTEGRITY_INTERVAL_S: int = 300      # verify the database and refresh the rolling backup this often
    SESSION_HARD_MINUTES: int = 360      # 6 hours hard limit
    SESSION_WARNING_MINUTES: int = 5     # warn when less than this many minutes remain before the hard limit

    # ── ESP Device Registration ──
    DEVICE_API_KEY: str = DEFAULT_DEVICE_API_KEY
    # Per-device keys (#66): devices register with DEVICE_API_KEY and get their
    # own key. True = the shared key works for registration only (firmware
    # older than per-device keys then stops working).
    DEVICE_KEYS_REQUIRED: bool = False

    # Signed firmware (#66): path to the site's RSA-3072 public key (PEM, from
    # scripts/firmware_key.sh). Set: uploads must be signed with it, and images
    # that aren't are never deployed. Empty: signatures are recorded, not required.
    FIRMWARE_SIGNING_KEY: str = ""
    # Without a signing key, the TrustedInstaller refuses to deploy unless the
    # site accepts unsigned images explicitly (#123). DEBUG implies true.
    FIRMWARE_ALLOW_UNSIGNED: bool = False
    # Separation of duties (#123): the uploader of an image can't approve it.
    # A site with a single administrator sets this; a super admin may then
    # approve their own upload, and the approval is logged as such.
    FIRMWARE_SINGLE_APPROVER: bool = False

    # ── The default super admin, impress.default.superAdmin (v2.2) ──
    # Empty: a random password is made at EVERY start and printed in the server console. Set one to keep it.
    # IMPRESS_INITIAL_ADMIN_PASSWORD is the older name for the same setting and still works.
    DEFAULT_SUPERADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""

    # ── Firmware / OTA ──
    FIRMWARE_DIR: str = "./firmware_bins"   # uploaded firmware .bin files live here

    # ── Timetable (#126) ──
    # When an authoritative source (AURIS, #127) has synchronised before, its
    # data older than this many hours counts as unknown, and room-occupancy
    # questions (OTA maintenance windows, #128) fail closed. 0 = never stale.
    SCHEDULE_MAX_AGE_HOURS: int = 48

    # ── Transport security (#152) ──
    # Refuse staff traffic that did not arrive over HTTPS. Unset: on unless
    # DEBUG. Loopback, health checks and device-key routes are exempt.
    REQUIRE_HTTPS: bool | None = None
    # Devices too must use HTTPS/WSS (firmware built with BACKEND_TLS, #66).
    DEVICE_HTTPS_ONLY: bool = False

    # ── Global policy control (v2.2, docs/design/gpc.md) ──
    # The security and integrity switches belong to root, not to a super admin:
    # a built-in default per profile, optionally a root-signed file, optionally
    # inline overrides on the start command.
    PROFILE: str = "standard"        # "standard" or "hardened" (refuses to start below the hardened floor)
    GPC: str = ""                    # inline overrides, e.g. "dual_control.delay_minutes=30,test_mode.allowed=false"
    GPC_FILE: str = ""               # root-signed policy file; "" = ./global_policy_control.json
    ROOT_PUBLIC_KEY: str = ""        # root's Ed25519 public key (base64); "" = ./root_public.key

    # ── WebSocket ──
    # Require auth on /ws/class: devices present ?api_key=<device key>,
    # teachers present ?token=<JWT>. Turn off for LAN debugging.
    WS_REQUIRE_AUTH: bool = True

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_prefix": "IMPRESS_", "env_file": ".env"}


settings = Settings()

# The release, from the repository's VERSION file (#42); /health reports it.
_VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"
APP_VERSION = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "unknown"


def _release_label() -> str:
    """The version with its patch number, as the release page names it (2.2.14). A RELEASE file stamped by the
    build wins; in a git checkout the patch is the first-parent commits since the line's .0 tag (scripts/release.py)."""
    stamp = _VERSION_FILE.with_name("RELEASE")
    if stamp.exists() and stamp.read_text().strip():
        return stamp.read_text().strip().split("/")[-1].lstrip("v")
    major_minor = ".".join(APP_VERSION.split(".")[:2])
    try:
        import subprocess
        root = str(_VERSION_FILE.parent)
        for owner in ("varun", "kush", "kelaiya"):
            tag = f"{owner}/v{major_minor}.0"
            if subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=root,
                              capture_output=True, timeout=5).returncode == 0:
                n = subprocess.run(["git", "rev-list", "--first-parent", "--count", f"{tag}..HEAD"], cwd=root,
                                   capture_output=True, text=True, timeout=5).stdout.strip()
                return f"{major_minor}.{int(n)}" if n.isdigit() else APP_VERSION
    except Exception:                                    # noqa: BLE001
        pass
    return APP_VERSION


APP_RELEASE = _release_label()


# The accounts the system looks after itself (v2.2, services/bootstrap.py): the API can't delete, demote,
# deactivate or reset these.
DEFAULT_SUPERADMIN = "impress.default.superAdmin"
RECOVERY_SUPERADMIN = "impress.recovery.superAdmin"


def insecure_settings(s: Settings) -> list[str]:
    """Names of settings still at their public, repo-published defaults."""
    bad = []
    if s.JWT_SECRET == DEFAULT_JWT_SECRET:
        bad.append("IMPRESS_JWT_SECRET")
    if s.DEVICE_API_KEY == DEFAULT_DEVICE_API_KEY:
        bad.append("IMPRESS_DEVICE_API_KEY")
    return bad


def check_secure(s: Settings) -> None:
    """Refuse to run with published secrets, or with unauthenticated
    WebSockets (#121), unless explicitly in DEBUG mode."""
    if not s.WS_REQUIRE_AUTH and not s.DEBUG:
        raise RuntimeError("IMPRESS_WS_REQUIRE_AUTH=false is for local debugging only: "
                           "set IMPRESS_DEBUG=true as well, or remove it.")
    bad = insecure_settings(s)
    if bad and not s.DEBUG:
        raise RuntimeError(
            "Refusing to start with default secrets: set " + ", ".join(bad)
            + " (e.g. python -c 'import secrets; print(secrets.token_urlsafe(32))')"
            + ", or IMPRESS_DEBUG=true for local development."
        )


def api_key_ok(candidate: str | None) -> bool:
    """Constant-time device API key comparison."""
    return secrets.compare_digest((candidate or "").encode(), settings.DEVICE_API_KEY.encode())
