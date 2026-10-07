"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import logging

from sqlalchemy import text

from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency that yields an async DB session."""
    async with async_session() as session:
        yield session


# Columns added to pre-existing tables via ALTER TABLE (SQLite best-effort).
_ADD_COLUMNS = {
    "class_sessions": {
        "start_date": "DATE",
        "end_date": "DATE",
        "exam_start_date": "DATE",
        "exam_end_date": "DATE",
        "classroom_code": "VARCHAR(32)",
    },
    "esp_devices": {
        "is_connected": "BOOLEAN DEFAULT 0",
        "gateway_id": "INTEGER",
        "is_active": "BOOLEAN DEFAULT 1",
        "firmware_version": "VARCHAR(32) DEFAULT '0.0.0'",
        "pending_version": "VARCHAR(32) DEFAULT ''",
        "ota_status": "VARCHAR(16) DEFAULT 'idle'",
        "ota_requested_at": "DATETIME",
        "verified_at": "DATETIME",
        "student_count": "INTEGER DEFAULT 0",
        "free_heap": "INTEGER",
        "total_flash": "INTEGER",
        "student_enrollment_id": "INTEGER",
        "device_id": "INTEGER",
    },
    "courses": {
        "exam_date": "DATE",
        "exam_start_time": "VARCHAR(8)",
        "exam_end_time": "VARCHAR(8)",
    },
    "quiz_answers": {
        "student_id": "INTEGER",
    },
    "poll_votes": {
        "student_id": "INTEGER",
    },
    "attendance": {
        "student_enrollment_id": "INTEGER",
        "device_id": "INTEGER",
    },
}


async def _migrate_columns():
    """Add any missing columns to existing tables (non-destructive)."""
    async with engine.begin() as conn:
        for table, cols in _ADD_COLUMNS.items():
            try:
                result = await conn.execute(text(f"PRAGMA table_info({table})"))
            except Exception:
                continue
            existing = {row[1] for row in result.fetchall()}
            for name, ddl in cols.items():
                if name not in existing:
                    await conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"
                    ))


async def _scrub_raw_session_tokens() -> int:
    """Older versions stored the raw bearer token in user_sessions.session_token.

    Any such row is treated as leaked: revoke it and overwrite the column with
    the hash. Idempotent — rows written by current code already hold the hash.
    """
    from sqlalchemy import update
    from .models import UserSession  # late import: models imports Base from here

    async with engine.begin() as conn:
        result = await conn.execute(
            update(UserSession)
            .where(UserSession.session_token != UserSession.token_hash)
            .values(revoked=True, session_token=UserSession.token_hash)
        )
    return result.rowcount or 0


async def init_db():
    """Create all tables on startup, then best-effort migrate existing ones."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        await _migrate_columns()
    except Exception:
        pass
    scrubbed = await _scrub_raw_session_tokens()
    if scrubbed:
        logging.getLogger(__name__).warning(
            "Revoked %d legacy session(s) that stored raw bearer tokens", scrubbed)
