"""global_deadlock_prevention (v2.2): the system must never be left without a super admin.

Through the web app that can't happen (the last active super admin can't be removed, and the database itself
refuses it). It can only happen if someone altered the database from outside. So the response is, in order:

1. treat it as tampering: keep a forensic copy, roll the database back to the last good backup, verify it;
2. if there is still no active super admin (no usable backup, or the backups have none either),
   create `impress.recovery.superAdmin` with a random 12-character password and show it in the console.

Policy flag: deadlock_prevention.enabled (root's; on by default). Checked at start-up, after every integrity
check, and every 30 seconds.
"""

from __future__ import annotations

import logging

from .. import gpc
from ..database import async_session
from . import bootstrap, events, integrity

logger = logging.getLogger(__name__)


async def count_super_admins() -> int:
    async with async_session() as db:
        return await bootstrap.active_super_admins(db)


async def check(reason: str = "check") -> dict | None:
    """None when all is well; otherwise a description of what was done (for tests and the log)."""
    if not gpc.get("deadlock_prevention.enabled"):
        return None
    if await count_super_admins() > 0:
        return None
    done = {"reason": reason, "rolled_back": False, "recovery_password": None}
    message = "No active super admin exists: the database was altered outside imPress."
    async with integrity._lock:
        source = next((p for p in (integrity.backup_dir() / "rolling.db", integrity.backup_dir() / "startup.db")
                       if p.exists()), None)
        if source is not None:
            forensic = await integrity.keep_forensic_copy()
            await integrity.restore_from(source)
            done["rolled_back"] = True
            message += f" Rolled back to {source.name}" + (f" (the altered database is kept as {forensic.name})." if forensic else ".")
            rep = await integrity.verify_now()
            if not rep.ok:
                await integrity.reseal_everything("deadlock rollback")
        if await count_super_admins() == 0:
            password = await bootstrap.create_recovery_account(reason)
            done["recovery_password"] = password
            message += f" Even then there was none: {bootstrap.RECOVERY_SUPERADMIN} was created."
            bootstrap.banner("imPress RECOVERY ACCOUNT (global_deadlock_prevention)", [
                f"username : {bootstrap.RECOVERY_SUPERADMIN}", f"password : {password}",
                "Sign in, then set your own password. Create a proper super admin in the console and retire this one."])
    await integrity._flag(message, restored=None)
    logger.critical(message)
    events.alert(message, "error")
    return done
