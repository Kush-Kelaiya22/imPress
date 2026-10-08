"""Auth router: login, me, password change. Registration is admin-only (see admin router)."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import UserLogin, TokenResponse, UserResponse, PasswordChange, ProfileUpdate
from ..auth import (
    verify_password,
    get_current_user,
    hash_password,
    create_session,
    oauth2_scheme,
)
from ..activity import log_activity
from ..config import settings
from ..timeutil import istnow

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")

    # Create server-side session
    session, raw_token = await create_session(db, user, request)
    now = istnow()
    expires_at = session.expires_at
    await log_activity(db, "auth.login", user.id, "user", user.id)

    return TokenResponse(
        access_token=raw_token,
        token_type="bearer",
        expires_at=expires_at,
        created_at=session.created_at,
        idle_timeout_s=settings.SESSION_IDLE_MINUTES * 60,
        hard_timeout_s=settings.SESSION_HARD_MINUTES * 60,
        server_time=now,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A logged-in user updates their own display name."""
    new_name = body.full_name.strip()
    if not new_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Full name cannot be blank")

    user.full_name = new_name
    await log_activity(db, "auth.update_profile", user.id, "user", user.id)
    await db.commit()
    return user


@router.post("/change-password")
async def change_password(
    body: PasswordChange,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A logged-in user changes their own password (needs the current one)."""
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")

    user.hashed_password = hash_password(body.new_password)
    await log_activity(db, "auth.change_password", user.id, "user", user.id)
    await db.commit()
    return {"status": "ok", "message": "Password updated"}


@router.post("/logout")
async def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current session."""
    session = getattr(request.state, "session", None)
    if session:
        session.revoked = True
        await db.commit()
    return {"status": "ok"}


@router.get("/session")
async def session_info(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Return session metadata without refreshing activity (light dependency).
    Frontend uses this for countdown timers and 5-min warning.
    """
    from ..auth import validate_session

    # Use light validation (no activity refresh)
    session, user, error = await validate_session(db, token, refresh_activity=False)
    if error or session is None or user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")

    now = istnow()
    idle_remaining = max(0, int((session.last_activity_at - now).total_seconds() + settings.SESSION_IDLE_MINUTES * 60))
    hard_remaining = max(0, int((session.expires_at - now).total_seconds()))

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": session.created_at,
        "last_activity_at": session.last_activity_at,
        "expires_at": session.expires_at,
        "idle_timeout_s": settings.SESSION_IDLE_MINUTES * 60,
        "hard_timeout_s": settings.SESSION_HARD_MINUTES * 60,
        "server_time": now,
        "idle_remaining_s": idle_remaining,
        "hard_remaining_s": hard_remaining,
    }


@router.get("/session-status")
async def session_status(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Live session status for the frontend countdown / warning UI.

    Light validation (NO activity refresh) so auto-polling from the browser
    does not keep an otherwise idle session alive. The frontend polls this and
    shows a 5-minute warning banner before the hard limit, then auto-logs out
    (the endpoint returns 401 once the session expires).
    """
    from ..auth import validate_session

    session, user, error = await validate_session(db, token, refresh_activity=False)
    if error or session is None or user is None:
        code = error or "invalid"
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_EXPIRED",
            headers={"WWW-Authenticate": "Bearer", "X-Session-Code": code},
        )

    now = istnow()
    idle_remaining = max(0, int(
        (session.last_activity_at + timedelta(minutes=settings.SESSION_IDLE_MINUTES) - now).total_seconds()
    ))
    hard_remaining = max(0, int((session.expires_at - now).total_seconds()))
    warning_active = hard_remaining <= settings.SESSION_WARNING_MINUTES * 60

    return {
        "idle_seconds_remaining": idle_remaining,
        "hard_seconds_remaining": hard_remaining,
        "warning_active": warning_active,
        "last_activity_at": session.last_activity_at,
        "expires_at": session.expires_at,
        "server_time": now,
    }


@router.post("/activity")
async def activity_ping(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicit activity ping - refreshes last_activity_at."""
    session = getattr(request.state, "session", None)
    if session:
        now = istnow()
        session.last_activity_at = now
        await db.commit()
        # Calculate hard remaining
        hard_remaining = max(0, int((session.expires_at - now).total_seconds()))
        return {
            "status": "ok",
            "last_activity_at": session.last_activity_at,
            "hard_remaining_s": hard_remaining,
            "server_time": now,
        }
    return {"status": "ok"}
