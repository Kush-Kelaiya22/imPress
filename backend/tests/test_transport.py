"""HTTPS for staff traffic and browser security headers (#152)."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from conftest import DEVICE


@pytest.fixture
def strict(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "REQUIRE_HTTPS", None)        # the default: on unless DEBUG
    monkeypatch.setattr(settings, "DEBUG", False)
    return client


def _https(client):
    from app.main import app
    return TestClient(app, base_url="https://testserver")


def test_login_over_plain_http_is_refused_with_a_reason(strict):
    r = strict.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "HTTPS_REQUIRED"
    page = strict.get("/")
    assert page.status_code == 403 and "https://" in page.text


def test_https_works_and_gets_hsts(strict):
    c = _https(strict)
    r = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.headers["strict-transport-security"].startswith("max-age=")


def test_a_reverse_proxy_counts_as_https(strict):
    """uvicorn turns X-Forwarded-Proto from a trusted proxy into the scheme; the
    test client sets the scheme the same way."""
    c = _https(strict)
    assert c.get("/api/auth/me").status_code == 401                   # reached the auth layer


def test_exempt_routes(strict):
    assert strict.get("/health").status_code == 200
    r = strict.post("/api/device/register", headers=DEVICE, json={"mac_address": "48:F6:EE:00:00:01",
                                                                   "device_type": "c6"})
    assert r.status_code == 200                                         # devices: firmware TLS is optional (#66)


def test_devices_too_when_the_site_requires_it(strict, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "DEVICE_HTTPS_ONLY", True)
    r = strict.post("/api/device/register", headers=DEVICE, json={"mac_address": "48:F6:EE:00:00:01",
                                                                   "device_type": "c6"})
    assert r.status_code == 403


def test_loopback_is_exempt():
    from app.transport import is_loopback, needs_https
    assert is_loopback("127.0.0.1") and is_loopback("::1") and not is_loopback("192.168.137.12")
    assert not needs_https("/api/auth/login", "http", "127.0.0.1")


def test_teacher_socket_needs_wss(strict):
    with pytest.raises(WebSocketDisconnect) as e:
        with strict.websocket_connect("/ws/class/1?role=teacher&token=x") as ws:
            ws.receive_json()
    assert e.value.code == 4403


def test_security_headers(client):
    page = client.get("/")
    assert page.headers["x-frame-options"] == "DENY" and page.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    api = client.get("/api/auth/me")
    assert api.headers["cache-control"] == "no-store" and "strict-transport-security" not in api.headers
