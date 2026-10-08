"""#40: the student module inventory. Modules seen on a gateway's mesh are
listed per class, one row per module, without location history."""

from datetime import timedelta

import pytest
from sqlalchemy import func, select, update

from conftest import DEVICE, auth, login, make_class, make_student, make_user

GW = "48:F6:EE:00:00:C6"
UID = 0x1A2B3C4D                   # firmware device_id: last 4 bytes of the module's MAC
ROLL = "ABCDE12345"


@pytest.fixture
def setup(client):
    """Smoke steps 1-5: a class whose gateway registered with its room code."""
    h = auth(login(client))
    cid = make_class(client, h, classroom_code="RM-201")
    make_student(client, h, roll=ROLL)
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": GW, "device_type": "c6", "device_name": "room 201", "classroom_code": "RM-201"})
    assert r.json()["class_id"] == cid
    return h, cid


def _batch(client, *messages, gw=GW):
    r = client.post("/api/device/batch", headers=DEVICE, json={
        "device_type": "c6", "messages": [{"device_mac": gw, **m} for m in messages]})
    assert r.status_code == 200, r.text
    return r.json()


def join(uid=UID, roll=ROLL):
    return {"type": "student_join", "enrollment_number": roll, "device_id": uid, "class_code": ""}


def leave(uid=UID, roll=ROLL):
    return {"type": "student_leave", "enrollment_number": roll, "device_id": uid, "reason": 0}


def beat(uid=UID, battery=80, rssi=-60):
    return {"type": "heartbeat", "device_id": uid, "battery_pct": battery, "rssi": rssi}


def _rows(db):
    from app.models import StudentModule

    async def q(s):
        return await s.scalar(select(func.count()).select_from(StudentModule))
    return db(q)


def _age(db, seconds):
    from app.models import StudentModule
    from app.timeutil import istnow

    async def q(s):
        await s.execute(update(StudentModule).values(last_seen=istnow() - timedelta(seconds=seconds)))
    db(q)


def _modules(client, h, **params):
    r = client.get("/api/admin/student-modules", headers=h, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_smoke_step_7_the_joined_module_is_listed(client, setup):
    h, cid = setup
    _batch(client, join())
    view = client.get(f"/api/admin/classes/{cid}/devices", headers=h).json()
    assert view["node"]["mac_address"] == GW
    [m] = view["student_modules"]                  # was: 0 student devices
    assert (m["device_uid"], m["enrollment_number"], m["state"], m["gateway_name"], m["class_id"]) == \
        ("1A2B3C4D", ROLL, "connected", "room 201", cid)
    # the live presence snapshot (teachers, WS push) carries it too
    assert [x["device_uid"] for x in client.get(f"/api/classes/{cid}/presence", headers=h).json()
            ["student_modules"]] == ["1A2B3C4D"]


def test_reconnects_and_heartbeats_update_one_row(client, db, setup):
    h, _ = setup
    _batch(client, join(), beat(), leave(), join(), beat(battery=55, rssi=-71))
    assert _rows(db) == 1
    [m] = _modules(client, h)
    assert (m["state"], m["battery_pct"], m["rssi"]) == ("connected", 55, -71)


def test_a_relayed_heartbeat_does_not_overwrite_the_gateways_telemetry(client, db, setup):
    from app.models import EspDevice
    client.post("/api/device/heartbeat", headers=DEVICE, json={"mac_address": GW, "battery_pct": 100, "rssi": -40})
    _batch(client, beat(battery=12, rssi=-88), beat(uid=0, battery=100, rssi=0))   # a student, then the S3

    async def gw(s):
        return await s.scalar(select(EspDevice).where(EspDevice.mac_address == GW))
    g = db(gw)
    assert (g.battery_pct, g.rssi, g.is_connected) == (100, -40, True)
    assert _rows(db) == 1                         # the S3's own heartbeat (device_id 0) is no module


def test_leave_marks_the_module_seen_previously(client, setup):
    h, _ = setup
    _batch(client, join(), leave())
    assert [m["state"] for m in _modules(client, h)] == ["seen"]


def test_sweep_uses_the_modules_heartbeat_interval(client, db, setup):
    from app.services.presence import _sweep_once
    h, _ = setup
    _batch(client, join())
    states = []
    for age in (45, 95):                          # one missed 30 s beat is not offline; three are
        _age(db, age)
        client.portal.call(_sweep_once)
        states.append(_modules(client, h)[0]["state"])
    assert states == ["connected", "seen"]


def test_older_firmware_without_device_id_is_keyed_by_enrollment(client, db, setup):
    h, _ = setup
    legacy = {"type": "student_join", "enrollment_number": ROLL}
    _batch(client, legacy, legacy, {"type": "student_leave", "enrollment_number": ROLL})
    assert _rows(db) == 1
    [m] = _modules(client, h)
    assert (m["device_uid"], m["enrollment_number"], m["state"]) == ("", ROLL, "seen")


def test_a_module_that_moves_keeps_its_row(client, db, setup):
    h, cid = setup
    other = make_class(client, h, "Chem", "CHM101", classroom_code="RM-305")
    client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:C7", "device_type": "c6", "classroom_code": "RM-305"})
    _batch(client, join())
    _batch(client, join(), gw="48:F6:EE:00:00:C7")
    assert _rows(db) == 1
    assert [m["class_id"] for m in _modules(client, h)] == [other]
    assert client.get(f"/api/classes/{cid}/presence", headers=h).json()["student_modules"] == []


def test_filters(client, setup):
    h, cid = setup
    make_student(client, h, roll="ZZZZZ99999", name="B")
    _batch(client, join(), join(uid=0x0000BEEF, roll="ZZZZZ99999"), leave(uid=0x0000BEEF, roll="ZZZZZ99999"))
    assert [m["device_uid"] for m in _modules(client, h, state="connected")] == ["1A2B3C4D"]
    assert [m["device_uid"] for m in _modules(client, h, state="seen")] == ["0000BEEF"]
    assert [m["enrollment_number"] for m in _modules(client, h, q="beef")] == ["ZZZZZ99999"]
    assert [m["device_uid"] for m in _modules(client, h, q="abcde")] == ["1A2B3C4D"]
    assert len(_modules(client, h, class_id=cid)) == 2 and _modules(client, h, class_id=cid + 99) == []
    assert client.get("/api/admin/student-modules", headers=h, params={"state": "gone"}).status_code == 422


def test_access_is_scoped(client, setup):
    h, cid = setup
    _batch(client, join())
    _, teacher = make_user(client, h, "teach1")
    assert client.get("/api/admin/student-modules", headers=teacher).status_code == 403
    assert client.get(f"/api/classes/{cid}/presence", headers=teacher).status_code == 403   # not their class
    assert client.get("/api/admin/student-modules").status_code == 401


def test_deletes_unlink_but_keep_the_module(client, db, setup):
    h, cid = setup
    sid = client.get("/api/students/", headers=h).json()
    sid = (sid["items"] if isinstance(sid, dict) else sid)[0]["id"]
    _batch(client, join())
    assert client.delete(f"/api/students/{sid}/hard-delete", headers=h).status_code == 200
    [m] = _modules(client, h)
    assert m["enrollment_number"] == ""             # erased student no longer tied to the module
    assert client.delete(f"/api/admin/classes/{cid}", headers=h).status_code == 200
    [m] = _modules(client, h)
    assert m["class_id"] is None and _rows(db) == 1
