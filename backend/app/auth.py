"""JWT + server-side session authentication helpers."""

import base64
import hashlib
import secrets
import time
from datetime import timedelta
from typing import Optional, Tuple

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .timeutil import istnow, istnow_aware
from .models import User, UserSession

SESSION_COOKIE = "impress_session"
CSRF_HEADER = "x-impress-request"       # the web app sends it on every request
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def session_token_from(request) -> str:
    """The session token of an HTTP request or WebSocket handshake: the
    Authorization bearer token (API clients, scripts), else the browser's
    HttpOnly session cookie. Never a URL parameter (#v2.2: tokens in URLs end
    up in proxy and server logs)."""
    authz = request.headers.get("authorization") or ""
    if authz.lower().startswith("bearer "):
        return authz.split(" ", 1)[1].strip()
    return request.cookies.get(SESSION_COOKIE, "")


class _SessionToken(OAuth2PasswordBearer):
    """Bearer header or session cookie. A cookie is sent by the browser on
    its own, so a state-changing request authenticated by it must also carry
    the web app's header: another site cannot add a custom header without a
    CORS preflight this server never grants (CSRF)."""

    async def __call__(self, request: Request) -> str:
        if (request.headers.get("authorization") or "").lower().startswith("bearer "):
            return await super().__call__(request)
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated",
                                headers={"WWW-Authenticate": "Bearer"})
        if request.method not in _SAFE_METHODS and request.headers.get(CSRF_HEADER) != "1":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Request refused: missing X-Impress-Request header (CSRF)")
        return token


oauth2_scheme = _SessionToken(tokenUrl="/api/auth/login")


def set_session_cookie(response, request, token: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=settings.SESSION_HARD_MINUTES * 60, path="/",
                        httponly=True, samesite="strict", secure=request.url.scheme == "https")


LAST_ACCOUNT_COOKIE = "impress_last"


def set_last_account_cookie(response, request, user) -> None:
    """Which account signed in here last, so the sign-in page can offer "Continue as ...". It holds a username and a display
    name only (no secret, never a session), so page scripts may read it: HttpOnly is deliberately off. The password is still
    asked for; this is a convenience, not a login."""
    import json
    from urllib.parse import quote
    value = quote(json.dumps({"u": user.username, "n": (user.display_name or user.full_name or user.username)[:64]}, separators=(",", ":")))
    response.set_cookie(LAST_ACCOUNT_COOKIE, value, max_age=365 * 86400, path="/", httponly=False, samesite="strict",
                        secure=request.url.scheme == "https")


def clear_session_cookie(response, request) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict",
                           secure=request.url.scheme == "https")


# Passwords (v2.2): bcrypt (salted per password, deliberately slow) over the
# SHA-256 of the password. bcrypt alone silently ignores everything after the
# 72nd byte; the SHA-256 pre-hash makes every byte count. "$i2$" marks the
# format; older plain-bcrypt hashes still verify and are upgraded at the next
# successful sign-in (needs_rehash). Plain SHA-256 is never used on its own for
# passwords: it is fast, so a stolen database could be guessed quickly.
_PW_V2 = "$i2$"


def _prehash(password: str) -> bytes:
    return base64.b64encode(hashlib.sha256(password.encode()).digest())


def hash_password(password: str) -> str:
    return _PW_V2 + bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        if hashed.startswith(_PW_V2):
            return bcrypt.checkpw(_prehash(plain), hashed[len(_PW_V2):].encode())
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:                        # not a bcrypt hash at all
        return False


def needs_rehash(hashed: str) -> bool:
    return not hashed.startswith(_PW_V2)


def create_access_token(data: dict) -> str:
    """Legacy JWT creation (kept for device registration / backward compat)."""
    to_encode = data.copy()
    expire = istnow_aware() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ── Session helpers ────────────────────────────────────────────────────

def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


# 1PSID, the first-party session identifier (v2.2): every session id carries the identity of the server run that
# issued it. The identity is new at every start, so a restart ends every session and a token copied earlier is dead.
BOOT_ID = secrets.token_hex(4)


def generate_session_token() -> str:
    """An opaque session id: 'impress_' + this run's identity + 48 random bytes."""
    return f"impress_{BOOT_ID}" + secrets.token_urlsafe(48)


def psid_fingerprint(raw_token: str) -> str:
    """What the person may see of their 1PSID: a short fingerprint, never the id."""
    return _sha256_hex(raw_token)[:12]


async def create_session(
    db: AsyncSession,
    user: User,
    request: Optional[Request] = None,
) -> Tuple[UserSession, str]:
    """
    Create a new server-side session for the user.
    Returns (session_row, raw_session_token).
    """
    raw_token = generate_session_token()
    token_hash = _sha256_hex(raw_token)
    now = istnow()
    expires_at = now + timedelta(minutes=settings.SESSION_HARD_MINUTES)

    ip = ""
    user_agent = ""
    if request:
        ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")

    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        # Legacy NOT NULL/UNIQUE column: holds the hash too. The raw bearer
        # token is never persisted — it's returned to the client once.
        session_token=token_hash,
        created_at=now,
        last_activity_at=now,
        expires_at=expires_at,
        ip=ip,
        user_agent=user_agent,
        revoked=False,
        boot_id=BOOT_ID,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session, raw_token


async def revoke_user_sessions(db: AsyncSession, user_id: int, keep_id: Optional[int] = None,
                               reason: Optional[str] = None) -> None:
    """Revoke every session of a user (except `keep_id`), in the caller's
    transaction (#118). Deactivation, deletion, password and role changes
    call this so no token issued before the change still works, even after a
    later reactivation."""
    if reason is None:                           # why it ended: the web app explains a disabled account properly
        who = await db.get(User, user_id)
        reason = "disabled" if who is not None and not who.is_active else "signed_out"
    q = update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked.is_(False))
    if keep_id is not None:
        q = q.where(UserSession.id != keep_id)
    await db.execute(q.values(revoked=True, end_reason=reason))


async def _load_session_by_hash(db: AsyncSession, token_hash: str) -> Optional[UserSession]:
    """Load a session by its token_hash, checking revoked/expired status."""
    result = await db.execute(
        select(UserSession).where(UserSession.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


# ── Idle timeout: 5 minutes, 30 for faculty during their classes ─────

_class_time_cache: dict[int, tuple[float, bool]] = {}     # user id -> (checked at, in class)


async def in_class_now(db: AsyncSession, user: User, now) -> bool:
    """Is one of this user's classes (as primary teacher or co-faculty) in
    session now: activated, or inside a timetable slot including dated
    changes? Cached for a minute per user: asked on every request."""
    cached = _class_time_cache.get(user.id)
    if cached and time.monotonic() - cached[0] < 60:
        return cached[1]
    from .models import ClassSession, class_faculty
    from .schedule import occupancy
    classes = (await db.execute(select(ClassSession).where(
        (ClassSession.teacher_id == user.id)
        | ClassSession.id.in_(select(class_faculty.c.class_session_id).where(class_faculty.c.user_id == user.id))
    ))).scalars().all()
    result = False
    for cls in classes:
        if cls.is_active or await occupancy(db, "", now, now + timedelta(seconds=1), now=now, class_id=cls.id):
            result = True
            break
    _class_time_cache[user.id] = (time.monotonic(), result)
    return result


async def idle_limit_minutes(db: AsyncSession, user: User, now) -> int:
    # Only faculty get the longer limit while their class is in session; administrators and super admins
    # time out after 5 minutes whatever the timetable says (v2.2).
    from .policy import is_faculty
    if is_faculty(user) and user.is_active and await in_class_now(db, user, now):
        return max(settings.SESSION_CLASS_IDLE_MINUTES, settings.SESSION_IDLE_MINUTES)
    return settings.SESSION_IDLE_MINUTES


async def validate_session(
    db: AsyncSession,
    raw_token: str,
    refresh_activity: bool = True,
) -> Tuple[Optional[UserSession], Optional[User], Optional[str]]:
    """
    Validate a session token.
    Returns (session, user, error_code) where error_code in {None, "hard", "idle", "invalid"}.
    If refresh_activity is True, updates last_activity_at on success.
    """
    if not raw_token:
        return None, None, "invalid"

    token_hash = _sha256_hex(raw_token)
    session = await _load_session_by_hash(db, token_hash)
    if session is None:
        return None, None, "invalid"
    if session.revoked:
        return session, None, "disabled" if session.end_reason == "disabled" else "invalid"
    if session.boot_id != BOOT_ID:               # issued by an earlier run of the server (1PSID)
        return session, None, "restart"

    now = istnow()

    # Hard cap: force-expired no matter what
    if now >= session.expires_at:
        return session, None, "hard"

    user_result = await db.execute(select(User).where(User.id == session.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return session, None, "invalid"
    if not user.is_active:
        return session, None, "disabled"

    # Idle timeout: 5 minutes, 30 while one of the user's classes is in session
    idle_delta = now - session.last_activity_at
    if idle_delta.total_seconds() > await idle_limit_minutes(db, user, now) * 60:
        return session, None, "idle"

    if refresh_activity:
        session.last_activity_at = now
        await db.commit()

    return session, user, None


# ── One account, one device (v2.2) ────────────────────────────────────

def _client_family(user_agent: str) -> str:
    """Browser and OS family from a User-Agent: a new browser version or
    a changed window size is the same device, Chrome on another computer is not."""
    ua = (user_agent or "").lower()
    os_ = next((o for o in ("windows", "android", "iphone", "ipad", "mac os", "linux", "cros") if o in ua), "other")
    app = next((b for b in ("edg/", "opr/", "firefox", "chrome", "safari", "curl", "python") if b in ua), "other")
    return f"{app}|{os_}"


def same_device(session: UserSession, request: Request) -> bool:
    ip = request.client.host if request.client else ""
    return (session.ip or "") == ip and _client_family(session.user_agent) == _client_family(
        request.headers.get("user-agent", ""))


async def live_sessions(db: AsyncSession, user: User, now) -> list[UserSession]:
    """Sessions of this user that would still be accepted now."""
    rows = (await db.execute(select(UserSession).where(
        UserSession.user_id == user.id, UserSession.revoked.is_(False), UserSession.expires_at > now,
        UserSession.boot_id == BOOT_ID))).scalars().all()
    limit = timedelta(minutes=await idle_limit_minutes(db, user, now))
    return [r for r in rows if now - r.last_activity_at <= limit]


# What an account with temporary credentials may call: enough to sign in, set itself up, and sign out.
PENDING_SETUP_PATHS = frozenset({
    "/api/auth/me", "/api/auth/change-password", "/api/auth/logout", "/api/auth/preferences",
    "/api/auth/onboarding", "/api/auth/password-strength", "/api/auth/session", "/api/auth/session-status",
    "/api/auth/activity"})


_ENDED = {"hard": ("SESSION_EXPIRED", "hard"), "idle": ("SESSION_EXPIRED", "idle"),
          "disabled": ("ACCOUNT_DISABLED", "disabled"), "restart": ("SERVER_RESTARTED", "restart")}


def _raise_for(error, user, fallback: HTTPException) -> None:
    """The right 401 for a session that does not hold: the X-Session-Code tells the web app what to say."""
    if error in _ENDED:
        detail, code = _ENDED[error]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                            headers={"WWW-Authenticate": "Bearer", "X-Session-Code": code})
    if error == "invalid" or user is None:
        raise fallback


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user from session token (Bearer).
    Does NOT refresh last_activity_at here — the HTTP session-activity middleware
    handles the refresh once per request (see app.main). Kept separate so
    auto-polling endpoints can read session status without keeping the session alive.
    Raises 401 with detail="SESSION_EXPIRED" and X-Session-Code header on expiry.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    session, user, error = await validate_session(db, token, refresh_activity=False)

    _raise_for(error, user, credentials_exception)

    # Attach session to request.state for downstream use (e.g., /session endpoint)
    request.state.session = session
    request.state.user_id = user.id                      # read by the traffic monitor
    from .dbgateway import act_as, as_user
    act_as(as_user(user))                    # what this request may write (v2.2 database gateway)
    if user.must_change_password and request.url.path not in PENDING_SETUP_PATHS:
        # Temporary credentials (v2.2): the account can do nothing but finish setting itself up.
        raise HTTPException(status.HTTP_403_FORBIDDEN, {
            "code": "PASSWORD_CHANGE_REQUIRED",
            "message": "Choose your own password to finish setting up this account."})
    return user


async def get_current_user_light(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Light version: validates session (hard + idle checks) but does NOT refresh last_activity_at.
    Use for read-only polling endpoints so auto-polling doesn't keep sessions alive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    session, user, error = await validate_session(db, token, refresh_activity=False)

    _raise_for(error, user, credentials_exception)

    from .dbgateway import act_as, as_user
    act_as(as_user(user))
    return user


# Role and permission checks live in policy.py (#122).
