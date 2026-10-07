"""Session housekeeping: periodic cleanup of expired server-side sessions.

Expired sessions are dead security records — the auth dependency already
rejects idle/hard-expired sessions with 401, so deleting the rows is safe.
The sweep deliberately does NOT revive anything: it only touches rows that
are hard-expired, idle-expired, or already revoked.
"""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import delete

from ..config import settings
from ..timeutil import istnow

logger = logging.getLogger(__name__)

# How often the cleanup sweep runs (seconds).
CLEANUP_INTERVAL_S = 300  # every 5 minutes


async def _cleanup_once() -> int:
    """Delete sessions that are hard-expired, idle-expired, or revoked.

    Returns the number of rows removed.
    """
    from ..database import async_session
    from ..models import UserSession

    now = istnow()
    idle_cutoff = now - timedelta(minutes=settings.SESSION_IDLE_MINUTES)

    async with async_session() as db:
        result = await db.execute(
            delete(UserSession).where(
                (UserSession.expires_at <= now)
                | (UserSession.last_activity_at < idle_cutoff)
                | (UserSession.revoked.is_(True))
            )
        )
        await db.commit()
        return result.rowcount or 0


async def session_cleanup_loop():
    """Background task: periodically delete expired / revoked sessions."""
    logger.info("Session cleanup started (interval=%ss)", CLEANUP_INTERVAL_S)
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_S)
            n = await _cleanup_once()
            if n:
                logger.info("Session cleanup: removed %d expired session(s)", n)
        except asyncio.CancelledError:
            logger.info("Session cleanup stopped")
            raise
        except Exception as e:  # keep the loop alive on transient errors
            logger.warning("Session cleanup error: %s", e)