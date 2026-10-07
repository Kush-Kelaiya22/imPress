"""#17: registration must not steal a class's gateway link."""

from sqlalchemy import select

from conftest import DEVICE, auth, login


def _class(client, h, code):
    cid = client.post("/api/admin/classes", headers=h, json={"name": code, "code": code}).json()["id"]
    assert client.post(f"/api/classes/{cid}/activate", headers=h).status_code == 200
    return cid


def _register(client, mac, device_type, **extra):
    r = client.post("/api/device/register", headers=DEVICE,
                    json={"mac_address": mac, "device_type": device_type, "device_name": device_type, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def _gateway_of(db, cid):
    from app.models import ClassSession

    async def q(s):
        return (await s.execute(select(ClassSession.device_id).where(ClassSession.id == cid))).scalar_one()
    return db(q)


def test_non_gateway_registration_keeps_class_gateway(client, db):
    h = auth(login(client))
    cid = _class(client, h, "LAB1")
    c6 = _register(client, "AA:00:00:00:00:C6", "c6")
    assert c6["class_id"] == cid and _gateway_of(db, cid) == c6["device_id"]
    s3 = _register(client, "AA:00:00:00:00:53", "s3")              # S3 OTA hop registers
    node = _register(client, "AA:00:00:00:00:99", "student")
    assert s3["class_id"] is None and node["class_id"] is None
    assert _gateway_of(db, cid) == c6["device_id"]                 # still the C6
    snap = client.get(f"/api/classes/{cid}/presence", headers=h).json()
    assert snap["devices"][0]["id"] == c6["device_id"]


def test_second_gateway_takes_next_free_class(client, db):
    h = auth(login(client))
    first, second = _class(client, h, "LAB1"), _class(client, h, "LAB2")
    a = _register(client, "AA:00:00:00:00:01", "c6")
    b = _register(client, "AA:00:00:00:00:02", "c6")
    assert (a["class_id"], b["class_id"]) == (first, second)
    c = _register(client, "AA:00:00:00:00:03", "c6")               # no free class left
    assert c["class_id"] is None
    assert _gateway_of(db, first) == a["device_id"] and _gateway_of(db, second) == b["device_id"]


def test_gateway_keeps_its_class_on_reregister(client):
    h = auth(login(client))
    cid = _class(client, h, "LAB1")
    _register(client, "AA:00:00:00:00:C6", "c6")
    assert _register(client, "AA:00:00:00:00:C6", "c6")["class_id"] == cid


def test_explicit_classroom_code_still_assigns(client, db):
    h = auth(login(client))
    cid = client.post("/api/admin/classes", headers=h,
                      json={"name": "Rm", "code": "RM1", "classroom_code": "RM-201"}).json()["id"]
    gw = _register(client, "AA:00:00:00:00:C6", "c6", classroom_code="RM-201")
    assert gw["class_id"] == cid and _gateway_of(db, cid) == gw["device_id"]
