"""System status, live events and database administration (v2.2).

- GET  /api/system/status         banner data (test mode, database state): public
- GET  /api/events                Server-Sent Events: live refresh, toasts, status
- GET  /api/admin/system/integrity             verification, backups, Degraded
- POST /api/admin/system/integrity/verify      verify now
- POST /api/admin/system/integrity/acknowledge clear Degraded (super admin may also accept the current state)
- POST /api/admin/system/clear                 clear class data or reset everything (super admin, typed confirmation)
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..activity import log_activity
from ..auth import oauth2_scheme, validate_session
from ..config import APP_VERSION
from ..database import async_session, get_db
from ..dbgateway import SYSTEM, act_as
from ..models import User
from ..policy import allowed, require
from ..services import events, integrity
from ..timeutil import istnow

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

KEEPALIVE_S = 15
RECHECK_S = 30


@router.get("/api/system/status")
async def system_status():
    st = integrity.status()
    tm = st.get("test_mode") or {}
    # no database state here: the integrity state is for administrators (/api/events, System page)
    return {"version": APP_VERSION, "test_mode": bool(tm.get("on")), "test_mode_since": tm.get("since")}


@router.get("/api/events")
async def event_stream(request: Request, token: str = Depends(oauth2_scheme)):
    """One stream per signed-in browser. Never extends the session: when the
    session ends (idle, logout, revoked) the stream says so and closes."""
    async with async_session() as db:
        _session, user, error = await validate_session(db, token, refresh_activity=False)
    if error or user is None:
        raise HTTPException(401, "SESSION_EXPIRED")
    return StreamingResponse(stream_events(token, user, request.is_disconnected), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


async def stream_events(token: str, user: User, is_disconnected):
    is_admin = allowed(user, "users.manage")
    sub = events.subscribe(admin=is_admin, user_id=user.id)
    try:
        st = integrity.status()
        first = {"type": "status", "test_mode": bool((st.get("test_mode") or {}).get("on"))}
        if is_admin:
            first["db"] = st["db"]
        yield _sse(first)
        last_check = asyncio.get_running_loop().time()
        while True:
            if await is_disconnected():
                return
            try:
                data = await asyncio.wait_for(sub.queue.get(), timeout=KEEPALIVE_S)
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
            now = asyncio.get_running_loop().time()
            if now - last_check >= RECHECK_S:
                last_check = now
                async with async_session() as db:
                    _s, u, err = await validate_session(db, token, refresh_activity=False)
                if err or u is None:
                    yield _sse({"type": "session_ended", "reason": err or "invalid"})
                    return
    finally:
        events.unsubscribe(sub)


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, default=str)}\n\n"


@router.get("/api/admin/system/integrity")
async def integrity_info(user: User = Depends(require("audit.read"))):
    st = integrity.status()
    return {**st, "backups": integrity.backups_info(), "backup_dir": str(integrity.backup_dir()),
            "interval_s": integrity.settings.INTEGRITY_INTERVAL_S}


@router.post("/api/admin/system/integrity/verify")
async def integrity_verify(user: User = Depends(require("users.manage"))):
    await integrity.check_and_backup()
    return integrity.status()


class Acknowledge(BaseModel):
    accept_current: bool = False      # super admin: re-seal the database as it is now


@router.post("/api/admin/system/integrity/acknowledge")
async def integrity_acknowledge(body: Acknowledge, user: User = Depends(require("users.manage")),
                                db: AsyncSession = Depends(get_db)):
    if body.accept_current:
        if not allowed(user, "users.assign_role"):
            raise HTTPException(403, {"code": "FORBIDDEN", "message": "Only a super admin can accept the current state"})
        act_as(SYSTEM)
        await integrity.reseal_everything(f"accepted by {user.username}")
    await integrity.acknowledge()
    await log_activity(db, "system.db_acknowledged", user.id, "system", None,
                       {"accepted_current": body.accept_current})
    await db.commit()
    return integrity.status()


CLEAR_SCOPES = {
    "class_data": ("Delete every course, class, student, enrolment, quiz, poll, answer, vote, attendance and "
                   "timetable change. Accounts, devices and firmware stay.", "DELETE CLASS DATA"),
    "everything": ("Reset imPress: everything above, plus devices, firmware records, deployments, the activity "
                   "log and every account except yours.", "RESET EVERYTHING"),
}


class ClearRequest(BaseModel):
    scope: str
    confirm: str


@router.get("/api/admin/system/clear")
async def clear_options(user: User = Depends(require("users.assign_role"))):
    return {k: {"description": d, "confirm": c} for k, (d, c) in CLEAR_SCOPES.items()}


@router.post("/api/admin/system/clear")
async def clear_data(body: ClearRequest, request: Request, user: User = Depends(require("users.assign_role"))):
    """The only way to clear the database: a super admin, a typed
    confirmation, a backup first. Runs through the gateway as the system."""
    if body.scope not in CLEAR_SCOPES:
        raise HTTPException(422, "scope must be class_data or everything")
    if body.confirm.strip() != CLEAR_SCOPES[body.scope][1]:
        raise HTTPException(422, {"code": "CONFIRM", "message": f"Type {CLEAR_SCOPES[body.scope][1]} to confirm"})
    backup = integrity.backup_dir() / f"before-clear-{istnow():%Y%m%d-%H%M%S}.db"
    await integrity.copy_live_to(backup)
    keep_session = getattr(request.state, "session", None)
    act_as(SYSTEM)
    class_tables = ["quiz_answers", "quiz_questions", "quizzes", "poll_votes", "polls", "attendance",
                    "class_occurrence_exceptions", "student_enrollments", "class_faculty", "class_sessions",
                    "students", "courses", "schedule_sources"]
    async with async_session() as db:
        await db.execute(text("PRAGMA defer_foreign_keys = ON"))
        await db.execute(text("UPDATE esp_devices SET student_enrollment_id = NULL"))
        await db.execute(text("UPDATE student_modules SET class_session_id = NULL"))
        for t in class_tables:
            await db.execute(text(f"DELETE FROM {t}"))
        if body.scope == "everything":
            for t in ("student_modules", "deployment_targets", "firmware_deployments", "firmware_artifacts",
                      "esp_devices", "activity_logs", "login_throttle"):
                await db.execute(text(f"DELETE FROM {t}"))
            await db.execute(text("DELETE FROM user_sessions WHERE id != :k"),
                             {"k": keep_session.id if keep_session else -1})
            await db.execute(text("DELETE FROM users WHERE id != :u"), {"u": user.id})
        await log_activity(db, f"system.clear_{body.scope}", user.id, "system", None,
                           {"flag": True, "backup": backup.name})
        await db.commit()
    events.alert(f"{user.username} cleared the database ({body.scope.replace('_', ' ')}). "
                 f"A copy was saved first ({backup.name}).", "warning", "all")
    return {"status": "ok", "backup": backup.name}
