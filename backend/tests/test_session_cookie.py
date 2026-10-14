"""v2.2: the browser's session lives in an HttpOnly cookie, never in page
storage or a URL; cookie-authenticated changes need the app's CSRF header;
a cross-site page cannot open a teacher socket; logout revokes the session."""

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import make_class

CSRF = {"X-Impress-Request": "1"}


def _browser_login(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r


def test_login_sets_httponly_strict_cookie(client):
    cookie = _browser_login(client).headers["set-cookie"].lower()
    assert cookie.startswith("impress_session=")
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/" in cookie


def test_cookie_authenticates_reads(client):
    _browser_login(client)
    assert client.get("/api/auth/me").json()["username"] == "admin"


def test_cookie_change_without_csrf_header_refused(client):
    _browser_login(client)
    r = client.put("/api/auth/me", json={"full_name": "Changed"})
    assert r.status_code == 403 and "CSRF" in r.text
    assert client.get("/api/auth/me").json()["full_name"] != "Changed"


def test_cookie_change_with_csrf_header_allowed(client):
    _browser_login(client)
    assert client.put("/api/auth/me", json={"full_name": "Changed"}, headers=CSRF).status_code == 200


def test_bearer_clients_need_no_csrf_header(client):
    token = _browser_login(client).json()["access_token"]
    client.cookies.clear()
    r = client.put("/api/auth/me", json={"full_name": "Script"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_logout_revokes_session_and_clears_cookie(client):
    token = _browser_login(client).json()["access_token"]
    assert client.post("/api/auth/logout", headers=CSRF).status_code == 200
    assert client.get("/api/auth/me").status_code == 401                     # cookie cleared
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401  # revoked


def test_logout_without_csrf_header_refused(client):
    _browser_login(client)
    assert client.post("/api/auth/logout").status_code == 403
    assert client.get("/api/auth/me").status_code == 200


def test_teacher_socket_uses_cookie_not_url(client):
    _browser_login(client)
    cid = make_class(client, CSRF)
    with client.websocket_connect(f"/ws/class/{cid}?role=teacher") as ws:
        assert ws.receive_json()["event"] == "connected"


def test_url_token_is_ignored(client):
    token = _browser_login(client).json()["access_token"]
    client.cookies.clear()
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/class/1?role=teacher&token={token}") as ws:
            ws.receive_json()
    assert e.value.code == 4401


def test_cross_site_socket_refused(client):
    _browser_login(client)
    cid = make_class(client, CSRF)
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/class/{cid}?role=teacher",
                                      headers={"Origin": "https://evil.example"}) as ws:
            ws.receive_json()
    assert e.value.code == 4403


def test_same_origin_socket_allowed(client):
    _browser_login(client)
    cid = make_class(client, CSRF)
    with client.websocket_connect(f"/ws/class/{cid}?role=teacher",
                                  headers={"Origin": "http://testserver"}) as ws:
        assert ws.receive_json()["event"] == "connected"


def test_web_app_keeps_the_token_out_of_storage_and_urls():
    from pathlib import Path
    js = (Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "api.js").read_text()
    assert "localStorage.setItem('impress_token'" not in js and "getToken" not in js
    assert "token=" not in js and "Authorization" not in js
    assert "'X-Impress-Request': '1'" in js
