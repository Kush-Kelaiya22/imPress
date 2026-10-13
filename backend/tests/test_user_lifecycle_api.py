"""Separate account operations and server-provided allowed_actions (#119)."""

import pytest

from conftest import auth, login, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


def _row(client, h, uid):
    return next(u for u in client.get("/api/admin/users", headers=h).json() if u["id"] == uid)


def test_deactivate_and_reactivate(client, su):
    uid, _ = make_user(client, su, "tch1")
    r = client.post(f"/api/admin/users/{uid}/deactivate", headers=su)
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert "reactivate" in r.json()["allowed_actions"] and "deactivate" not in r.json()["allowed_actions"]
    r = client.post(f"/api/admin/users/{uid}/reactivate", headers=su)
    assert r.status_code == 200 and r.json()["is_active"] is True


def test_patch_edits_profile_only(client, su):
    uid, _ = make_user(client, su, "tch1")
    r = client.patch(f"/api/admin/users/{uid}", headers=su, json={"full_name": "Asha R"})
    assert r.status_code == 200 and r.json()["full_name"] == "Asha R"
    for body in ({"is_active": False}, {"role": "admin"}):
        r = client.patch(f"/api/admin/users/{uid}", headers=su, json=body)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "USE_LIFECYCLE_ENDPOINT"
    assert _row(client, su, uid)["is_active"] is True


def test_duplicate_email_on_edit_is_400(client, su):
    uid, _ = make_user(client, su, "tch1")
    make_user(client, su, "tch2")
    r = client.patch(f"/api/admin/users/{uid}", headers=su, json={"email": "tch2@example.edu"})
    assert r.status_code == 400


def test_allowed_actions_for_a_super_admin(client, su):
    me = client.get("/api/auth/me", headers=su).json()["id"]
    uid, _ = make_user(client, su, "tch1")
    assert _row(client, su, me)["allowed_actions"] == ["edit", "reset_password"]
    assert _row(client, su, uid)["allowed_actions"] == [
        "edit", "deactivate", "change_role", "reset_password", "delete"]


def test_allowed_actions_for_an_admin(client, su):
    me = client.get("/api/auth/me", headers=su).json()["id"]
    tid, _ = make_user(client, su, "tch1")
    _, adm = make_user(client, su, "adm1", role="admin")
    assert _row(client, adm, me)["allowed_actions"] == []                 # super admin: hands off
    assert "change_role" not in _row(client, adm, tid)["allowed_actions"]   # roles: super admin only


ROUTES = {
    "edit": lambda c, h, u: c.patch(f"/api/admin/users/{u}", headers=h, json={"full_name": "X"}),
    "deactivate": lambda c, h, u: c.post(f"/api/admin/users/{u}/deactivate", headers=h),
    "reactivate": lambda c, h, u: c.post(f"/api/admin/users/{u}/reactivate", headers=h),
    "change_role": lambda c, h, u: c.post(f"/api/admin/users/{u}/role", headers=h, json={"role": "teacher"}),
    "reset_password": lambda c, h, u: c.post(f"/api/admin/users/{u}/reset-password", headers=h,
                                             json={"new_password": "Reset-123x"}),
    "delete": lambda c, h, u: c.delete(f"/api/admin/users/{u}", headers=h),
}


@pytest.mark.parametrize("action", list(ROUTES))
def test_hidden_actions_are_refused_by_the_server(client, su, action):
    """Whatever allowed_actions leaves out, the route refuses (UI is not the guard)."""
    me = client.get("/api/auth/me", headers=su).json()["id"]
    _, adm = make_user(client, su, "adm1", role="admin")
    tid, _ = make_user(client, su, "tch1")
    for headers, target in ((su, me), (adm, me), (adm, tid)):
        if action not in _row(client, headers, target)["allowed_actions"] and action != "reactivate":
            assert ROUTES[action](client, headers, target).status_code == 403, (action, target)
