"""Gateway-facing device API (routers/device.py) + presence service (services/presence.py).

These are the endpoints the C6 firmware calls; their request/response shapes
are part of the firmware contract (see firmware/class_c6/main/wifi_client.c).
"""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from conftest import DEVICE, auth, login, make_class, make_student

GW = "48:F6:EE:FF:FE:C7"


def _register(client, mac=GW, device_type="c6", **extra):
    r = client.post("/api/device/register", headers=DEVICE,
                    json={"mac_address": mac, "device_type": device_type, "device_name": "gw", **extra})
    assert r.status_code == 200, r.text
    return r.json()


def _device(db, mac=GW):
    from app.models import EspDevice

    async def q(s):
        return (await s.execute(select(EspDevice).where(EspDevice.mac_address == mac))).scalar_one()
    return db(q)


def _activity(db, action):
    from app.models import ActivityLog

    async def q(s):
        return (await s.execute(select(ActivityLog).where(ActivityLog.action == action))).scalars().all()
    return db(q)


@pytest.fixture
def su(client):
    return auth(login(client))


# ── Register ────────────────────────────────────────────────────────────────

def test_register_creates_then_updates_same_device(client, db):
    first = _register(client)
    again = _register(client, device_name="renamed")
    assert first["device_id"] == again["device_id"] and first["status"] == "registered"
    assert _device(db).device_name == "renamed"


def test_register_without_active_class_links_nothing(client, su):
    make_class(client, su)                       # inactive
    assert _register(client)["class_id"] is None


def test_register_auto_links_first_active_class_and_keeps_it(client, su):
    make_class(client, su, "A", "AAA1", activate=True)
    second = make_class(client, su, "B", "BBB1", activate=True)
    first_id = _register(client)["class_id"]
    assert first_id is not None and first_id != second
    assert _register(client)["class_id"] == first_id   # re-register keeps linkage


def test_register_links_by_classroom_code(client, su):
    make_class(client, su, "A", "AAA1", activate=True)
    target = make_class(client, su, "B", "BBB1", classroom_code="RM-201")
    assert _register(client, classroom_code="RM-201")["class_id"] == target


def test_register_marks_online_and_logs_once(client, db):
    _register(client)
    _register(client)
    assert _device(db).is_connected is True
    assert len(_activity(db, "esp_device.online")) == 1


# ── Heartbeat / ping ────────────────────────────────────────────────────────

def test_heartbeat_requires_registration(client):
    r = client.post("/api/device/heartbeat", headers=DEVICE, json={"mac_address": "00:00:00:00:00:01"})
    assert r.status_code == 404


def test_heartbeat_updates_telemetry(client, db):
    _register(client)
    r = client.post("/api/device/heartbeat", headers=DEVICE, json={
        "mac_address": GW, "battery_pct": 87, "rssi": -61, "firmware_version": "1.0.1",
        "student_count": 12, "free_heap": 180000, "total_flash": 8388608})
    assert r.status_code == 200 and "server_time" in r.json()
    d = _device(db)
    assert (d.battery_pct, d.rssi, d.firmware_version, d.student_count, d.free_heap) == (87, -61, "1.0.1", 12, 180000)


def test_status_ping_records_class_status_update(client, db, su):
    cid = make_class(client, su, activate=True)
    _register(client)
    r = client.post("/api/device/ping", headers=DEVICE, json={
        "mac_address": GW, "class_id": cid, "student_count": 9, "uptime_s": 3600, "rssi": -55, "free_heap": 1})
    assert r.status_code == 200
    rows = _activity(db, "class.status_update")
    assert len(rows) == 1 and rows[0].entity_id == cid and rows[0].details["student_count"] == 9


# ── Attendance ──────────────────────────────────────────────────────────────

def test_attendance_paths(client, db, su):
    cid = make_class(client, su, "Bio", "BIO1")
    sid = make_student(client, su, roll="ABCDE12345")
    body = {"enrollment_number": "abcde12345", "class_code": "BIO1"}
    assert client.post("/api/device/attendance", headers=DEVICE,
                       json={**body, "class_code": "NOPE"}).status_code == 404
    assert client.post("/api/device/attendance", headers=DEVICE, json=body).status_code == 400   # inactive class
    client.post(f"/api/classes/{cid}/activate", headers=su)
    assert client.post("/api/device/attendance", headers=DEVICE,
                       json={**body, "enrollment_number": "ZZZZZ99999"}).status_code == 404
    assert client.post("/api/device/attendance", headers=DEVICE, json=body).status_code == 400   # not enrolled
    client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": sid})
    ok = client.post("/api/device/attendance", headers=DEVICE, json=body)
    assert ok.status_code == 200 and ok.json() == {"status": "checked_in", "class_name": "Bio"}
    assert client.post("/api/device/attendance", headers=DEVICE, json=body).status_code == 200  # idempotent upsert
    from app.models import Attendance

    async def count(s):
        return len((await s.execute(select(Attendance))).scalars().all())
    assert db(count) == 1


# ── Firmware check / applied ────────────────────────────────────────────────

def test_firmware_check_and_applied_cycle(client, db):
    from app.models import EspDevice
    _register(client, device_type="s3")
    chk = client.post("/api/device/firmware/check", headers=DEVICE,
                      json={"mac_address": GW, "current_version": "1.0.0"}).json()
    assert chk["update_available"] is False and chk["version"] == ""

    async def push(s):
        await s.execute(update(EspDevice).values(pending_version="1.1.0"))
    db(push)
    chk = client.post("/api/device/firmware/check", headers=DEVICE,
                      json={"mac_address": GW, "current_version": "1.0.0"}).json()
    assert chk["update_available"] is True and chk["version"] == "1.1.0"
    done = client.post("/api/device/firmware/applied", headers=DEVICE, json={"mac_address": GW, "version": "1.1.0"})
    assert done.json()["firmware_version"] == "1.1.0"
    d = _device(db)
    assert (d.pending_version, d.ota_status) == ("", "applied")
    chk = client.post("/api/device/firmware/check", headers=DEVICE,
                      json={"mac_address": GW, "current_version": "1.1.0"}).json()
    assert chk["update_available"] is False


# ── Presence service ────────────────────────────────────────────────────────

def test_offline_sweep_marks_stale_devices_and_logs(client, db):
    from app.models import EspDevice
    from app.services.presence import _sweep_once
    from app.timeutil import istnow
    _register(client)
    _register(client, mac="AA:AA:AA:AA:AA:02")

    async def stale(s):
        await s.execute(update(EspDevice).where(EspDevice.mac_address == GW)
                        .values(last_seen=istnow() - timedelta(seconds=120)))
    db(stale)
    assert client.portal.call(_sweep_once) == 1
    assert _device(db).is_connected is False
    assert _device(db, "AA:AA:AA:AA:AA:02").is_connected is True
    assert len(_activity(db, "esp_device.offline")) == 1
    assert client.portal.call(_sweep_once) == 0          # already offline: no duplicate log
    client.post("/api/device/heartbeat", headers=DEVICE, json={"mac_address": GW})
    assert len(_activity(db, "esp_device.online")) == 3  # 2 registrations + 1 recovery


def test_class_presence_snapshot_walks_gateway_tree(client, db, su):
    from app.models import EspDevice
    from app.services.presence import class_id_for_device
    cid = make_class(client, su, activate=True)
    gw = _register(client)["device_id"]
    hub = _register(client, mac="AA:AA:AA:AA:AA:53", device_type="s3")["device_id"]
    node = _register(client, mac="AA:AA:AA:AA:AA:99", device_type="student")["device_id"]

    async def wire(s):
        await s.execute(update(EspDevice).where(EspDevice.id == hub).values(gateway_id=gw))
        await s.execute(update(EspDevice).where(EspDevice.id == node).values(gateway_id=hub))
    db(wire)
    snap = client.get(f"/api/classes/{cid}/presence", headers=su).json()
    assert [d["id"] for d in snap["devices"]] == [gw, hub, node]
    assert snap["online_count"] == snap["total_count"] == 3

    async def resolve(s):
        n = (await s.execute(select(EspDevice).where(EspDevice.id == node))).scalar_one()
        return await class_id_for_device(s, n)
    assert db(resolve) == cid


def test_registration_records_the_running_version(client, db):
    # it was accepted and silently dropped; deployments rely on it (#38)
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": GW, "device_type": "c6", "device_name": "gw", "firmware_version": "2.1.0"})
    assert r.status_code == 200
    assert _device(db).firmware_version == "2.1.0"
    client.post("/api/device/register", headers=DEVICE, json={"mac_address": GW, "device_type": "c6"})
    assert _device(db).firmware_version == "2.1.0"       # an older client that omits it changes nothing
