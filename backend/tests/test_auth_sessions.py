"""Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py middleware).

Core contracts pinned here:
- opaque bearer tokens, validated server-side; logout revokes
- idle expiry and hard expiry produce 401 SESSION_EXPIRED with X-Session-Code
- status/polling endpoints never extend a session; real API calls do
- profile + password changes behave and are enforced
"""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from conftest import PASSWORD, auth, login, make_user


def _session_row(db):
    from app.models import UserSession

    async def q(s):
        return (await s.execute(select(UserSession).order_by(UserSession.id.desc()))).scalars().first()
    return db(q)


def _shift_session(db, **cols):
    from app.models import UserSession

    async def go(s):
        await s.execute(update(UserSession).values(**cols))
    db(go)


# ── Login ───────────────────────────────────────────────────────────────────

def test_login_returns_opaque_token_and_timeouts(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].startswith("impress_") and len(body["access_token"]) > 40
    assert body["idle_timeout_s"] == 60 * 60 and body["hard_timeout_s"] == 360 * 60


@pytest.mark.parametrize("username,password", [("admin", "wrong"), ("nobody", "admin123"), ("", "")])
def test_login_rejects_bad_credentials(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 401


def test_login_rejects_disabled_account(client):
    admin = auth(login(client))
    uid, _ = make_user(client, admin, "tina")
    assert client.post(f"/api/admin/users/{uid}/deactivate", headers=admin).status_code == 200
    r = client.post("/api/auth/login", json={"username": "tina", "password": PASSWORD})
    assert r.status_code == 403


def test_each_login_is_an_independent_session(client):
    a, b = login(client), login(client)
    assert a != b
    client.post("/api/auth/logout", headers=auth(a))
    assert client.get("/api/auth/me", headers=auth(a)).status_code == 401
    assert client.get("/api/auth/me", headers=auth(b)).status_code == 200


# ── Profile + password ──────────────────────────────────────────────────────

def test_profile_update_trims_and_rejects_blank(client):
    h = auth(login(client))
    assert client.put("/api/auth/me", headers=h, json={"full_name": "  Dr. Admin  "}).json()["full_name"] == "Dr. Admin"
    assert client.put("/api/auth/me", headers=h, json={"full_name": "   "}).status_code == 400
    assert client.put("/api/auth/me", headers=h, json={"full_name": ""}).status_code == 422


def test_change_password_requires_current_and_takes_effect(client):
    h = auth(login(client))
    bad = client.post("/api/auth/change-password", headers=h,
                      json={"current_password": "nope", "new_password": "N3w-password"})
    assert bad.status_code == 400
    short = client.post("/api/auth/change-password", headers=h,
                        json={"current_password": "admin123", "new_password": "123"})
    assert short.status_code == 422
    ok = client.post("/api/auth/change-password", headers=h,
                     json={"current_password": "admin123", "new_password": "N3w-password"})
    assert ok.status_code == 200
    assert client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "admin", "password": "N3w-password"}).status_code == 200


# ── Expiry ──────────────────────────────────────────────────────────────────

def test_idle_expiry_reports_idle_code(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    _shift_session(db, last_activity_at=istnow() - timedelta(minutes=61))
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 401
    assert r.json()["detail"] == "SESSION_EXPIRED" and r.headers["x-session-code"] == "idle"


def test_hard_expiry_reports_hard_code_even_if_active(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    _shift_session(db, expires_at=istnow() - timedelta(seconds=1))
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 401 and r.headers["x-session-code"] == "hard"


def test_expired_session_cannot_be_revived_by_activity_ping(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    _shift_session(db, last_activity_at=istnow() - timedelta(minutes=61))
    assert client.post("/api/auth/activity", headers=h).status_code == 401
    assert client.get("/api/auth/me", headers=h).status_code == 401


# ── Activity refresh semantics ──────────────────────────────────────────────

def test_status_endpoints_do_not_extend_the_session(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    old = istnow() - timedelta(minutes=30)
    _shift_session(db, last_activity_at=old)
    for path in ("/api/auth/session", "/api/auth/session-status"):
        assert client.get(path, headers=h).status_code == 200
    assert abs((_session_row(db).last_activity_at - old).total_seconds()) < 1


def test_regular_api_call_extends_the_session(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    _shift_session(db, last_activity_at=istnow() - timedelta(minutes=30))
    assert client.get("/api/admin/users", headers=h).status_code == 200
    assert (istnow() - _session_row(db).last_activity_at).total_seconds() < 5


def test_explicit_activity_ping_extends_the_session(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    _shift_session(db, last_activity_at=istnow() - timedelta(minutes=30))
    r = client.post("/api/auth/activity", headers=h)
    assert r.status_code == 200 and r.json()["hard_remaining_s"] > 0
    assert (istnow() - _session_row(db).last_activity_at).total_seconds() < 5


def test_session_status_counts_down_and_warns_near_hard_limit(client, db):
    from app.timeutil import istnow
    h = auth(login(client))
    s = client.get("/api/auth/session-status", headers=h).json()
    assert 0 < s["idle_seconds_remaining"] <= 3600 and s["warning_active"] is False
    _shift_session(db, expires_at=istnow() + timedelta(minutes=3))
    s = client.get("/api/auth/session-status", headers=h).json()
    assert s["warning_active"] is True and s["hard_seconds_remaining"] <= 180


def test_session_info_identifies_the_user(client):
    info = client.get("/api/auth/session", headers=auth(login(client))).json()
    assert info["username"] == "admin" and info["role"] == "super_admin"
    assert info["idle_remaining_s"] > 0 and info["hard_remaining_s"] > 0


def test_session_status_without_token_is_401(client):
    assert client.get("/api/auth/session-status").status_code == 401
    assert client.get("/api/auth/session-status", headers=auth("impress_bogus")).status_code == 401


# ── Session housekeeping service ────────────────────────────────────────────

def test_cleanup_removes_only_dead_sessions(client, db):
    from app.models import UserSession
    from app.services.sessions import _cleanup_once
    from app.timeutil import istnow
    live = login(client)
    for _ in range(3):
        login(client)

    async def age(s):
        rows = (await s.execute(select(UserSession).order_by(UserSession.id))).scalars().all()
        rows[1].revoked = True
        rows[2].expires_at = istnow() - timedelta(seconds=1)
        rows[3].last_activity_at = istnow() - timedelta(hours=2)
    db(age)
    assert client.portal.call(_cleanup_once) == 3
    assert client.get("/api/auth/me", headers=auth(live)).status_code == 200
