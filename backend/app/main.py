"""imPress Backend — FastAPI application entry point."""

import asyncio
import logging
import secrets
import re
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from . import gpc
from .transport import enforce_https, https_required
from .config import APP_VERSION, settings, check_secure, insecure_settings
from .database import init_db, async_session
from .timeutil import istnow
from .routers import auth, classes, quizzes, polls, device, admin, courses, students, firmware, deployments
from .routers.classes import live_router as classes_live_router  # GET /api/devices/live
from .ws.handler import router as ws_router
from .services.presence import presence_sweep_loop
from .services.sessions import session_cleanup_loop
from .models import User, UserSession
from .auth import hash_password, _sha256_hex, session_token_from
from .dbgateway import DatabaseWriteRefused
from .routers.system import router as system_router
from .routers.approvals import router as approvals_router
from .routers.testmode import router as testmode_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed a default super admin on startup."""
    check_secure(settings)
    # Global policy (v2.2): root's switches. A policy that can't be applied stops a hardened server.
    try:
        policy = gpc.load(settings)
    except gpc.PolicyError as exc:
        raise RuntimeError(f"Global policy: {exc}") from None
    gpc.enforce_startup(settings)
    startup_alerts = [f"Policy file refused: {p}" for p in policy.problems]
    if gpc.get("code.verify_manifest") != "off":
        from . import signing
        code = signing.verify_manifest_if_present()
        if gpc.get("code.verify_manifest") == "enforce" and (not code["present"] or code["problems"]):
            raise RuntimeError("The server's code does not match the root-signed manifest (policy code.verify_manifest=enforce): "
                               + ("; ".join(code["problems"][:5]) or "MANIFEST.json is missing"))
        if code["problems"]:
            startup_alerts.append("The server's code differs from the signed manifest: " + "; ".join(code["problems"][:5]))
    if https_required():
        logger.info("HTTPS required for staff traffic; devices %s (IMPRESS_REQUIRE_HTTPS, #152)",
                    "too" if gpc.device_https_only(settings) else "may use HTTP")
    else:
        logger.warning("IMPRESS_REQUIRE_HTTPS is off: passwords and class data may cross the network unencrypted")
    from .services.firmware_signing import site_key_digest
    signing_key = site_key_digest()          # an unreadable key stops startup here, not at the first upload
    if signing_key:
        logger.info("Firmware must be signed with key %s… (IMPRESS_FIRMWARE_SIGNING_KEY)", signing_key[:16])
    if insecure_settings(settings):
        logger.warning("DEBUG mode with default secrets %s — never deploy like this",
                       insecure_settings(settings))
    await init_db()
    logger.info("Database tables created")

    async with async_session() as db:      # pre-v2.1 <type>-<version>.bin files → registry
        from .services.firmware_store import adopt_legacy_files
        await adopt_legacy_files(db)
        await db.commit()

    # ESP device presence monitor: logs classroom ESP online/offline.
    presence_task = asyncio.create_task(presence_sweep_loop())

    # Session housekeeping: periodically purge expired/revoked user sessions.
    session_task = asyncio.create_task(session_cleanup_loop())

    # Firmware deployments: durable; resumes whatever was running before a restart.
    from .services.deployments import deployments_loop
    deployment_task = asyncio.create_task(deployments_loop())

    # Quiz timing (#73): advances per-question quizzes, ends total-timed ones.
    from .services.quiz_timer import quiz_timer_loop
    quiz_timer_task = asyncio.create_task(quiz_timer_loop())

    # Seed default super admin if no users exist
    async with async_session() as db:
        result = await db.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            password = settings.INITIAL_ADMIN_PASSWORD or secrets.token_urlsafe(12)
            admin_user = User(
                username="admin",
                email="admin@impress.local",
                hashed_password=hash_password(password),
                full_name="Super Admin",
                role="super_admin",
            )
            db.add(admin_user)
            await db.commit()
            if settings.INITIAL_ADMIN_PASSWORD:
                logger.warning("Initial super admin 'admin' created with IMPRESS_INITIAL_ADMIN_PASSWORD")
            else:
                # Shown once, on the very first start only. Change it after login.
                logger.warning("Initial super admin created: username=admin password=%s "
                               "(shown once — change it now)", password)

    # Database integrity (v2.2): baseline or verify (and repair), then the
    # start-up and rolling backups, after the first account exists.
    from .services import integrity
    await integrity.startup()
    integrity_task = asyncio.create_task(integrity.integrity_loop())
    from .services import housekeeping
    maintenance_task = asyncio.create_task(housekeeping.maintenance_loop())
    for note in startup_alerts:
        await housekeeping.report(note)

    try:
        yield
    finally:
        presence_task.cancel()
        try:
            await presence_task
        except asyncio.CancelledError:
            pass
        deployment_task.cancel()
        quiz_timer_task.cancel()
        try:
            await quiz_timer_task
        except asyncio.CancelledError:
            pass
        integrity_task.cancel()
        maintenance_task.cancel()
        session_task.cancel()
        try:
            await session_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="imPress Backend",
    description="ESP32 Classroom Participation System",
    version=APP_VERSION,
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Transport security (#152): HTTPS for staff, browser security headers ──

app.middleware("http")(enforce_https)

# ── Session Activity Middleware ───────────────────────────────────────

# Endpoints that must NOT refresh last_activity_at. These are control-plane /
# polling routes: refreshing them would let an auto-poll keep an otherwise
# idle session alive forever, defeating the idle timeout. The explicit
# /activity ping refreshes itself, and /logout is pointless to refresh.
_ACTIVITY_FREE_PATHS = frozenset({
    "/api/auth/session-status",
    "/api/events",
    "/api/system/status",
    "/api/auth/session",
    "/api/auth/activity",
    "/api/auth/login",
    "/api/auth/logout",
})


@app.middleware("http")
async def database_principal(request: Request, call_next):
    """Every request starts as anonymous for the database gateway (v2.2);
    signing in (user) or a device key (device) raises it."""
    from .dbgateway import ANONYMOUS, act_as
    act_as(ANONYMOUS)
    return await call_next(request)


@app.exception_handler(DatabaseWriteRefused)
async def _write_refused(request: Request, exc: DatabaseWriteRefused):
    """A write the gateway refused: 403, flagged in the activity log."""
    from .dbgateway import SYSTEM, act_as
    from .activity import log_activity
    act_as(SYSTEM)
    try:
        async with async_session() as db:
            await log_activity(db, "db.write_refused", getattr(exc.principal.user, "id", None), "database", None,
                               {"flag": True, "table": exc.table, "by": exc.principal.label, "why": exc.why,
                                "path": request.url.path})
            await db.commit()
    except Exception:
        logger.exception("could not log a refused write")
    return JSONResponse({"detail": {"code": "DB_WRITE_REFUSED",
                                    "message": f"Not allowed to change {exc.table}: {exc.why}"}}, status_code=403)


@app.middleware("http")
async def refresh_session_activity(request: Request, call_next):
    """Touch last_activity_at for live user sessions on each API request.

    Best-effort and never raises: a refresh failure must not take down a
    request. Only a session still inside its idle limit (5 minutes, 30 for
    faculty during their classes) and the hard limit is refreshed, so an
    expired session is never resurrected. Requests the web app makes on its
    own (live refresh, X-Impress-Background: 1) are not activity (v2.2).
    """
    path = request.url.path
    if (path.startswith("/api") and path not in _ACTIVITY_FREE_PATHS
            and request.headers.get("x-impress-background") != "1"):
        token = session_token_from(request)
        if token:
            try:
                from .auth import idle_limit_minutes
                now = istnow()
                async with async_session() as db:
                    session = (await db.execute(select(UserSession).where(
                        UserSession.token_hash == _sha256_hex(token),
                        UserSession.revoked.is_(False),
                        UserSession.expires_at > now,
                    ))).scalar_one_or_none()
                    user = await db.get(User, session.user_id) if session is not None else None
                    if user is not None and now - session.last_activity_at <= timedelta(
                            minutes=await idle_limit_minutes(db, user, now)):
                        session.last_activity_at = now
                        await db.commit()
            except Exception:
                logger.exception("Session activity refresh error")
    return await call_next(request)

# ── Routers ──────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(classes.router)
app.include_router(classes_live_router)  # GET /api/devices/live
app.include_router(quizzes.router)
app.include_router(polls.router)
app.include_router(device.router)
app.include_router(courses.router)
app.include_router(students.router)
app.include_router(firmware.router)
app.include_router(deployments.router)
app.include_router(ws_router)
app.include_router(system_router)
app.include_router(testmode_router)
app.include_router(approvals_router)


# ── Static Files & Templates ────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"
REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
GRAPH_DIR = REPO_ROOT / "graphify-out"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Health Check ─────────────────────────────────────────────────────

@app.get("/health")
@app.get("/api/health")
async def health():
    from .database import engine
    from .migrations import schema_version
    return {"status": "healthy", "version": APP_VERSION, "schema_version": await schema_version(engine)}


# ── Public engineering documentation ─────────────────────────────────

def _documentation_index() -> list[dict[str, str]]:
    """Small, dependency-free searchable catalog of the committed Markdown docs."""
    entries = []
    for path in sorted(DOCS_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
        plain = re.sub(r"[`*_>#\[\]()|]", " ", text)
        plain = re.sub(r"\s+", " ", plain).strip()
        entries.append({"path": str(path.relative_to(REPO_ROOT)), "title": title, "excerpt": plain[:360]})
    return entries


@app.get("/graph", include_in_schema=False)
async def graph_portal(request: Request):
    """Documentation and architecture portal; intentionally public and read-only."""
    return templates.TemplateResponse(request, "graph_portal.html", {"docs": _documentation_index()})


@app.get("/graph/search", include_in_schema=False)
async def graph_search(q: str = ""):
    query = q.casefold().strip()
    docs = _documentation_index()
    if query:
        docs = [doc for doc in docs if query in (doc["title"] + " " + doc["excerpt"] + " " + doc["path"]).casefold()]
    return JSONResponse({"query": q, "results": docs[:50], "total": len(docs)})


@app.get("/graph/visualization", include_in_schema=False)
async def graph_visualization():
    graph = GRAPH_DIR / "graph.html"
    if not graph.is_file():
        raise HTTPException(503, "Knowledge graph has not been generated yet")
    return FileResponse(graph, media_type="text/html", headers={"Cache-Control": "no-cache"})


@app.get("/graph/data", include_in_schema=False)
async def graph_data():
    graph = GRAPH_DIR / "graph.json"
    if not graph.is_file():
        raise HTTPException(503, "Knowledge graph has not been generated yet")
    return FileResponse(graph, media_type="application/json", headers={"Cache-Control": "no-cache"})


# ── Frontend (catch-all SPA route — must be last) ────────────────────

@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str = ""):
    """Serve the SPA index.html for all non-API, non-WS routes."""
    return templates.TemplateResponse(request, "index.html")
