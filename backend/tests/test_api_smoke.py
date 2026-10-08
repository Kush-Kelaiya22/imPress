"""Smoke tests: the app boots on an empty DB and its basic contracts hold."""

from conftest import DEVICE, auth, login


def test_health(client):
    from pathlib import Path
    from app.migrations import LATEST
    version = (Path(__file__).resolve().parents[2] / "VERSION").read_text().strip()     # #42
    for path in ("/health", "/api/health"):
        assert client.get(path).json() == {"status": "healthy", "version": version, "schema_version": LATEST}
    assert client.get("/openapi.json").json()["info"]["version"] == version


def test_seeded_super_admin_can_log_in(client):
    me = client.get("/api/auth/me", headers=auth(login(client))).json()
    assert me["username"] == "admin" and me["role"] == "super_admin"


def test_bad_password_rejected(client):
    assert client.post("/api/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401


def test_protected_routes_need_a_session(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/admin/users").status_code == 401


def test_device_routes_need_the_device_key(client):
    body = {"mac_address": "AA:BB:CC:00:00:99", "device_type": "c6", "device_name": "gw"}
    assert client.post("/api/device/register", headers={"X-API-Key": "wrong"}, json=body).status_code == 401   # 401 since #66: the firmware drops a reset device key on 401
    r = client.post("/api/device/register", headers=DEVICE, json=body)
    assert r.status_code == 200 and r.json()["status"] == "registered"


def test_spa_served_for_unknown_paths(client):
    r = client.get("/some/client/route")
    assert r.status_code == 200 and "<html" in r.text.lower()
