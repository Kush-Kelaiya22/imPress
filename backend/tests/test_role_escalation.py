"""#10: only a super admin can grant/remove admin-level roles; roles are a closed set."""

import pytest

from conftest import auth, login


def _create(client, h, username, role):
    return client.post("/api/admin/users", headers=h, json={
        "username": username, "email": f"{username}@x.io", "password": "Passw0rd!x",
        "full_name": username, "role": role})


@pytest.fixture
def accounts(client):
    su = auth(login(client))
    ids = {}
    for name, role in (("adm", "admin"), ("adm2", "admin"), ("tch", "teacher")):
        r = _create(client, su, name, role)
        assert r.status_code == 201, r.text
        ids[name] = r.json()["id"]
    return {"su": su, "adm": auth(login(client, "adm", "Passw0rd!x")), "ids": ids}


def test_admin_cannot_promote_self_to_super_admin(client, accounts):
    r = client.put(f"/api/admin/users/{accounts['ids']['adm']}", headers=accounts["adm"], json={"role": "super_admin"})
    assert r.status_code == 403


def test_admin_cannot_promote_teacher_to_admin_or_super_admin(client, accounts):
    for role in ("admin", "super_admin"):
        r = client.put(f"/api/admin/users/{accounts['ids']['tch']}", headers=accounts["adm"], json={"role": role})
        assert r.status_code == 403, role


def test_admin_cannot_demote_another_admin(client, accounts):
    r = client.put(f"/api/admin/users/{accounts['ids']['adm2']}", headers=accounts["adm"], json={"role": "teacher"})
    assert r.status_code == 403


def test_admin_cannot_create_super_admin(client, accounts):
    assert _create(client, accounts["adm"], "evil", "super_admin").status_code == 403
    assert _create(client, accounts["adm"], "evil2", "admin").status_code == 403


@pytest.mark.parametrize("role", ["root", "SUPER_ADMIN", "", "student"])
def test_unknown_roles_rejected(client, accounts, role):
    r = client.put(f"/api/admin/users/{accounts['ids']['tch']}", headers=accounts["su"], json={"role": role})
    assert r.status_code == 422
    assert _create(client, accounts["su"], "x" + str(abs(hash(role)))[:6], role).status_code == 422


def test_super_admin_can_grant_and_revoke(client, accounts):
    tid = accounts["ids"]["tch"]
    assert client.put(f"/api/admin/users/{tid}", headers=accounts["su"], json={"role": "admin"}).json()["role"] == "admin"
    assert client.put(f"/api/admin/users/{tid}", headers=accounts["su"], json={"role": "teacher"}).json()["role"] == "teacher"


def test_nobody_changes_own_role(client, accounts):
    me = client.get("/api/auth/me", headers=accounts["su"]).json()["id"]
    assert client.put(f"/api/admin/users/{me}", headers=accounts["su"], json={"role": "teacher"}).status_code == 403


def test_admin_still_manages_teachers(client, accounts):
    tid = accounts["ids"]["tch"]
    r = client.put(f"/api/admin/users/{tid}", headers=accounts["adm"], json={"full_name": "Renamed", "role": "teacher"})
    assert r.status_code == 200 and r.json()["full_name"] == "Renamed"
    assert _create(client, accounts["adm"], "tch2", "teacher").status_code == 201
