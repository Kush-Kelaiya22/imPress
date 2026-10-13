"""Account changes that end access revoke every earlier session and socket (#118)."""

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import PASSWORD, auth, login, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


def _ok(client, h):
    return client.get("/api/auth/me", headers=h).status_code == 200


def test_reactivation_does_not_revive_old_tokens(client, su):
    uid, teacher = make_user(client, su, "tch1")
    assert client.post(f"/api/admin/users/{uid}/deactivate", headers=su).status_code == 200
    assert client.put(f"/api/admin/users/{uid}", headers=su, json={"is_active": True}).status_code == 200
    assert not _ok(client, teacher)
    assert _ok(client, auth(login(client, "tch1", PASSWORD)))           # a fresh login works


def test_deactivation_through_put_revokes_too(client, su):
    uid, teacher = make_user(client, su, "tch1")
    client.put(f"/api/admin/users/{uid}", headers=su, json={"is_active": False})
    client.put(f"/api/admin/users/{uid}", headers=su, json={"is_active": True})
    assert not _ok(client, teacher)


def test_admin_password_reset_logs_the_user_out(client, su):
    uid, teacher = make_user(client, su, "tch1")
    assert client.post(f"/api/admin/users/{uid}/reset-password", headers=su,
                       json={"new_password": "Reset-123x"}).status_code == 200
    assert not _ok(client, teacher)
    assert _ok(client, su)                                               # the admin is unaffected


def test_own_password_change_keeps_only_the_current_session(client, su):
    uid, first = make_user(client, su, "tch1")
    second = auth(login(client, "tch1", PASSWORD))
    r = client.post("/api/auth/change-password", headers=second,
                    json={"current_password": PASSWORD, "new_password": "Changed-123x"})
    assert r.status_code == 200
    assert _ok(client, second) and not _ok(client, first)


def test_role_change_revokes_sessions(client, su):
    uid, admin = make_user(client, su, "adm1", role="admin")
    assert client.put(f"/api/admin/users/{uid}", headers=su, json={"role": "teacher"}).status_code == 200
    assert not _ok(client, admin)
    me = client.get("/api/auth/me", headers=auth(login(client, "adm1", PASSWORD))).json()
    assert me["role"] == "teacher"


def test_profile_edit_does_not_revoke(client, su):
    uid, teacher = make_user(client, su, "tch1")
    client.put(f"/api/admin/users/{uid}", headers=su, json={"full_name": "New Name"})
    assert _ok(client, teacher)


def test_open_teacher_socket_is_closed_on_deactivation(client, su):
    uid, teacher = make_user(client, su, "tch1")
    token = teacher["Authorization"].split()[1]
    with client.websocket_connect(f"/ws/class/1?role=teacher&token={token}") as ws:
        assert ws.receive_json()["event"] == "connected"
        assert client.post(f"/api/admin/users/{uid}/deactivate", headers=su).status_code == 200
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
        assert e.value.code == 4401
