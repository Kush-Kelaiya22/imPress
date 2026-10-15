"""System status, live events and database administration (v2.2).

- GET  /api/system/status         banner data (test mode, database state): public
- GET  /api/events                Server-Sent Events: live refresh, toasts, status
- GET  /api/admin/system/integrity             verification, backups, Degraded
- POST /api/admin/system/integrity/verify      verify now
- POST /api/admin/system/integrity/acknowledge clear Degraded (super admin may also accept the current state)
- POST /api/admin/system/clear                 clear class data or reset everything (super admin, typed confirmation,
                                               a second super admin's approval: services/approvals.py)
- GET  /api/admin/system/policy                the effective global policy (read-only: root changes it)
- GET  /api/system/signing-key                 public key that verifies this server's signed exports
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc, signing
from ..activity import log_activity
from ..auth import oauth2_scheme, validate_session
from ..config import APP_VERSION
from ..database import async_session, get_db
from ..dbgateway import SYSTEM, act_as
from ..models import User
from ..policy import allowed, require
from ..services import approvals, auditsink, events, integrity, rootops

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

KEEPALIVE_S = 15
RECHECK_S = 30


@router.get("/api/system/status")
async def system_status(db: AsyncSession = Depends(get_db)):
    from ..config import APP_RELEASE
    from ..models import FirmwareDeployment
    from ..services import boot_verify, features, iips
    st = integrity.status()
    tm = st.get("test_mode") or {}
    running = (await db.execute(select(func.count()).select_from(FirmwareDeployment)
                                .where(FirmwareDeployment.state == "running"))).scalar_one() if features.enabled("update_overlay") else 0
    # banners shown above every page, in this order (test mode and the integrity warning can both be on)
    banners = []
    if not iips.state()["enabled"]:
        banners.append({"id": "iips", "level": "danger", "text": "imPress Integrity Protection Service is disabled. Proceed with caution."})
    if tm.get("on"):
        banners.append({"id": "test_mode", "level": "warning", "since": tm.get("since"),
                        "text": "Test mode: you are working on test data, not the real database."})
    # no database state here: the integrity state is for administrators (/api/events, System page)
    return {"version": APP_VERSION, "release": APP_RELEASE, "test_mode": bool(tm.get("on")), "test_mode_since": tm.get("since"),
            "test_mode_forced": bool(gpc.get("test_mode.forced")), "banners": banners,
            "integrity_protection": iips.state()["status"], "locked": boot_verify.locked() or iips.locked(),
            "updating": {"active": bool(running), "deployments": running,
                         "message": "We are updating the system. Please wait a moment: this page will return as soon as the update has finished."},
            "feature_flags": features.snapshot(),
            "features": {"ota": bool(gpc.get("ota.enabled")), "test_data": bool(gpc.get("test_mode.allowed"))}}


@router.get("/api/events")
async def event_stream(request: Request, token: str = Depends(oauth2_scheme)):
    """One stream per signed-in browser. Never extends the session: when the
    session ends (idle, logout, revoked) the stream says so and closes."""
    async with async_session() as db:
        _session, user, error = await validate_session(db, token, refresh_activity=False)
    if error or user is None:
        raise HTTPException(401, "SESSION_EXPIRED")
    if user.must_change_password:                        # temporary credentials: no live alerts yet
        raise HTTPException(403, {"code": "PASSWORD_CHANGE_REQUIRED", "message": "Choose your own password first"})
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
                if '"type": "session_ended"' in data:
                    return
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
    accept_current: bool = False      # super admin: re-seal the database as it is now (needs an approval)
    approval_id: int | None = None


@router.post("/api/admin/system/integrity/acknowledge")
async def integrity_acknowledge(body: Acknowledge, user: User = Depends(require("users.manage")),
                                db: AsyncSession = Depends(get_db)):
    if body.accept_current:
        if not allowed(user, "users.assign_role"):
            raise HTTPException(403, {"code": "FORBIDDEN", "message": "Only a super admin can accept the current state"})
        await approvals.require(db, user, "integrity.accept_current", {}, body.approval_id)
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
    approval_id: int | None = None


@router.get("/api/admin/system/clear")
async def clear_options(user: User = Depends(require("users.assign_role"))):
    return {"scopes": {k: {"description": d, "confirm": c} for k, (d, c) in CLEAR_SCOPES.items()
                       if k != "everything" or gpc.get("system.reset_everything_allowed")},
            "dual_control": gpc.get("dual_control.enabled"),
            "delay_minutes": gpc.get("dual_control.delay_minutes"),
            "retained_audit_days": gpc.get("audit.min_retention_days")}


@router.post("/api/admin/system/clear")
async def clear_data(body: ClearRequest, request: Request, user: User = Depends(require("users.assign_role"))):
    """The only way to clear the database: a super admin, a typed
    confirmation, a backup first. Runs through the gateway as the system."""
    if body.scope not in CLEAR_SCOPES:
        raise HTTPException(422, "scope must be class_data or everything")
    if body.confirm.strip() != CLEAR_SCOPES[body.scope][1]:
        raise HTTPException(422, {"code": "CONFIRM", "message": f"Type {CLEAR_SCOPES[body.scope][1]} to confirm"})
    if body.scope == "everything" and not gpc.get("system.reset_everything_allowed"):
        raise HTTPException(403, {"code": "POLICY_DISABLED",
                                  "message": "A full reset is switched off by policy (system.reset_everything_allowed)"})
    async with async_session() as adb:                  # the approval is spent first, in its own transaction
        await approvals.require(adb, user, f"system.clear.{body.scope}", {}, body.approval_id)
    keep_session = getattr(request.state, "session", None)
    backup = await rootops.clear_data(body.scope, keep_user_id=user.id, keep_session_id=keep_session.id if keep_session else None)
    if body.scope == "everything":
        from ..services import bootstrap
        await bootstrap.after_reset(user.username)
    events.alert(f"{user.username} cleared the database ({body.scope.replace('_', ' ')}). "
                 + (f"A copy was saved first ({backup})." if backup else "No copy was made: test mode makes no backups."),
                 "warning", "all")
    return {"status": "ok", "backup": backup}


@router.get("/api/admin/system/policy")
async def policy_view(user: User = Depends(require("audit.read"))):
    """The effective policy, with who set each flag and who enforces it since when. Administrators read it; only root (the
    console) and, for the few operational flags, a super admin (below) change it."""
    problems = signing.verify_manifest_if_present()
    return {**gpc.describe(), "audit": auditsink.status(), "code_manifest": problems}


@router.get("/api/admin/system/policy/history")
async def policy_history(flag: str | None = None, limit: int = 50, user: User = Depends(require("audit.read"))):
    from .. import gpcstore
    return {"history": gpcstore.history(flag, min(max(limit, 1), 200)), "restrictions": gpcstore.restrictions()}


class PolicyChange(BaseModel):
    value: object = None
    note: str = ""
    password: str
    code: str = ""


def _refused(exc) -> HTTPException:
    return HTTPException(exc.status, {"code": exc.code, "message": exc.message})


@router.put("/api/admin/system/policy/{name}")
async def policy_set(name: str, body: PolicyChange, user: User = Depends(require("users.assign_role")),
                     db: AsyncSession = Depends(get_db)):
    """A super admin changes an operational flag (editable_by = super admin): password and second factor, recorded with who and
    when, alerts the administrators. Every other flag is root's, in the console."""
    from .. import gpcstore
    from ..config import settings
    await approvals.step_up(db, user, body.password, body.code)
    try:
        entry = gpcstore.set_flag(name, body.value, user.username, gpcstore.SUPER, "web", body.note[:200])
    except gpcstore.PolicyRefused as exc:
        raise _refused(exc) from None
    gpc.load(settings)
    await log_activity(db, "policy.set", user.id, "system", None, {"flag": True, "name": name, "value": body.value, "note": body.note[:200]})
    await db.commit()
    events.alert(f"{user.username} changed policy {name} to {body.value!r}.", "warning")
    return entry


@router.delete("/api/admin/system/policy/{name}")
async def policy_reset(name: str, password: str, code: str = "", user: User = Depends(require("users.assign_role")),
                       db: AsyncSession = Depends(get_db)):
    from .. import gpcstore
    from ..config import settings
    await approvals.step_up(db, user, password, code)
    try:
        done = gpcstore.reset_flags([name], user.username, gpcstore.SUPER, "web")
    except gpcstore.PolicyRefused as exc:
        raise _refused(exc) from None
    gpc.load(settings)
    await log_activity(db, "policy.reset", user.id, "system", None, {"flag": True, "name": name})
    await db.commit()
    return {"reset": done}


@router.get("/api/system/errors")
async def error_catalogue(user: User = Depends(require("audit.read"))):
    """The error catalogue (impress.errors.json): categories, codes, what they mean and what to do."""
    from .. import errors
    return {"categories": errors.categories(), "errors": errors.catalogue()}


_csp_window = {"t": 0.0, "n": 0}


@router.post("/api/system/csp-report", status_code=204)
async def csp_report(request: Request):
    """Browsers post here when the Content-Security-Policy blocks something. Public (the browser
    sends it without credentials), so: a small body, at most 30 reports a minute for the whole
    server, and no database write: the report goes to the log and the external audit trail."""
    now = time.monotonic()
    if now - _csp_window["t"] > 60:
        _csp_window.update(t=now, n=0)
    _csp_window["n"] += 1
    if _csp_window["n"] <= 30:
        try:
            body = json.loads((await request.body())[:4000] or b"{}")
        except ValueError:
            body = {}
        rep = body.get("csp-report", {}) if isinstance(body, dict) else {}
        details = {"flag": True, "directive": str(rep.get("violated-directive", ""))[:80],
                   "blocked": str(rep.get("blocked-uri", ""))[:120],
                   "page": urlparse(str(rep.get("document-uri", ""))).path[:120]}
        logger.warning("CSP violation: %s", details)
        auditsink.emit("ui.csp_violation", None, "system", None, details)
    return Response(status_code=204)


@router.get("/api/system/signing-key")
async def signing_key():
    """Public: the key that verifies the server's signed exports (scripts/verify_export.py)."""
    return signing.export_public_key()
