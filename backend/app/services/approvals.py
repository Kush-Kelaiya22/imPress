"""Dual control for the actions that can redefine or erase what the system trusts (v2.2).

An application super admin can no longer, alone and at once, accept an altered
database as the new baseline or clear the data. One super admin *requests* the
action (re-entering their password: step-up), a *different* super admin
approves it (also re-entering theirs), the policy's delay passes, and then the
requester runs it, once, within the approval's expiry. Every step is an
activity-log entry (also copied to the external audit sink) and an alert to the
other administrators.

Policy (root-controlled, docs/design/gpc.md): dual_control.enabled,
dual_control.single_operator_ok (only super admin may approve their own request),
dual_control.delay_minutes, dual_control.expiry_minutes.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc
from ..activity import log_activity
from ..auth import verify_password
from ..models import ActivityLog, Approval, User
from ..timeutil import istnow
from . import events, mfa

ACTIONS = {
    "integrity.accept_current": "Accept the database as it is now as the new trusted baseline",
    "system.clear.class_data": "Delete all class data (courses, classes, students, quizzes, polls, results)",
    "system.clear.everything": "Reset the whole system (class data, devices, firmware records, accounts)",
    "backups.restore": "Restore the system from a backup",
}
STEP_UP_MAX_FAILURES = 5          # wrong passwords in 15 minutes before step-up is refused for a while


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status, {"code": code, "message": message})


async def active_super_admins(db: AsyncSession) -> int:
    return (await db.execute(select(func.count()).select_from(User).where(
        User.role == "super_admin", User.is_active.is_(True)))).scalar() or 0


async def check_password(db: AsyncSession, user: User, password: str) -> None:
    """The password half of step-up, with its lockout (also used to enrol or turn off the second factor)."""
    since = istnow() - timedelta(minutes=15)
    failures = (await db.execute(select(func.count()).select_from(ActivityLog).where(
        ActivityLog.user_id == user.id, ActivityLog.action == "approval.step_up_failed",
        ActivityLog.timestamp > since))).scalar() or 0
    if failures >= STEP_UP_MAX_FAILURES:
        raise _err(429, "STEP_UP_LOCKED", "Too many wrong passwords: try again in 15 minutes")
    if not password or not verify_password(password, user.hashed_password):
        await log_activity(db, "approval.step_up_failed", user.id, "user", user.id, {"flag": True})
        await db.commit()
        raise _err(403, "STEP_UP_FAILED", "The password is not correct")


async def step_up(db: AsyncSession, user: User, password: str, code: str = "") -> None:
    """Re-entering the password proves it is the account's owner at the keyboard, not a left-open session. With a
    second factor (services/mfa.py: enrolled, or required by policy dual_control.mfa_required) the code from the
    authenticator app, or an unused recovery code, is needed as well."""
    await check_password(db, user, password)
    if await mfa.second_factor_needed(db, user):
        row = await mfa.get(db, user)
        if row is None or not row.enabled:
            raise _err(403, "MFA_ENROLMENT_REQUIRED", "Set up two-step verification in Settings > Security before you "
                       "request or approve this (policy dual_control.mfa_required).")
        if not code.strip():
            raise _err(403, "MFA_CODE_REQUIRED", "Enter the code from your authenticator app (or a recovery code).")
        if not await mfa.verify(db, user, code):
            await log_activity(db, "approval.step_up_failed", user.id, "user", user.id, {"flag": True, "factor": "code"})
            await db.commit()
            raise _err(403, "STEP_UP_FAILED", "The code is not correct, or was already used")


def _public(a: Approval, names: dict) -> dict:
    return {"id": a.id, "action": a.action, "description": ACTIONS.get(a.action, a.action), "params": a.params or {},
            "status": a.status, "requested_by": names.get(a.requested_by), "requested_at": a.requested_at,
            "approved_by": names.get(a.approved_by), "approved_at": a.approved_at,
            "not_before": a.not_before, "expires_at": a.expires_at, "executed_at": a.executed_at}


async def listing(db: AsyncSession, limit: int = 30) -> list[dict]:
    rows = (await db.execute(select(Approval).order_by(Approval.id.desc()).limit(limit))).scalars().all()
    names = {u.id: u.username for u in (await db.execute(select(User))).scalars()}
    return [_public(a, names) for a in rows]


async def create(db: AsyncSession, user: User, action: str, params: dict, password: str, code: str = "") -> Approval:
    if action not in ACTIONS:
        raise _err(422, "UNKNOWN_ACTION", "Unknown action: " + ", ".join(ACTIONS))
    if action == "system.clear.everything" and not gpc.get("system.reset_everything_allowed"):
        raise _err(403, "POLICY_DISABLED", "A full reset is switched off by policy (system.reset_everything_allowed)")
    if action == "backups.restore":
        from . import backups as _backups
        wanted = str((params or {}).get("backup", ""))
        try:
            _backups.resolve(wanted)
        except _backups.BackupError:
            raise _err(422, "UNKNOWN_BACKUP", "Choose an existing backup") from None
        params = {"backup": wanted}
    await step_up(db, user, password, code)
    a = Approval(action=action, params=params or {}, requested_by=user.id, status="pending")
    db.add(a)
    await log_activity(db, "approval.request", user.id, "approval", None, {"flag": True, "action": action, "params": params or {}})
    await db.commit()
    events.alert(f"{user.username} requested: {ACTIONS[action]}. Another super admin must approve it.", "warning")
    return a


async def approve(db: AsyncSession, user: User, approval_id: int, password: str, code: str = "") -> Approval:
    a = await db.get(Approval, approval_id)
    if a is None:
        raise _err(404, "NOT_FOUND", "No such request")
    if a.status != "pending":
        raise _err(409, "NOT_PENDING", f"This request is already {a.status}")
    own = a.requested_by == user.id
    if own and not (gpc.get("dual_control.single_operator_ok") and await active_super_admins(db) == 1):
        raise _err(403, "SELF_APPROVAL", "A different super admin must approve this request")
    await step_up(db, user, password, code)
    now = istnow()
    a.status, a.approved_by, a.approved_at = "approved", user.id, now
    a.not_before = now + timedelta(minutes=gpc.get("dual_control.delay_minutes"))
    a.expires_at = a.not_before + timedelta(minutes=gpc.get("dual_control.expiry_minutes"))
    await log_activity(db, "approval.approve", user.id, "approval", a.id,
                       {"flag": True, "action": a.action, "self_approved": own, "not_before": a.not_before.isoformat()})
    await db.commit()
    events.alert(f"{user.username} approved: {ACTIONS.get(a.action, a.action)}. It can run from {a.not_before:%H:%M}.", "warning")
    return a


async def deny(db: AsyncSession, user: User, approval_id: int) -> Approval:
    a = await db.get(Approval, approval_id)
    if a is None:
        raise _err(404, "NOT_FOUND", "No such request")
    if a.status not in ("pending", "approved"):
        raise _err(409, "NOT_PENDING", f"This request is already {a.status}")
    a.status = "denied"
    await log_activity(db, "approval.deny", user.id, "approval", a.id, {"flag": True, "action": a.action})
    await db.commit()
    return a


async def require(db: AsyncSession, user: User, action: str, params: dict, approval_id: int | None) -> Approval | None:
    """Called by the endpoint that performs `action`. Returns the consumed
    approval, or None when the policy doesn't ask for dual control."""
    if not gpc.get("dual_control.enabled"):
        return None
    if not approval_id:
        raise _err(403, "APPROVAL_REQUIRED",
                   "This action needs a second super admin's approval: request it on the System page first")
    a = await db.get(Approval, approval_id)
    if a is None or a.action != action or (a.params or {}) != (params or {}):
        raise _err(403, "APPROVAL_MISMATCH", "That approval is not for this action")
    if a.requested_by != user.id:
        raise _err(403, "APPROVAL_MISMATCH", "Only the super admin who requested it can run it")
    if a.status != "approved":
        raise _err(409, "NOT_APPROVED", f"This request is {a.status}")
    now = istnow()
    if now < a.not_before:
        wait = int((a.not_before - now).total_seconds())
        raise _err(409, "NOT_YET", f"The delay has not passed: it can run in {wait // 60} min {wait % 60} s")
    if now > a.expires_at:
        a.status = "denied"
        await log_activity(db, "approval.expired", user.id, "approval", a.id, {"action": a.action})
        await db.commit()
        raise _err(409, "EXPIRED", "The approval expired: request it again")
    a.status, a.executed_at = "executed", now          # spent before the action runs: it can't be replayed
    await log_activity(db, "approval.execute", user.id, "approval", a.id, {"flag": True, "action": action, "params": params or {}})
    await db.commit()
    return a
