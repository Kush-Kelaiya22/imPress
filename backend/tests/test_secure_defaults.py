"""#11: no working public credentials or debug leaks by default."""

import asyncio
import logging
import re

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from conftest import DEVICE_KEY, _reset_db


def _fresh_settings(monkeypatch, **env):
    from app.config import Settings
    for k in list(__import__("os").environ):
        if k.startswith("IMPRESS_"):
            monkeypatch.delenv(k)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return Settings(_env_file=None)


def test_debug_and_sql_echo_off_by_default(monkeypatch):
    s = _fresh_settings(monkeypatch)
    assert s.DEBUG is False and s.SQL_ECHO is False
    from app.database import engine
    assert engine.echo is False


def test_refuses_default_secrets_outside_debug(monkeypatch):
    from app.config import check_secure
    with pytest.raises(RuntimeError, match="IMPRESS_JWT_SECRET.*IMPRESS_DEVICE_API_KEY"):
        check_secure(_fresh_settings(monkeypatch))
    with pytest.raises(RuntimeError, match="IMPRESS_DEVICE_API_KEY"):
        check_secure(_fresh_settings(monkeypatch, IMPRESS_JWT_SECRET="x" * 32))
    check_secure(_fresh_settings(monkeypatch, IMPRESS_JWT_SECRET="x" * 32, IMPRESS_DEVICE_API_KEY="y" * 32))
    check_secure(_fresh_settings(monkeypatch, IMPRESS_DEBUG="true"))   # local dev still works


def test_app_startup_fails_with_default_secrets(monkeypatch):
    from app.config import DEFAULT_DEVICE_API_KEY, DEFAULT_JWT_SECRET, settings
    from app.main import app
    monkeypatch.setattr(settings, "JWT_SECRET", DEFAULT_JWT_SECRET)
    monkeypatch.setattr(settings, "DEVICE_API_KEY", DEFAULT_DEVICE_API_KEY)
    with pytest.raises(RuntimeError, match="default secrets"):
        with TestClient(app):
            pass


def test_first_admin_password_is_random_not_admin123(monkeypatch, caplog):
    from app.config import settings
    from app.main import app
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "")
    asyncio.run(_reset_db())
    with caplog.at_level(logging.WARNING, logger="app.main"), TestClient(app) as c:
        assert c.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 401
        m = re.search(r"username=admin password=(\S+)", caplog.text)
        assert m, caplog.text
        assert len(m.group(1)) >= 16
        assert c.post("/api/auth/login", json={"username": "admin", "password": m.group(1)}).status_code == 200


def test_cors_only_configured_origins(client):
    def preflight(origin):
        return client.options("/api/auth/login", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST"})
    assert preflight("http://localhost:5173").headers.get("access-control-allow-origin") == "http://localhost:5173"
    evil = preflight("https://evil.example")
    assert evil.headers.get("access-control-allow-origin") is None


def test_device_ws_accepts_key_header_and_legacy_query(client):
    with client.websocket_connect("/ws/class/1?role=device", headers={"X-API-Key": DEVICE_KEY}) as ws:
        assert ws.receive_json()["role"] == "device"
    with client.websocket_connect(f"/ws/class/1?role=device&api_key={DEVICE_KEY}") as ws:
        assert ws.receive_json()["role"] == "device"
    for kw in ({"headers": {"X-API-Key": "nope"}}, {}):
        with pytest.raises(WebSocketDisconnect) as e:
            with client.websocket_connect("/ws/class/1?role=device", **kw) as ws:
                ws.receive_json()
        assert e.value.code == 4401


def test_device_http_key_checked(client):
    body = {"mac_address": "AA:BB:CC:00:00:01", "device_type": "c6", "device_name": "x"}
    assert client.post("/api/device/register", headers={"X-API-Key": "impress-device-key-2024"}, json=body).status_code == 403
    assert client.post("/api/device/register", headers={"X-API-Key": DEVICE_KEY}, json=body).status_code == 200
