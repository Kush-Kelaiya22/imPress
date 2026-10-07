"""#8: teacher WebSocket auth uses the login session token; roles are recorded."""

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import DEVICE_KEY, auth, login


def _rejected(client, url):
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(url) as ws:
            ws.receive_json()
    return e.value.code


def test_teacher_with_login_token_connects(client):
    tok = login(client)
    with client.websocket_connect(f"/ws/class/1?role=teacher&token={tok}") as ws:
        hello = ws.receive_json()
    assert hello["event"] == "connected" and hello["role"] == "teacher"


@pytest.mark.parametrize("token", ["", "garbage", "impress_" + "x" * 64])
def test_teacher_with_bad_token_rejected(client, token):
    assert _rejected(client, f"/ws/class/1?role=teacher&token={token}") == 4401


def test_teacher_after_logout_rejected(client):
    tok = login(client)
    assert client.post("/api/auth/logout", headers=auth(tok)).status_code == 200
    assert _rejected(client, f"/ws/class/1?role=teacher&token={tok}") == 4401


def test_teacher_with_idle_expired_session_rejected(client, db):
    from datetime import timedelta
    from sqlalchemy import update
    from app.models import UserSession
    from app.timeutil import istnow
    tok = login(client)

    async def age(s):
        await s.execute(update(UserSession).values(last_activity_at=istnow() - timedelta(days=1)))
    db(age)
    assert _rejected(client, f"/ws/class/1?role=teacher&token={tok}") == 4401


def test_inactive_user_rejected(client, db):
    from sqlalchemy import update
    from app.models import User
    tok = login(client)

    async def deactivate(s):
        await s.execute(update(User).values(is_active=False))
    db(deactivate)
    assert _rejected(client, f"/ws/class/1?role=teacher&token={tok}") == 4401


def test_device_key_still_required(client):
    assert _rejected(client, "/ws/class/1?role=device&api_key=wrong") == 4401
    with client.websocket_connect(f"/ws/class/1?role=device&api_key={DEVICE_KEY}") as ws:
        assert ws.receive_json()["role"] == "device"


def test_roles_recorded_and_role_broadcast_targets_teachers(client):
    from app.ws.manager import manager
    tok = login(client)
    with client.websocket_connect(f"/ws/class/7?role=teacher&token={tok}") as teacher, \
         client.websocket_connect(f"/ws/class/7?role=device&api_key={DEVICE_KEY}") as device:
        teacher.receive_json(); device.receive_json()
        assert sorted(manager.connection_roles[7].values()) == ["device", "teacher"]

        client.portal.call(manager.broadcast_to_role, 7, {"event": "presence", "n": 1}, "teacher")
        client.portal.call(manager.broadcast_to_class, 7, {"event": "marker"})
        assert teacher.receive_json() == {"event": "presence", "n": 1}
        # The device's next frame is the class-wide marker: it never got the teacher-only push.
        assert device.receive_json() == {"event": "marker"}
        assert teacher.receive_json() == {"event": "marker"}
