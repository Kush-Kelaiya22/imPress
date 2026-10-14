"""What root can do to the system (v2.2): the operations behind the console (`python -m app.console`) and the
shared pieces of the web app's dangerous actions (clearing data).

Everything here runs as the system (the database gateway's principal for the server itself): root already holds
the keys to the host. Every operation is written to the activity log and the external audit trail as root's.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, func, select, text

from .. import gpc, passwords
from ..activity import log_activity
from ..auth import hash_password, revoke_user_sessions
from ..config import APP_VERSION, DEFAULT_SUPERADMIN
from ..database import async_session
from ..dbgateway import SYSTEM, act_as
from ..models import DeletedUser, LoginThrottle, User, UserSession
from ..policy import is_faculty_role
from ..timeutil import istnow
from . import accounts, bootstrap, integrity, test_mode


class RootError(Exception):
    pass


CLASS_TABLES = ["quiz_answers", "quiz_questions", "quizzes", "poll_votes", "polls", "attendance",
                "class_occurrence_exceptions", "student_enrollments", "class_faculty", "class_sessions",
                "students", "courses", "schedule_sources"]


async def audit(action: str, details: dict | None = None) -> None:
    async with async_session() as db:
        await log_activity(db, f"console.{action}", None, "system", None, {"flag": True, **(details or {})})
        await db.commit()


async def clear_data(scope: str, keep_user_id: int | None = None, keep_session_id: int | None = None,
                     entry: str | None = None) -> str:
    """Clear class data, or everything but one account (and its session). A full copy is saved first; returns its name.
    Used by the web app (after its approval and typed phrase) and by the console."""
    act_as(SYSTEM)
    backup = integrity.backup_dir() / f"before-clear-{istnow():%Y%m%d-%H%M%S}.db"
    await integrity.copy_live_to(backup)
    keep = keep_user_id if keep_user_id is not None else -1
    async with async_session() as db:
        await db.execute(text("PRAGMA defer_foreign_keys = ON"))
        await db.execute(text("UPDATE esp_devices SET student_enrollment_id = NULL"))
        await db.execute(text("UPDATE student_modules SET class_session_id = NULL"))
        for t in CLASS_TABLES:
            await db.execute(text(f"DELETE FROM {t}"))
        if scope == "everything":
            for t in ("student_modules", "deployment_targets", "firmware_deployments", "firmware_artifacts",
                      "esp_devices", "login_throttle", "deleted_users"):
                await db.execute(text(f"DELETE FROM {t}"))
            keep_days = gpc.get("audit.min_retention_days")       # policy: recent audit entries survive a reset
            if keep_days:
                await db.execute(text("DELETE FROM activity_logs WHERE timestamp < :c"),
                                 {"c": (istnow() - timedelta(days=keep_days)).isoformat(sep=" ")})
                await db.execute(text("UPDATE activity_logs SET user_id = NULL WHERE user_id IS NOT NULL AND user_id != :u"), {"u": keep})
            else:
                await db.execute(text("DELETE FROM activity_logs"))
            await db.execute(text("DELETE FROM approvals WHERE requested_by != :u OR (approved_by IS NOT NULL AND approved_by != :u)"), {"u": keep})
            await db.execute(text("DELETE FROM user_sessions WHERE id != :k"), {"k": keep_session_id if keep_session_id else -1})
            await db.execute(text("DELETE FROM users WHERE id != :u"), {"u": keep})
        await log_activity(db, entry or f"system.clear_{scope}", keep_user_id, "system", None, {"flag": True, "backup": backup.name})
        await db.commit()
    return backup.name


# ── status ────────────────────────────────────────────────────────────────

async def status() -> dict:
    async with async_session() as db:
        counts = {}
        for label, model in (("accounts", User), ("deleted accounts", DeletedUser)):
            counts[label] = (await db.execute(select(func.count()).select_from(model))).scalar() or 0
        supers = await bootstrap.active_super_admins(db)
        now = istnow()
        live = (await db.execute(select(func.count()).select_from(UserSession).where(
            UserSession.revoked.is_(False), UserSession.expires_at > now))).scalar() or 0
    st = integrity.status()
    return {"version": APP_VERSION, "profile": gpc.profile(), "database": st["db"], "active super admins": supers,
            "open sessions": live, "test mode": ("forced on" if gpc.get("test_mode.forced") else
                                                 "on" if test_mode.state()["on"] else "off"),
            "ota": "on" if gpc.get("ota.enabled") else "off", "deadlock prevention": "on" if gpc.get("deadlock_prevention.enabled") else "off",
            **counts}


# ── accounts ──────────────────────────────────────────────────────────────

async def _user(db, ref: str) -> User:
    q = select(User).where(User.id == int(ref)) if ref.isdigit() else select(User).where(User.username == ref)
    u = (await db.execute(q)).scalar_one_or_none()
    if u is None:
        raise RootError(f"no such account: {ref}")
    return u


async def list_users(role: str | None = None) -> list[dict]:
    async with async_session() as db:
        q = select(User).order_by(User.id)
        if role:
            q = q.where(User.role == role)
        rows = (await db.execute(q)).scalars().all()
        return [{"id": u.id, "username": u.username, "name": u.display_name or u.full_name, "role": u.role,
                 "status": "inactive" if not u.is_active else "pending setup" if u.must_change_password else "active",
                 "designation": u.designation if is_faculty_role(u.role) else ""} for u in rows]


async def create_account(username: str, role: str, email: str = "", name: str = "", password: str = "",
                         designation: str = "faculty") -> tuple[str, str]:
    """Create an account. Returns (username, the temporary password). Super admins are only ever created here."""
    if role not in ("super_admin", "admin", "teacher"):
        raise RootError("role must be super_admin, admin or teacher")
    if len(username) < 3 or not all(c.isalnum() or c in "._-" for c in username):
        raise RootError("username: at least 3 characters, letters, digits and . _ -")
    generated = not password
    password = password or passwords.generate(12 if role != "super_admin" else 14)
    if (why := passwords.problem(password, username, role)):
        raise RootError(f"password {why}")
    act_as(SYSTEM)
    async with async_session() as db:
        if (await db.execute(select(User).where(User.username == username))).scalar_one_or_none():
            raise RootError(f"the username {username} is taken")
        email = email or f"{username.lower()}@impress.local"
        if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
            raise RootError(f"the e-mail {email} is used by another account")
        u = User(username=username, email=email, full_name=name or username, display_name=name, role=role,
                 designation=designation if role == "teacher" else "faculty", hashed_password=hash_password(password),
                 must_change_password=True)
        db.add(u)
        await db.flush()
        await log_activity(db, "console.create_account", None, "user", u.id, {"flag": True, "username": username, "role": role, "generated": generated})
        await db.commit()
    return username, password


async def set_password(ref: str, password: str = "") -> tuple[str, str]:
    act_as(SYSTEM)
    async with async_session() as db:
        u = await _user(db, ref)
        password = password or passwords.generate(12)
        if (why := passwords.problem(password, u.username, u.role)):
            raise RootError(f"password {why}")
        u.hashed_password = hash_password(password)
        u.must_change_password = u.username != DEFAULT_SUPERADMIN
        await revoke_user_sessions(db, u.id)
        await log_activity(db, "console.set_password", None, "user", u.id, {"flag": True, "username": u.username})
        await db.commit()
        return u.username, password


async def finish_setup(ref: str) -> str:
    """Treat an account's setup as done without changing its password: clears the temporary-credentials flag
    ('pending setup') and marks the welcome as seen. For when root has handed the credentials over in person."""
    act_as(SYSTEM)
    async with async_session() as db:
        u = await _user(db, ref)
        u.must_change_password = False
        u.onboarded_at = u.onboarded_at or istnow()
        await log_activity(db, "console.finish_setup", None, "user", u.id, {"flag": True, "username": u.username})
        await db.commit()
        return u.username


async def set_active(ref: str, active: bool) -> str:
    act_as(SYSTEM)
    async with async_session() as db:
        u = await _user(db, ref)
        u.is_active = active
        if not active:
            await revoke_user_sessions(db, u.id)
        await log_activity(db, "console.activate" if active else "console.deactivate", None, "user", u.id, {"flag": True, "username": u.username})
        try:
            await db.commit()
        except Exception as exc:                              # the database refuses to leave no active super admin
            await db.rollback()
            raise RootError("refused: that would leave no active super admin") from exc
        return u.username


async def delete_account(ref: str) -> str:
    act_as(SYSTEM)
    async with async_session() as db:
        u = await _user(db, ref)
        if u.username == DEFAULT_SUPERADMIN:
            raise RootError("the default super admin can't be deleted")
        await log_activity(db, "console.delete_account", None, "user", u.id, {"flag": True, "username": u.username})
        await accounts.delete_user(db, u, deleted_by="root (console)")
        await accounts.commit(db, revoked=u)
        return u.username


async def trash() -> list[dict]:
    async with async_session() as db:
        rows = (await db.execute(select(DeletedUser).order_by(DeletedUser.id.desc()))).scalars().all()
        return [{"id": d.id, "username": d.username, "role": d.role, "deleted": d.deleted_at.strftime("%Y-%m-%d %H:%M"),
                 "days left": max(0, (d.purge_after - istnow()).days)} for d in rows]


async def restore_account(ref: str) -> str:
    act_as(SYSTEM)
    async with async_session() as db:
        q = select(DeletedUser).where(DeletedUser.id == int(ref)) if ref.isdigit() else select(DeletedUser).where(DeletedUser.username == ref)
        d = (await db.execute(q.order_by(DeletedUser.id.desc()))).scalars().first()
        if d is None:
            raise RootError(f"nothing in the trash for {ref}")
        if (await db.execute(select(User).where((User.username == d.username) | (User.email == d.email)))).first():
            raise RootError("the username or e-mail is in use by another account")
        db.add(User(username=d.username, email=d.email, hashed_password=d.hashed_password, full_name=d.full_name,
                    display_name=d.display_name, role=d.role, designation=d.designation, preferences=d.preferences or {},
                    created_at=d.created_at, onboarded_at=istnow()))
        await db.delete(d)
        await log_activity(db, "console.restore_account", None, "user", None, {"flag": True, "username": d.username})
        await db.commit()
        return d.username


async def unlock(ref: str) -> int:
    """Clear sign-in throttling for an account (after too many wrong passwords)."""
    act_as(SYSTEM)
    async with async_session() as db:
        u = await _user(db, ref)
        n = (await db.execute(delete(LoginThrottle).where(LoginThrottle.key.in_([f"user:{u.username.lower()}", f"change:{u.id}"])))).rowcount
        await log_activity(db, "console.unlock", None, "user", u.id, {"flag": True, "username": u.username})
        await db.commit()
        return n or 0


async def sessions(ref: str | None = None) -> list[dict]:
    async with async_session() as db:
        now = istnow()
        q = select(UserSession, User.username).join(User, User.id == UserSession.user_id).where(
            UserSession.revoked.is_(False), UserSession.expires_at > now).order_by(UserSession.last_activity_at.desc())
        if ref:
            q = q.where(User.username == ref)
        return [{"user": name, "since": s.created_at.strftime("%H:%M:%S"), "last active": s.last_activity_at.strftime("%H:%M:%S"),
                 "from": s.ip} for s, name in (await db.execute(q)).all()]


async def end_sessions(ref: str | None) -> int:
    act_as(SYSTEM)
    async with async_session() as db:
        if ref:
            u = await _user(db, ref)
            await revoke_user_sessions(db, u.id)
            n = 1
        else:
            r = await db.execute(text("UPDATE user_sessions SET revoked = 1 WHERE revoked = 0"))
            n = r.rowcount or 0
        await log_activity(db, "console.end_sessions", None, "system", None, {"flag": True, "who": ref or "everyone"})
        await db.commit()
        return n
