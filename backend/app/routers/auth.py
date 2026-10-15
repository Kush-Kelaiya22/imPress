"""Auth router: login, me, password change. Registration is admin-only (see admin router)."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import (UserLogin, TokenResponse, MeResponse, PasswordChange, ProfileUpdate,
                       PreferencesUpdate, OnboardingComplete)
from ..auth import (
    BOOT_ID,
    set_last_account_cookie,
    psid_fingerprint,
    verify_password,
    get_current_user,
    hash_password,
    create_session,
    oauth2_scheme,
    revoke_user_sessions,
    set_session_cookie,
    clear_session_cookie,
    session_token_from,
    validate_session,
    needs_rehash,
    live_sessions,
    same_device,
    idle_limit_minutes,
)
from ..activity import log_activity
from .. import passwords
from ..services import prefs, throttle
from ..config import settings
from ..timeutil import istnow

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # Password guessing is slowed per username and per address (#153); the
    # password is not even checked while a key is waiting.
    now = istnow()
    username = body.username.strip()
    keys = [f"user:{username.lower()}"[:160],
            f"ip:{request.client.host if request.client else '?'}"]
    await throttle.check(db, keys, now)
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        await throttle.failed(db, keys, now)
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    await throttle.succeeded(db, keys[0])
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    from ..dbgateway import act_as, as_user
    act_as(as_user(user))                                  # signed in: writes as this user from here
    if needs_rehash(user.hashed_password):                 # upgrade to the v2.2 format (SHA-256 + bcrypt)
        user.hashed_password = hash_password(body.password)

    # One account, one device (v2.2): a second sign-in from another device or
    # address is refused and flagged while the first session is alive.
    if settings.SINGLE_SESSION:
        elsewhere = [s for s in await live_sessions(db, user, now) if not same_device(s, request)]
        if elsewhere:
            first = max(elsewhere, key=lambda s: s.last_activity_at)
            here = request.client.host if request.client else "?"
            await log_activity(db, "auth.second_sign_in_blocked", user.id, "user", user.id, {
                "flag": True, "ip": here, "user_agent": request.headers.get("user-agent", "")[:200],
                "signed_in_from": first.ip, "since": first.created_at.isoformat()})
            await db.commit()
            from ..services import events
            events.alert(f"Blocked a second sign-in of {user.username} from {here}: "
                         f"already signed in from {first.ip or 'another device'}.", "warning")
            raise HTTPException(status.HTTP_409_CONFLICT, {
                "code": "ALREADY_SIGNED_IN",
                "message": ("This account is already signed in on another device. Sign out there first, "
                            "or wait until that session times out. An administrator can end it under User access."),
            })

    # Create server-side session
    session, raw_token = await create_session(db, user, request)
    now = istnow()
    expires_at = session.expires_at
    await log_activity(db, "auth.login", user.id, "user", user.id)
    await db.commit()
    # The web app keeps the session in an HttpOnly cookie that page scripts
    # cannot read; API clients use the returned token as a bearer token.
    set_session_cookie(response, request, raw_token)
    set_last_account_cookie(response, request, user)

    return TokenResponse(
        access_token=raw_token,
        token_type="bearer",
        must_change_password=bool(user.must_change_password),
        expires_at=expires_at,
        created_at=session.created_at,
        idle_timeout_s=await idle_limit_minutes(db, user, now) * 60,
        hard_timeout_s=settings.SESSION_HARD_MINUTES * 60,
        server_time=now,
    )


def _me_out(user: User) -> MeResponse:
    out = MeResponse.model_validate(user)
    out.preferences = prefs.merged(user.preferences, user.role)
    out.onboarded = user.onboarded_at is not None
    return out


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return _me_out(user)


@router.put("/me", response_model=MeResponse)
async def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A logged-in user changes their own full name and/or the name they want to be called by."""
    if body.full_name is not None:
        if not body.full_name.strip():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Full name cannot be blank")
        user.full_name = body.full_name.strip()
    if body.display_name is not None:
        user.display_name = body.display_name.strip()
    await log_activity(db, "auth.update_profile", user.id, "user", user.id)
    await db.commit()
    return _me_out(user)


@router.get("/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    return prefs.merged(user.preferences, user.role)


@router.put("/preferences")
async def put_preferences(body: PreferencesUpdate, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    """Save some of the user's own preferences (theme, accent, accessibility, advanced mode, dashboard layout)."""
    try:
        clean = prefs.validate(body.model_dump(), user.role)
    except prefs.PreferenceError as exc:
        raise HTTPException(422, str(exc)) from None
    if clean:
        user.preferences = {**(user.preferences or {}), **clean}
        await db.commit()
    return prefs.merged(user.preferences, user.role)


@router.post("/onboarding", response_model=MeResponse)
async def complete_onboarding(body: OnboardingComplete, user: User = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    """The welcome flow's last step: the name they want to be called by and their theme. The password has
    to be chosen first (change-password), for an account that started with a temporary one."""
    if user.must_change_password:
        raise HTTPException(409, {"code": "PASSWORD_CHANGE_REQUIRED", "message": "Choose your password first"})
    user.display_name = body.display_name.strip()
    user.preferences = {**(user.preferences or {}), "theme": body.theme}
    user.onboarded_at = istnow()
    await log_activity(db, "auth.onboarded", user.id, "user", user.id)
    await db.commit()
    return _me_out(user)


@router.post("/change-password")
async def change_password(
    body: PasswordChange,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A logged-in user changes their own password (needs the current one)."""
    key, now = [f"change:{user.id}"], istnow()
    await throttle.check(db, key, now)                      # #153
    if not verify_password(body.current_password, user.hashed_password):
        await throttle.failed(db, key, now)
        await db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    if (why := passwords.problem(body.new_password, user.username, user.role)):
        raise HTTPException(422, f"New password {why}")
    if verify_password(body.new_password, user.hashed_password):
        raise HTTPException(422, "New password must be different from the current one")
    await throttle.succeeded(db, key[0])

    user.hashed_password = hash_password(body.new_password)
    user.must_change_password = False
    current = getattr(request.state, "session", None)
    await revoke_user_sessions(db, user.id, keep_id=current.id if current else None)   # #118
    await log_activity(db, "auth.change_password", user.id, "user", user.id)
    await db.commit()
    return {"status": "ok", "message": "Password updated"}


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Revoke the current session and clear the browser's cookie. An expired
    session is still revoked and its cookie cleared; an unknown one is 401."""
    token = session_token_from(request)
    session = None
    if token:
        if (request.headers.get("authorization") is None
                and request.headers.get("x-impress-request") != "1"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Request refused: missing X-Impress-Request header (CSRF)")
        session, _user, _error = await validate_session(db, token, refresh_activity=False)
    if session is None:
        refused = JSONResponse({"detail": "Not authenticated"}, status_code=401)
        clear_session_cookie(refused, request)
        return refused
    if not session.revoked:
        owner = await db.get(User, session.user_id)
        if owner is not None and owner.is_active:
            from ..dbgateway import act_as, as_user
            act_as(as_user(owner))                       # ending one's own session
            session.revoked = True
            await db.commit()
    clear_session_cookie(response, request)
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
    idle_s = await idle_limit_minutes(db, user, now) * 60
    idle_remaining = max(0, int((session.last_activity_at - now).total_seconds() + idle_s))
    hard_remaining = max(0, int((session.expires_at - now).total_seconds()))

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": session.created_at,
        "last_activity_at": session.last_activity_at,
        "expires_at": session.expires_at,
        "idle_timeout_s": idle_s,
        "hard_timeout_s": settings.SESSION_HARD_MINUTES * 60,
        "server_time": now,
        "idle_remaining_s": idle_remaining,
        "hard_remaining_s": hard_remaining,
        "psid": psid_fingerprint(token),               # 1PSID: a short fingerprint of this session's id, never the id
        "server_run": BOOT_ID,                         # the server run that issued it; a restart ends every session
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
        (session.last_activity_at + timedelta(minutes=await idle_limit_minutes(db, user, now)) - now).total_seconds()
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
