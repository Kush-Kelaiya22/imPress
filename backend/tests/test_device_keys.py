"""#66: per-device keys. Devices register with the shared key and are issued
their own; once used, it is the only key that can act for that device."""

import hashlib

import pytest
from sqlalchemy import select
from starlette.websockets import WebSocketDisconnect

from conftest import DEVICE, DEVICE_KEY, auth, login, make_class

GW, OTHER = "48:F6:EE:00:00:01", "48:F6:EE:00:00:02"


def _register(client, mac=GW, headers=DEVICE, **extra):
    return client.post("/api/device/register", headers=headers,
                       json={"mac_address": mac, "device_type": "c6", **extra})


def _beat(client, key, mac=GW):
    return client.post("/api/device/heartbeat", headers={"X-API-Key": key}, json={"mac_address": mac})


def _key(client, mac=GW):
    r = _register(client, mac)
    assert r.status_code == 200, r.text
    return r.json()["device_key"]


def _device(db, mac=GW):
    from app.models import EspDevice

    async def q(s):
        return await s.scalar(select(EspDevice).where(EspDevice.mac_address == mac))
    return db(q)


@pytest.fixture
def h(client):
    return auth(login(client))


def test_registration_issues_a_key_and_stores_only_its_hash(client, db):
    key = _key(client)
    assert len(key) >= 40 and key != DEVICE_KEY
    d = _device(db)
    assert d.api_key_hash == hashlib.sha256(key.encode()).hexdigest() and key not in (d.api_key_hash or "")
    assert d.key_confirmed_at is None                     # issued, not active yet


def test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out(client):
    first = _key(client)
    second = _key(client)                                 # the device never saw the first response
    assert first != second
    assert _beat(client, first).status_code == 401        # replaced
    assert _beat(client, second).status_code == 200


def test_once_used_only_the_devices_own_key_acts_for_it(client):
    key = _key(client)
    assert _beat(client, key).status_code == 200          # first use activates it
    assert _beat(client, DEVICE_KEY).status_code == 403   # the shared key can no longer impersonate it
    r = _register(client)                                 # nor re-register it to get a fresh key
    assert r.status_code == 403 and "its own key" in r.json()["detail"]
    again = _register(client, headers={"X-API-Key": key})  # the device itself re-registers normally
    assert again.status_code == 200 and "device_key" not in again.json()


def test_a_device_key_works_only_for_its_own_mac(client):
    key = _key(client)
    _register(client, OTHER)
    r = _beat(client, key, OTHER)
    assert r.status_code == 403 and "another device" in r.json()["detail"]


def test_unknown_keys_are_refused(client):
    _register(client)
    assert _beat(client, "not-a-key").status_code == 401


def test_reset_kills_the_old_key_and_the_device_re_enrols(client, h):
    key = _key(client)
    _beat(client, key)
    dev_id = _register(client, headers={"X-API-Key": key}).json()["device_id"]
    r = client.post(f"/api/admin/modules/{dev_id}/reset-key", headers=h)
    assert r.status_code == 200 and r.json()["key_state"] == "shared"
    assert _beat(client, key).status_code == 401          # the firmware drops the key and re-registers
    fresh = _key(client)
    assert _beat(client, fresh).status_code == 200


def test_disabling_a_device_refuses_it_whatever_the_key_and_spares_the_others(client, h):
    key = _key(client)
    _beat(client, key)
    other = _key(client, OTHER)
    dev_id = _register(client, headers={"X-API-Key": key}).json()["device_id"]
    client.post(f"/api/admin/modules/{dev_id}/access", headers=h, json={"is_active": False})
    assert _beat(client, key).status_code == 403
    assert _beat(client, DEVICE_KEY).status_code == 403
    assert _beat(client, other, OTHER).status_code == 200


def test_key_state_is_shown_to_admins(client, h):
    key = _key(client)
    states = lambda: {m["mac_address"]: m["key_state"] for m in client.get("/api/admin/modules", headers=h).json()}
    assert states() == {GW: "issued"}
    _beat(client, key)
    assert states() == {GW: "active"}


def test_batch_messages_for_a_claimed_gateway_need_its_key(client, h):
    cid = make_class(client, h, classroom_code="RM-1")
    key = _key(client, GW)
    _register(client, headers={"X-API-Key": key}, classroom_code="RM-1")
    qid = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
    client.post(f"/api/quizzes/{qid}/start", headers=h)
    client.post("/api/students/", headers=h, json={"roll_number": "ABCDE12345", "student_name": "A"})
    join = {"type": "student_join", "device_mac": GW, "device_id": 7, "enrollment_number": "ABCDE12345"}
    ans = {"type": "quiz_answer", "quiz_id": qid, "question_order": 0, "enrollment_number": "ABCDE12345",
           "selected_option": 1}
    forged = client.post("/api/device/batch", headers=DEVICE, json={"messages": [join]}).json()
    assert forged["skipped"] == 1                          # shared key, claimed gateway
    real = client.post("/api/device/batch", headers={"X-API-Key": key}, json={"messages": [join, ans]}).json()
    assert (real["processed"], real["skipped"]) == (2, 0)  # the answer carries no device_mac: it is the caller's


def test_required_mode_accepts_the_shared_key_for_registration_only(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "DEVICE_KEYS_REQUIRED", True)
    key = _key(client)                                     # registering still works
    assert _beat(client, DEVICE_KEY).status_code == 403
    assert _beat(client, key).status_code == 200


def test_websocket_accepts_device_keys_and_refuses_reset_ones(client, h, monkeypatch):
    key = _key(client)
    with client.websocket_connect("/ws/class/1?role=device", headers={"X-API-Key": key}) as ws:
        assert ws.receive_json()["event"] == "connected"
    dev_id = _register(client, headers={"X-API-Key": key}).json()["device_id"]
    client.post(f"/api/admin/modules/{dev_id}/reset-key", headers=h)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/class/1?role=device", headers={"X-API-Key": key}) as ws:
            ws.receive_json()
    from app.config import settings
    monkeypatch.setattr(settings, "DEVICE_KEYS_REQUIRED", True)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/class/1?role=device", headers={"X-API-Key": DEVICE_KEY}) as ws:
            ws.receive_json()


def test_direct_votes_only_for_the_callers_own_device(client, h):
    cid = make_class(client, h)
    mine, theirs = _key(client), _key(client, OTHER)
    _beat(client, mine), _beat(client, theirs, OTHER)
    their_id = _register(client, OTHER, headers={"X-API-Key": theirs}).json()["device_id"]
    pid = client.post("/api/polls/", headers=h, json={"class_session_id": cid, "title": "P",
                                                      "options": ["a", "b"], "poll_mode": "planned"}).json()["id"]
    client.post(f"/api/polls/{pid}/start", headers=h)
    r = client.post(f"/api/polls/{pid}/vote", headers={"X-API-Key": mine},
                    json={"device_id": their_id, "selected_option": 0})
    assert r.status_code == 403
