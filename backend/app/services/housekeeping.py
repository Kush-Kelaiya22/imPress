"""Housekeeping for the v2.2 hardening: the policy file is re-read when root
changes it, and expired test data is deleted (policy test_mode.*_ttl_*)."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import text

from .. import gpc
from ..activity import log_activity
from ..config import settings
from ..database import async_session
from ..timeutil import istnow
from . import events, integrity, test_mode

logger = logging.getLogger(__name__)
POLICY_CHECK_S = 30
SWEEP_EVERY = 20                  # policy checks between test-data sweeps (10 minutes)


async def report(note: str, action: str = "system.policy_alert") -> None:
    """Tell the administrators and write it where the audit trail keeps it."""
    logger.error(note)
    events.alert(note, "error")
    async with async_session() as db:
        await log_activity(db, action, None, "system", None, {"flag": True, "message": note})
        await db.commit()


async def purge_activity() -> int:
    """Delete activity-log entries older than policy audit.purge_days (never sooner than
    audit.min_retention_days). The external audit trail keeps its copy."""
    days = gpc.get("audit.purge_days")
    if not days:
        return 0
    days = max(days, gpc.get("audit.min_retention_days"))
    cutoff = (istnow() - timedelta(days=days)).isoformat(sep=" ")
    async with async_session() as db:
        deleted = (await db.execute(text("DELETE FROM activity_logs WHERE timestamp < :c"), {"c": cutoff})).rowcount or 0
        if deleted:
            await log_activity(db, "system.activity_purged", None, "system", None,
                               {"flag": True, "deleted": deleted, "older_than_days": days})
        await db.commit()
    return deleted


async def maintenance_once(tick: int) -> None:
    reloaded, error = gpc.reload_if_changed(settings)
    if error:
        await report(f"A changed policy file was refused and the previous policy stays in force: {error}")
    elif reloaded:
        async with async_session() as db:
            await log_activity(db, "system.policy_reloaded", None, "system", None,
                               {"flag": True, "profile": gpc.profile(), "file": gpc.current().file})
            await db.commit()
        events.alert("The global policy was updated by root.", "info")
    if tick % SWEEP_EVERY == 0:
        await purge_activity()
        old = await asyncio.to_thread(integrity.sweep_old_copies)
        if old:
            async with async_session() as db:
                await log_activity(db, "system.backup_expired", None, "system", None, {"flag": True, "deleted": old})
                await db.commit()
        gone = await asyncio.to_thread(test_mode.sweep_expired)
        if gone:
            async with async_session() as db:
                await log_activity(db, "system.test_data_expired", None, "system", None, {"flag": True, "deleted": gone})
                await db.commit()


async def maintenance_loop() -> None:
    tick = 0
    while True:
        try:
            await maintenance_once(tick)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("maintenance failed")
        tick += 1
        await asyncio.sleep(POLICY_CHECK_S)
