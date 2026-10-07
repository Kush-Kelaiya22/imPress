"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ── App ──
    APP_NAME: str = "imPress Backend"
    DEBUG: bool = True

    # ── Database ──
    DATABASE_URL: str = "sqlite+aiosqlite:///./impress.db"

    # ── JWT Auth ──
    JWT_SECRET: str = "CHANGE-ME-IN-PRODUCTION-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Session Auth (server-side) ──
    SESSION_IDLE_MINUTES: int = 60       # 1 hour inactivity timeout
    SESSION_HARD_MINUTES: int = 360      # 6 hours hard limit
    SESSION_WARNING_MINUTES: int = 5     # warn when less than this many minutes remain before the hard limit

    # ── ESP Device Registration ──
    DEVICE_API_KEY: str = "impress-device-key-2024"

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
