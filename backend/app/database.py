"""Async SQLAlchemy engine and session factory."""

import logging

from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record):
    """SQLite ignores foreign keys unless asked, per connection."""
    if engine.dialect.name == "sqlite":
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency that yields an async DB session."""
    async with async_session() as session:
        yield session


async def commit_or_conflict(db: AsyncSession, detail: str, status: int = 409) -> None:
    """Commit; a uniqueness/foreign-key violation becomes an HTTP error.

    Application checks ("already answered?") race when two requests arrive
    together; the database constraint is the real guard, and this keeps the
    loser of the race from turning into a 500.
    """
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status, detail)


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
    """Create missing tables and apply pending migrations (stops on failure)."""
    from .migrations import migrate  # late import: migrations needs Base's metadata loaded
    from . import models  # noqa: F401  register every table on Base.metadata
    await migrate(engine, Base.metadata.create_all)
    scrubbed = await _scrub_raw_session_tokens()
    if scrubbed:
        logging.getLogger(__name__).warning(
            "Revoked %d legacy session(s) that stored raw bearer tokens", scrubbed)
