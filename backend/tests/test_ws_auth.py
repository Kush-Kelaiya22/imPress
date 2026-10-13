"""#8: teacher WebSocket auth uses the login session token; roles are recorded.
#121: a socket joins only a class its identity may access."""

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import DEVICE, DEVICE_KEY, PASSWORD, auth, login, make_class, make_user


def _rejected(client, url, token=None):
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(url, headers=auth(token) if token is not None else {}) as ws:
            ws.receive_json()
    return e.value.code


def test_teacher_with_login_token_connects(client):
    tok = login(client)
    cid = make_class(client, auth(tok))
    with client.websocket_connect(f"/ws/class/{cid}?role=teacher", headers=auth(tok)) as ws:
        hello = ws.receive_json()
    assert hello["event"] == "connected" and hello["role"] == "teacher"


@pytest.mark.parametrize("token", ["", "garbage", "impress_" + "x" * 64])
def test_teacher_with_bad_token_rejected(client, token):
    assert _rejected(client, "/ws/class/1?role=teacher", token) == 4401


def test_teacher_after_logout_rejected(client):
    tok = login(client)
    assert client.post("/api/auth/logout", headers=auth(tok)).status_code == 200
    assert _rejected(client, "/ws/class/1?role=teacher", tok) == 4401


def test_teacher_with_idle_expired_session_rejected(client, db):
    from datetime import timedelta
    from sqlalchemy import update
    from app.models import UserSession
    from app.timeutil import istnow
    tok = login(client)

    async def age(s):
        await s.execute(update(UserSession).values(last_activity_at=istnow() - timedelta(days=1)))
    db(age)
    assert _rejected(client, "/ws/class/1?role=teacher", tok) == 4401


def test_inactive_user_rejected(client, db):
    from sqlalchemy import update
    from app.models import User
    uid, _ = make_user(client, auth(login(client)), "tch1")
    tok = login(client, "tch1", PASSWORD)

    async def deactivate(s):        # not the super admin: the last one can't be deactivated (#116)
        await s.execute(update(User).where(User.id == uid).values(is_active=False))
    db(deactivate)
    assert _rejected(client, "/ws/class/1?role=teacher", tok) == 4401


def test_device_key_still_required(client):
    assert _rejected(client, "/ws/class/1?role=device&api_key=wrong") == 4401
    with client.websocket_connect(f"/ws/class/1?role=device&api_key={DEVICE_KEY}") as ws:
        assert ws.receive_json()["role"] == "device"


def test_roles_recorded_and_role_broadcast_targets_teachers(client):
    from app.ws.manager import manager
    tok = login(client)
    c = make_class(client, auth(tok))
    with client.websocket_connect(f"/ws/class/{c}?role=teacher", headers=auth(tok)) as teacher, \
         client.websocket_connect(f"/ws/class/{c}?role=device&api_key={DEVICE_KEY}") as device:
        teacher.receive_json(); device.receive_json()
        assert sorted(manager.connection_roles[c].values()) == ["device", "teacher"]

        client.portal.call(manager.broadcast_to_role, c, {"event": "presence", "n": 1}, "teacher")
        client.portal.call(manager.broadcast_to_class, c, {"event": "marker"})
        assert teacher.receive_json() == {"event": "presence", "n": 1}
        # The device's next frame is the class-wide marker: it never got the teacher-only push.
        assert device.receive_json() == {"event": "marker"}
        assert teacher.receive_json() == {"event": "marker"}


# ── #121: class binding ─────────────────────────────────────────────────────

def test_teacher_cannot_join_another_teachers_class(client):
    su = auth(login(client))
    owner, _ = make_user(client, su, "owner")
    _, outsider = make_user(client, su, "outsider")
    cid = make_class(client, su, teacher_id=owner)
    token = outsider["Authorization"].split()[1]
    assert _rejected(client, f"/ws/class/{cid}?role=teacher", token) == 4403


def test_co_faculty_and_admin_may_join(client):
    su = auth(login(client))
    owner, _ = make_user(client, su, "owner")
    co, co_h = make_user(client, su, "cofac")
    cid = make_class(client, su, teacher_ids=[owner, co])
    for h in (co_h, su):
        with client.websocket_connect(f"/ws/class/{cid}?role=teacher", headers=h) as ws:
            assert ws.receive_json()["event"] == "connected"


def test_unknown_class_is_refused(client):
    assert _rejected(client, "/ws/class/999?role=teacher", login(client)) == 4404


def test_gateway_key_joins_only_its_own_class(client):
    su = auth(login(client))
    mine = make_class(client, su, name="Mine", code="MINE1", activate=True)
    r = client.post("/api/device/register", headers=DEVICE, json={"mac_address": "48:F6:EE:00:00:01",
                                                                  "device_type": "c6"})
    assert r.json()["class_id"] == mine
    key = {"X-API-Key": r.json()["device_key"]}
    other = make_class(client, su, name="Other", code="OTH1", activate=True)
    with client.websocket_connect(f"/ws/class/{mine}?role=device", headers=key) as ws:
        assert ws.receive_json()["event"] == "connected"
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/class/{other}?role=device", headers=key) as ws:
            ws.receive_json()
    assert e.value.code == 4403


def test_browser_cannot_relay_commands_to_devices(client):
    tok = login(client)
    cid = make_class(client, auth(tok))
    with client.websocket_connect(f"/ws/class/{cid}?role=teacher", headers=auth(tok)) as teacher, \
         client.websocket_connect(f"/ws/class/{cid}?role=device&api_key={DEVICE_KEY}") as device:
        teacher.receive_json(); device.receive_json()
        teacher.send_json({"event": "broadcast_command", "command": "quiz_question", "payload": {"q": 1}})
        teacher.send_json({"event": "device_data", "data": {"fake": True}})     # only devices send data
        teacher.send_json({"event": "ping"})
        assert teacher.receive_json() == {"event": "pong"}                      # nothing else arrived first
        from app.ws.manager import manager
        client.portal.call(manager.broadcast_to_class, cid, {"event": "marker"})
        assert device.receive_json() == {"event": "marker"}                     # no device_command before it


def test_unauthenticated_websockets_need_debug():
    from app.config import Settings, check_secure
    with pytest.raises(RuntimeError, match="WS_REQUIRE_AUTH"):
        check_secure(Settings(WS_REQUIRE_AUTH=False, DEBUG=False, JWT_SECRET="x" * 32, DEVICE_API_KEY="y" * 32))
    check_secure(Settings(WS_REQUIRE_AUTH=False, DEBUG=True))
