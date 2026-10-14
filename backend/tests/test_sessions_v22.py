"""v2.2 session rules: 5-minute idle limit (30 for faculty in class), one
device per account, background requests are not activity, SHA-256 + bcrypt
passwords with the old format upgraded at sign-in."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from conftest import PASSWORD, auth, login, make_class, make_user

OTHER_DEVICE = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/141.0 Safari/537.36"}


def _age_sessions(db, minutes, user="admin"):
    from app.models import User, UserSession
    from app.timeutil import istnow

    async def go(s):
        uid = (await s.execute(select(User.id).where(User.username == user))).scalar_one()
        for row in (await s.execute(select(UserSession).where(UserSession.user_id == uid))).scalars():
            row.last_activity_at = istnow() - timedelta(minutes=minutes)
    db(go)


def test_idle_five_minutes_signs_out(client, db):
    tok = login(client)
    _age_sessions(db, 4)
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 200
    _age_sessions(db, 6)
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 401


def test_faculty_get_thirty_minutes_during_their_class(client, db):
    su = auth(login(client))
    _, th = make_user(client, su, "prof1")
    cid = make_class(client, su, teacher_ids=[_uid(client, su, "prof1")])
    assert client.post(f"/api/classes/{cid}/activate", headers=su).status_code == 200
    from app.auth import _class_time_cache
    _class_time_cache.clear()
    _age_sessions(db, 20, "prof1")
    assert client.get("/api/auth/me", headers=th).status_code == 200      # in class: 30 minutes
    _age_sessions(db, 31, "prof1")
    assert client.get("/api/auth/me", headers=th).status_code == 401


def test_a_timetable_slot_counts_as_class_time(client, db):
    from app.timeutil import istnow
    from app.schedule import WEEKDAYS
    su = auth(login(client))
    _, th = make_user(client, su, "prof2")
    now = istnow()
    start, end = (now - timedelta(minutes=30)).strftime("%H:%M"), (now + timedelta(minutes=30)).strftime("%H:%M")
    if start > end:
        pytest.skip("slot would cross midnight")
    make_class(client, su, name="Algo", code="ALG1", teacher_ids=[_uid(client, su, "prof2")],
               meeting_schedule=[{"day": WEEKDAYS[now.weekday()], "start": start, "end": end}])
    from app.auth import _class_time_cache
    _class_time_cache.clear()
    _age_sessions(db, 20, "prof2")
    assert client.get("/api/auth/me", headers=th).status_code == 200


def test_a_teacher_outside_class_has_five_minutes(client, db):
    su = auth(login(client))
    _, th = make_user(client, su, "prof3")
    from app.auth import _class_time_cache
    _class_time_cache.clear()
    _age_sessions(db, 6, "prof3")
    assert client.get("/api/auth/me", headers=th).status_code == 401


def test_background_requests_do_not_count_as_activity(client, db):
    tok = login(client)
    _age_sessions(db, 3)
    client.get("/api/auth/me", headers={**auth(tok), "X-Impress-Background": "1"})
    from app.models import UserSession
    from app.timeutil import istnow

    async def last(s):
        return (await s.execute(select(UserSession.last_activity_at))).scalars().first()
    assert istnow() - db(last) > timedelta(minutes=2)


def test_a_second_device_is_refused_and_flagged(client, db, monkeypatch):
    from app.services import events
    alerts = []
    monkeypatch.setattr(events, "alert", lambda msg, level="warning", audience="admins": alerts.append(msg))
    login(client)
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}, headers=OTHER_DEVICE)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "ALREADY_SIGNED_IN"
    assert alerts and "admin" in alerts[0]
    from app.models import ActivityLog

    async def flagged(s):
        return (await s.execute(select(ActivityLog).where(ActivityLog.action == "auth.second_sign_in_blocked"))).scalars().all()
    rows = db(flagged)
    assert len(rows) == 1 and rows[0].details["flag"] is True


def test_the_same_device_may_sign_in_again(client):
    login(client)
    assert client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def test_after_sign_out_or_timeout_another_device_may_sign_in(client, db):
    tok = login(client)
    client.post("/api/auth/logout", headers=auth(tok))
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}, headers=OTHER_DEVICE)
    assert r.status_code == 200
    _age_sessions(db, 6)
    assert client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def test_an_admin_can_end_a_users_sessions(client):
    su = auth(login(client))
    make_user(client, su, "busy1")
    uid = _uid(client, su, "busy1")
    assert client.post("/api/auth/login", json={"username": "busy1", "password": PASSWORD},
                       headers=OTHER_DEVICE).status_code == 409          # make_user's session holds it
    assert client.post(f"/api/admin/users/{uid}/end-sessions", headers=su).status_code == 200
    assert client.post("/api/auth/login", json={"username": "busy1", "password": PASSWORD},
                       headers=OTHER_DEVICE).status_code == 200


def test_passwords_are_sha256_then_bcrypt_and_long_ones_count_in_full():
    from app.auth import hash_password, needs_rehash, verify_password
    a, b = "x" * 72 + "first", "x" * 72 + "second"
    h = hash_password(a)
    assert h.startswith("$i2$") and not needs_rehash(h)
    assert verify_password(a, h) and not verify_password(b, h)    # plain bcrypt would accept b
    assert hash_password(a) != h                                  # salted: same password, new hash


def test_old_hashes_still_work_and_are_upgraded_at_sign_in(client, db):
    import bcrypt
    from app.models import User

    async def downgrade(s):
        u = (await s.execute(select(User).where(User.username == "admin"))).scalar_one()
        u.hashed_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    db(downgrade)
    assert client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200

    async def current(s):
        return (await s.execute(select(User.hashed_password).where(User.username == "admin"))).scalar_one()
    assert db(current).startswith("$i2$")


def _uid(client, headers, username):
    return next(u["id"] for u in client.get("/api/admin/users", headers=headers).json() if u["username"] == username)
