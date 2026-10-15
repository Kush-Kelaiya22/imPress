"""At least one active super admin always remains (#116).

The original failure: a super admin deactivated their own account through
PUT /api/admin/users/{id} and nobody could manage the installation any more.
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from conftest import auth, login, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


def _me(client, headers):
    return client.get("/api/auth/me", headers=headers).json()["id"]


def test_put_can_no_longer_deactivate_anyone(client, su):
    """The original lockout path: PUT with is_active=false on yourself (#116, #119)."""
    me = _me(client, su)
    r = client.put(f"/api/admin/users/{me}", headers=su, json={"is_active": False})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "USE_LIFECYCLE_ENDPOINT"
    assert client.get("/api/auth/me", headers=su).status_code == 200      # still logged in


@pytest.mark.parametrize("call,code", [
    (lambda c, h, me: c.post(f"/api/admin/users/{me}/deactivate", headers=h), "SELF_LOCKOUT"),
    (lambda c, h, me: c.delete(f"/api/admin/users/{me}", headers=h), "SELF_LOCKOUT"),
    # a super admin's role is root's to change (the console), never the web app's
    (lambda c, h, me: c.post(f"/api/admin/users/{me}/role", headers=h, json={"role": "admin"}), "SUPER_ADMIN_VIA_CONSOLE"),
])
def test_no_self_lockout_on_any_route(client, su, call, code):
    _, mine = make_user(client, su, "root3", role="super_admin")
    r = call(client, mine, _me(client, mine))
    assert r.status_code == 403 and r.json()["detail"]["code"] == code


@pytest.mark.parametrize("call", [
    lambda c, h, me: c.post(f"/api/admin/users/{me}/deactivate", headers=h),
    lambda c, h, me: c.delete(f"/api/admin/users/{me}", headers=h),
    lambda c, h, me: c.post(f"/api/admin/users/{me}/reset-password", headers=h, json={}),
])
def test_the_default_super_admin_is_root_s(client, su, call):
    _, other = make_user(client, su, "root4", role="super_admin")
    r = call(client, other, _me(client, su))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "PROTECTED_ACCOUNT"


def test_super_admins_can_still_manage_each_other(client, su):
    other, other_h = make_user(client, su, "root2", role="super_admin")
    assert client.post(f"/api/admin/users/{other}/deactivate", headers=su).status_code == 200
    assert client.get("/api/auth/me", headers=su).status_code == 200


@pytest.mark.parametrize("sql", [
    "UPDATE users SET is_active = 0 WHERE role = 'super_admin'",
    "UPDATE users SET role = 'admin' WHERE role = 'super_admin'",
    "DELETE FROM users WHERE role = 'super_admin'",
])
def test_database_refuses_removing_the_last_super_admin(client, db, sql):
    async def go(s):
        await s.execute(text(sql))
    with pytest.raises(IntegrityError, match="LAST_SUPER_ADMIN"):
        db(go)


def test_trigger_ignores_inactive_and_other_roles(client, db, su):
    uid, _ = make_user(client, su, "tch1")
    async def go(s):
        await s.execute(text("UPDATE users SET is_active = 0, role = 'admin' WHERE id = :i"), {"i": uid})
        await s.execute(text("DELETE FROM user_sessions WHERE user_id = :i"), {"i": uid})
        await s.execute(text("DELETE FROM activity_logs WHERE user_id = :i"), {"i": uid})
        await s.execute(text("DELETE FROM users WHERE id = :i"), {"i": uid})
    db(go)


def test_concurrent_mutual_deactivation_leaves_one_super_admin(client, su):
    """Two super admins disabling each other at the same moment: one must fail."""
    from app.database import async_session
    from app.services import accounts
    from app.models import User
    b, _ = make_user(client, su, "root2", role="super_admin")
    a = _me(client, su)

    async def deactivate(target_id, results):
        async with async_session() as s:
            user = await s.get(User, target_id)
            user.is_active = False
            await asyncio.sleep(0)               # let the other request load its row too
            try:
                await accounts.commit(s)
                results.append("ok")
            except Exception as e:  # HTTPException(409) or a busy database
                results.append(getattr(e, "detail", str(e)))

    async def race():
        results = []
        await asyncio.gather(deactivate(a, results), deactivate(b, results))
        async with async_session() as s:
            n = (await s.execute(text(
                "SELECT COUNT(*) FROM users WHERE role='super_admin' AND is_active=1"))).scalar()
        return results, n

    results, active = client.portal.call(race)
    assert active == 1
    assert results.count("ok") == 1
