"""Admin user management (routers/admin.py /api/admin/users*)."""

import pytest

from conftest import PASSWORD, auth, login, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


def test_create_user_validates_uniqueness(client, su):
    make_user(client, su, "ravi")
    dup_name = client.post("/api/admin/users", headers=su, json={
        "username": "ravi", "email": "other@x.io", "password": PASSWORD, "role": "teacher"})
    dup_mail = client.post("/api/admin/users", headers=su, json={
        "username": "ravi2", "email": "ravi@example.edu", "password": PASSWORD, "role": "teacher"})
    assert dup_name.status_code == 400 and dup_mail.status_code == 400


@pytest.mark.parametrize("field,value", [("username", "ab"), ("password", "12345")])
def test_create_user_field_limits(client, su, field, value):
    body = {"username": "valid", "email": "v@x.io", "password": PASSWORD, "role": "teacher", field: value}
    assert client.post("/api/admin/users", headers=su, json=body).status_code == 422


def test_list_users_filters_by_role(client, su):
    make_user(client, su, "tch1")
    make_user(client, su, "adm1", role="admin")
    teachers = client.get("/api/admin/users", headers=su, params={"role": "teacher"}).json()
    assert {u["username"] for u in teachers} == {"tch1"}
    assert len(client.get("/api/admin/users", headers=su).json()) == 3


def test_teacher_cannot_use_admin_user_routes(client, su):
    _, teacher = make_user(client, su, "tch1")
    assert client.get("/api/admin/users", headers=teacher).status_code == 403
    assert client.post("/api/admin/users", headers=teacher, json={
        "username": "x" * 5, "email": "x@x.io", "password": PASSWORD}).status_code == 403


def test_deactivate_rules(client, su):
    me = client.get("/api/auth/me", headers=su).json()["id"]
    assert client.post(f"/api/admin/users/{me}/deactivate", headers=su).status_code == 400   # not yourself
    _, admin = make_user(client, su, "adm", role="admin")
    assert client.post(f"/api/admin/users/{me}/deactivate", headers=admin).status_code == 403  # not the super admin
    assert client.post("/api/admin/users/999/deactivate", headers=su).status_code == 404


def test_deactivated_user_loses_access_immediately(client, su):
    uid, teacher = make_user(client, su, "tch1")
    assert client.get("/api/auth/me", headers=teacher).status_code == 200
    client.post(f"/api/admin/users/{uid}/deactivate", headers=su)
    assert client.get("/api/auth/me", headers=teacher).status_code == 401


def test_admin_password_reset(client, su):
    uid, _ = make_user(client, su, "tch1")
    assert client.post(f"/api/admin/users/{uid}/reset-password", headers=su,
                       json={"new_password": "Reset-123"}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "tch1", "password": PASSWORD}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "tch1", "password": "Reset-123"}).status_code == 200


def test_admin_cannot_reset_super_admin_password(client, su):
    me = client.get("/api/auth/me", headers=su).json()["id"]
    _, admin = make_user(client, su, "adm", role="admin")
    r = client.post(f"/api/admin/users/{me}/reset-password", headers=admin, json={"new_password": "Hijack-123"})
    assert r.status_code == 403


def test_delete_is_soft_and_guarded(client, su):
    uid, _ = make_user(client, su, "tch1")
    me = client.get("/api/auth/me", headers=su).json()["id"]
    assert client.delete(f"/api/admin/users/{me}", headers=su).status_code == 400
    assert client.delete(f"/api/admin/users/{uid}", headers=su).status_code == 200
    assert client.post("/api/auth/login", json={"username": "tch1", "password": PASSWORD}).status_code == 403


# ── CSV import ──────────────────────────────────────────────────────────────

HEADER = "username,email,password,full_name,role\n"


def _import(client, h, body, name="users.csv"):
    return client.post("/api/admin/users/import", headers=h,
                       files={"file": (name, (HEADER + body).encode(), "text/csv")})


def test_csv_import_inserts_valid_rows_and_reports_bad_ones(client, su):
    r = _import(client, su,
                "alice,alice@x.io,Passw0rd!,Alice A,teacher\n"
                "bob,bob@x.io,short,Bob B,teacher\n"          # password too short
                "carl,carl@x.io,Passw0rd!,Carl C,wizard\n"    # bad role
                "alice,dup@x.io,Passw0rd!,Alice 2,teacher\n")  # duplicate username
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["inserted"] == 1 and len(res["skipped"]) == 3
    assert client.post("/api/auth/login", json={"username": "alice", "password": "Passw0rd!"}).status_code == 200


def test_csv_import_admin_rows_need_super_admin(client, su):
    _, admin = make_user(client, su, "adm", role="admin")
    res = _import(client, admin, "boss,boss@x.io,Passw0rd!,Boss,admin\n").json()
    assert res["inserted"] == 0 and "super admin" in res["skipped"][0]["error"]
