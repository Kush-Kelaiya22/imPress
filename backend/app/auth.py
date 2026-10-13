"""JWT + server-side session authentication helpers."""

import hashlib
import secrets
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


def clear_session_cookie(response, request) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict",
                           secure=request.url.scheme == "https")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    """Legacy JWT creation (kept for device registration / backward compat)."""
    to_encode = data.copy()
    expire = istnow_aware() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ── Session helpers ────────────────────────────────────────────────────

def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def generate_session_token() -> str:
    """Generate an opaque session token prefixed for easy identification."""
    return "impress_" + secrets.token_urlsafe(48)


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
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session, raw_token


async def revoke_user_sessions(db: AsyncSession, user_id: int, keep_id: Optional[int] = None) -> None:
    """Revoke every session of a user (except `keep_id`), in the caller's
    transaction (#118). Deactivation, deletion, password and role changes
    call this so no token issued before the change still works, even after a
    later reactivation."""
    q = update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked.is_(False))
    if keep_id is not None:
        q = q.where(UserSession.id != keep_id)
    await db.execute(q.values(revoked=True))


async def _load_session_by_hash(db: AsyncSession, token_hash: str) -> Optional[UserSession]:
    """Load a session by its token_hash, checking revoked/expired status."""
    result = await db.execute(
        select(UserSession).where(UserSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session is None or session.revoked:
        return None
    return session


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

    now = istnow()

    # Hard cap: force-expired no matter what
    if now >= session.expires_at:
        return session, None, "hard"

    # Idle timeout: no activity for SESSION_IDLE_MINUTES
    idle_delta = now - session.last_activity_at
    if idle_delta.total_seconds() > settings.SESSION_IDLE_MINUTES * 60:
        return session, None, "idle"

    # Valid session - optionally refresh activity timestamp
    user_result = await db.execute(select(User).where(User.id == session.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        return session, None, "invalid"

    if refresh_activity:
        session.last_activity_at = now
        await db.commit()

    return session, user, None


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

    if error == "hard":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_EXPIRED",
            headers={"WWW-Authenticate": "Bearer", "X-Session-Code": "hard"},
        )
    if error == "idle":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_EXPIRED",
            headers={"WWW-Authenticate": "Bearer", "X-Session-Code": "idle"},
        )
    if error == "invalid" or user is None:
        raise credentials_exception

    # Attach session to request.state for downstream use (e.g., /session endpoint)
    request.state.session = session
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

    if error == "hard":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_EXPIRED",
            headers={"WWW-Authenticate": "Bearer", "X-Session-Code": "hard"},
        )
    if error == "idle":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_EXPIRED",
            headers={"WWW-Authenticate": "Bearer", "X-Session-Code": "idle"},
        )
    if error == "invalid" or user is None:
        raise credentials_exception

    return user


# Role and permission checks live in policy.py (#122).
