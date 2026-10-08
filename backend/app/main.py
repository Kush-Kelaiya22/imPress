"""imPress Backend — FastAPI application entry point."""

import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from .config import settings, check_secure, insecure_settings
from .database import init_db, async_session
from .timeutil import istnow
from .routers import auth, classes, quizzes, polls, device, admin, courses, students
from .routers.classes import live_router as classes_live_router  # GET /api/devices/live
from .ws.handler import router as ws_router
from .services.presence import presence_sweep_loop
from .services.sessions import session_cleanup_loop
from .models import User, UserSession
from .auth import hash_password, _sha256_hex


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed a default super admin on startup."""
    check_secure(settings)
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

    try:
        yield
    finally:
        presence_task.cancel()
        try:
            await presence_task
        except asyncio.CancelledError:
            pass
        session_task.cancel()
        try:
            await session_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="imPress Backend",
    description="ESP32 Classroom Participation System",
    version="1.0.0",
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

# ── Session Activity Middleware ───────────────────────────────────────

# Endpoints that must NOT refresh last_activity_at. These are control-plane /
# polling routes: refreshing them would let an auto-poll keep an otherwise
# idle session alive forever, defeating the idle timeout. The explicit
# /activity ping refreshes itself, and /logout is pointless to refresh.
_ACTIVITY_FREE_PATHS = frozenset({
    "/api/auth/session-status",
    "/api/auth/session",
    "/api/auth/activity",
    "/api/auth/login",
    "/api/auth/logout",
})


@app.middleware("http")
async def refresh_session_activity(request: Request, call_next):
    """Touch last_activity_at for live user sessions on each API request.

    Best-effort and never raises: a refresh failure must not take down a
    request. Only sessions that are still inside the idle + hard windows are
    refreshed (mirrors validate_session) so an expired session is never
    resurrected by the refresh.
    """
    path = request.url.path
    if path.startswith("/api") and path not in _ACTIVITY_FREE_PATHS:
        authz = request.headers.get("authorization")
        if authz and authz.lower().startswith("bearer "):
            token = authz.split(" ", 1)[1].strip()
            if token:
                try:
                    now = istnow()
                    idle_cutoff = now - timedelta(
                        minutes=settings.SESSION_IDLE_MINUTES
                    )
                    async with async_session() as db:
                        result = await db.execute(
                            select(UserSession).where(
                                UserSession.token_hash == _sha256_hex(token),
                                UserSession.revoked.is_(False),
                                UserSession.expires_at > now,
                                UserSession.last_activity_at > idle_cutoff,
                            )
                        )
                        session = result.scalar_one_or_none()
                        if session is not None:
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
app.include_router(ws_router)


# ── Static Files & Templates ────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Health Check ─────────────────────────────────────────────────────

@app.get("/health")
async def health():
    from .database import engine
    from .migrations import schema_version
    return {"status": "healthy", "schema_version": await schema_version(engine)}


# ── Frontend (catch-all SPA route — must be last) ────────────────────

@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str = ""):
    """Serve the SPA index.html for all non-API, non-WS routes."""
    return templates.TemplateResponse(request, "index.html")
