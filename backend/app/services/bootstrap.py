"""The accounts the system itself looks after (v2.2): the default super admin, and the recovery account.

* **impress.default.superAdmin** exists on every start. Its password is random and **new at every start**
  (printed in the server console) unless root fixes one (IMPRESS_DEFAULT_SUPERADMIN_PASSWORD). It is never
  forced through a password change. With test mode forced by root (--test-mode) its password is the fixed
  lab password below. It can't be deleted, demoted or deactivated through the API.
* **impress.recovery.superAdmin** is created only by the deadlock-prevention policy (services/deadlock.py).

Every other super admin is created by root in the console (app.console), never by the web app.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select

from .. import gpc, passwords
from ..auth import hash_password, revoke_user_sessions
from ..config import settings
from ..database import async_session
from ..models import User
from ..timeutil import istnow

logger = logging.getLogger(__name__)

from ..config import DEFAULT_SUPERADMIN, RECOVERY_SUPERADMIN  # noqa: E402
FORCED_TEST_PASSWORD = "imPress@2026"           # lab use only: the hardened profile refuses forced test mode
PROTECTED = frozenset({DEFAULT_SUPERADMIN})       # accounts the API can't delete, demote or deactivate


def banner(title: str, lines: list[str]) -> None:
    width = max(len(title), *(len(x) for x in lines)) + 4
    out = ["", "=" * width, f"  {title}", *[f"    {x}" for x in lines], "=" * width, ""]
    text = "\n".join(out)
    print(text, flush=True)
    logger.warning("%s: %s", title, "; ".join(lines))


async def active_super_admins(db) -> int:
    return (await db.execute(select(func.count()).select_from(User).where(
        User.role == "super_admin", User.is_active.is_(True)))).scalar() or 0


def _boot_password() -> tuple[str, str]:
    """(password, where it came from)."""
    if gpc.get("test_mode.forced"):
        return FORCED_TEST_PASSWORD, "forced test mode (--test-mode): a fixed lab password"
    fixed = settings.DEFAULT_SUPERADMIN_PASSWORD or settings.INITIAL_ADMIN_PASSWORD
    if fixed:
        return fixed, "set by IMPRESS_DEFAULT_SUPERADMIN_PASSWORD"
    return passwords.generate(20), "random: new at every start"


async def ensure_default_superadmin(quiet: bool = False) -> str:
    """Create the default super admin if it is missing and give it this start's password. Returns the password."""
    password, origin = _boot_password()
    async with async_session() as db:
        user = (await db.execute(select(User).where(User.username == DEFAULT_SUPERADMIN))).scalar_one_or_none()
        created = user is None
        if created:
            user = User(username=DEFAULT_SUPERADMIN, email="default.superadmin@impress.local",
                        full_name="Default Super Admin", display_name="Default Super Admin", role="super_admin",
                        hashed_password="x", must_change_password=False)
            db.add(user)
        changed = created or not _same_password(password, user)
        if changed:
            user.hashed_password = hash_password(password)
            user.is_active = True
            user.must_change_password = False
        await db.flush()
        if changed and not created:
            await revoke_user_sessions(db, user.id)              # the old password's sessions end with it
        await db.commit()
    if not quiet:
        shown = password if origin.startswith(("random", "forced")) else "(the one you set: not shown)"
        banner("imPress default super admin", [f"username : {DEFAULT_SUPERADMIN}", f"password : {shown}",
                                               f"({origin})"])
    return password


async def after_reset(by: str) -> None:
    """After 'reset everything' the system starts over: the default super admin is back (new password in the
    console), the integrity baseline and the temporary backups are fresh, and open pages are told."""
    from . import events, integrity
    await ensure_default_superadmin()
    await integrity.reseal_everything(f"system reset by {by}")
    await integrity.check_and_backup()
    events.alert("The system was reset and restarted.", "warning", "all")
    events.status({"restarted": True})


def _same_password(password: str, user: User) -> bool:
    from ..auth import verify_password
    return verify_password(password, user.hashed_password)


async def create_recovery_account(reason: str) -> str:
    """The deadlock policy's last resort: a new super admin with a random 12-character password (all four
    character classes), Pending setup. Returns the password; the caller shows it in the console."""
    password = passwords.generate(12)
    async with async_session() as db:
        existing = (await db.execute(select(User).where(User.username == RECOVERY_SUPERADMIN))).scalar_one_or_none()
        if existing is not None:
            existing.hashed_password = hash_password(password)
            existing.is_active, existing.role, existing.must_change_password = True, "super_admin", True
            await revoke_user_sessions(db, existing.id)
        else:
            db.add(User(username=RECOVERY_SUPERADMIN, email="recovery.superadmin@impress.local",
                        full_name="Recovery Super Admin", display_name="Recovery Super Admin", role="super_admin",
                        hashed_password=hash_password(password), must_change_password=True, created_at=istnow()))
        from ..activity import log_activity
        await log_activity(db, "system.recovery_account", None, "system", None, {"flag": True, "reason": reason})
        await db.commit()
    return password
