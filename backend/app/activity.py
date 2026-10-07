"""Activity logging service — records all significant actions."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .models import ActivityLog


async def log_activity(
    db: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    entity_type: str = "",
    entity_id: Optional[int] = None,
    details: Optional[dict] = None,
):
    """Write one activity log entry."""
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(entry)
    # Don't commit here — let the caller commit as part of their transaction.
