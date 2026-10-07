"""Application configuration loaded from environment variables."""

import secrets

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
    SESSION_IDLE_MINUTES: int = 60       # 1 hour inactivity timeout
    SESSION_HARD_MINUTES: int = 360      # 6 hours hard limit
    SESSION_WARNING_MINUTES: int = 5     # warn when less than this many minutes remain before the hard limit

    # ── ESP Device Registration ──
    DEVICE_API_KEY: str = DEFAULT_DEVICE_API_KEY

    # ── First-run super admin ──
    # Empty → a random password is generated and logged ONCE at first start.
    INITIAL_ADMIN_PASSWORD: str = ""

    # ── Firmware / OTA ──
    FIRMWARE_DIR: str = "./firmware_bins"   # uploaded firmware .bin files live here

    # ── WebSocket ──
    # Require auth on /ws/class: devices present ?api_key=<device key>,
    # teachers present ?token=<JWT>. Turn off for LAN debugging.
    WS_REQUIRE_AUTH: bool = True

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_prefix": "IMPRESS_", "env_file": ".env"}


settings = Settings()


def insecure_settings(s: Settings) -> list[str]:
    """Names of settings still at their public, repo-published defaults."""
    bad = []
    if s.JWT_SECRET == DEFAULT_JWT_SECRET:
        bad.append("IMPRESS_JWT_SECRET")
    if s.DEVICE_API_KEY == DEFAULT_DEVICE_API_KEY:
        bad.append("IMPRESS_DEVICE_API_KEY")
    return bad


def check_secure(s: Settings) -> None:
    """Refuse to run with published secrets unless explicitly in DEBUG mode."""
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
