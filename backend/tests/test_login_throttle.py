"""Password guessing is slowed; new passwords resist trivial guesses (#153)."""

from datetime import timedelta

import pytest

from conftest import PASSWORD, auth, login, make_user


def _try(client, username="impress.default.superAdmin", password="wrong-password"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


@pytest.fixture
def clock(monkeypatch):
    import app.routers.auth as route
    from app.timeutil import istnow
    now = [istnow()]
    monkeypatch.setattr(route, "istnow", lambda: now[0])
    return now


def test_sixth_failure_waits_and_the_password_is_not_checked(client, clock):
    for _ in range(4):
        assert _try(client).status_code == 401
    assert _try(client).status_code == 401                     # 5th failure starts the wait
    r = _try(client, password="admin123")                      # even the right password waits
    assert r.status_code == 429 and r.json()["detail"]["code"] == "TOO_MANY_ATTEMPTS"
    assert int(r.headers["retry-after"]) == 30


def test_the_wait_doubles_then_ends(client, clock):
    for _ in range(5):
        _try(client)
    clock[0] += timedelta(seconds=31)
    assert _try(client).status_code == 401                      # 6th failure: next wait 60 s
    clock[0] += timedelta(seconds=31)
    assert _try(client).status_code == 429
    clock[0] += timedelta(seconds=30)
    assert _try(client, password="admin123").status_code == 200   # no permanent lockout


def test_success_resets_the_username_counter(client, clock):
    for _ in range(4):
        _try(client)
    assert _try(client, password="admin123").status_code == 200
    for _ in range(4):
        assert _try(client).status_code == 401                 # a fresh allowance


def test_one_address_guessing_many_usernames_is_slowed(client, clock):
    for i in range(20):
        assert _try(client, username=f"user{i}").status_code == 401
    assert _try(client, username="someone-else").status_code == 429


def test_another_username_is_not_affected(client, clock):
    su = auth(login(client))
    make_user(client, su, "tch1")
    for _ in range(5):
        _try(client)
    assert _try(client, "tch1", PASSWORD).status_code == 200


def test_counters_survive_a_restart(client, db, clock):
    for _ in range(5):
        _try(client)
    from app.database import engine
    db(lambda s: engine.dispose())
    assert _try(client, password="admin123").status_code == 429


def test_wrong_current_password_is_throttled_too(client, clock):
    su = auth(login(client))
    for _ in range(5):
        r = client.post("/api/auth/change-password", headers=su,
                        json={"current_password": "nope", "new_password": "Brand-new-pass1"})
        assert r.status_code == 400
    r = client.post("/api/auth/change-password", headers=su,
                    json={"current_password": "admin123", "new_password": "Brand-new-pass1"})
    assert r.status_code == 429


@pytest.mark.parametrize("password,why", [
    ("Short-1", "at least 8"),
    ("password123", "too common"),
    ("aaaaaaaaaaaa", "upper-case"),
    ("AAAAAAAAAAAA", "lower-case"),
    ("Aaaaaaaaaaaa", "number"),
    ("Aaaaaaaaaaa1", "special character"),
])
def test_weak_new_passwords_are_refused(client, password, why):
    su = auth(login(client))
    r = client.post("/api/admin/users", headers=su, json={
        "username": "tch1", "email": "t@x.io", "password": password, "full_name": "T", "role": "teacher"})
    assert r.status_code == 422 and why in r.text


def test_password_equal_to_username_is_refused(client):
    su = auth(login(client))
    r = client.post("/api/admin/users", headers=su, json={
        "username": "teacher-anna", "email": "a@x.io", "password": "Teacher-Anna", "full_name": "A",
        "role": "teacher"})
    assert r.status_code == 422 and "username" in r.text


def test_existing_passwords_keep_working(client):
    assert _try(client, password="admin123").status_code == 200      # set before the policy, 8 chars


def test_admin_password_reset_clears_the_accounts_old_failures(client):
    su = auth(login(client))
    uid, _ = make_user(client, su, "reset-me")
    for _ in range(5):
        assert _try(client, "reset-me").status_code == 401
    new = "Reset-By-Admin-19!"
    assert client.post(f"/api/admin/users/{uid}/reset-password", headers=su,
                       json={"new_password": new}).status_code == 200
    assert _try(client, "reset-me", new).status_code == 200


def test_root_password_reset_clears_failures_without_clearing_other_accounts(client, clock):
    from app.services import rootops
    su = auth(login(client))
    make_user(client, su, "other-person")
    for _ in range(5):
        _try(client)
        _try(client, "other-person")
    new = "Root-Recovery-19!"
    client.portal.call(rootops.set_password, "impress.default.superAdmin", new)
    assert _try(client, password=new).status_code == 200
    assert _try(client, "other-person", PASSWORD).status_code == 429


def test_default_password_recovery_clears_the_accounts_throttle(client):
    from app.services import bootstrap
    for _ in range(5):
        _try(client)
    new = "Default-Recovery-19!"
    client.portal.call(bootstrap.reset_default_password, new, False)
    assert _try(client, password=new).status_code == 200


def test_an_old_server_sessions_does_not_block_sign_in(client, db):
    from sqlalchemy import update
    from app.dbgateway import SYSTEM, act_as
    from app.models import UserSession
    login(client)

    async def old_session(s):
        act_as(SYSTEM)
        await s.execute(update(UserSession).values(boot_id="previous-server-run"))
    db(old_session)
    r = client.post("/api/auth/login", headers={"User-Agent": "Firefox on Linux"},
                    json={"username": "impress.default.superAdmin", "password": "admin123"})
    assert r.status_code == 200, r.text


def test_surrounding_username_whitespace_does_not_count_as_a_bad_password(client):
    assert _try(client, "  impress.default.superAdmin  ", "admin123").status_code == 200


def test_address_recovery_is_explicit_and_preserves_other_addresses(client, db):
    from app.dbgateway import SYSTEM, act_as
    from app.models import LoginThrottle
    from app.services import rootops
    from app.timeutil import istnow
    from sqlalchemy import select

    async def counters(s):
        act_as(SYSTEM)
        for key in ("user:impress.default.superadmin", "ip:203.0.113.10", "ip:203.0.113.11"):
            s.add(LoginThrottle(key=key, failures=20, first_at=istnow(), blocked_until=istnow() + timedelta(minutes=10)))
    db(counters)
    assert client.portal.call(rootops.unlock, "impress.default.superAdmin") == 1
    assert client.portal.call(rootops.unlock, "impress.default.superAdmin", "203.0.113.10") == 1

    async def remaining(s):
        return (await s.execute(select(LoginThrottle.key))).scalars().all()
    assert db(remaining) == ["ip:203.0.113.11"]
