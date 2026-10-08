"""#16: admin firmware upload works and OTA prompts are audit-logged."""

import os
from pathlib import Path

from sqlalchemy import select, update

from conftest import DEVICE, DEVICE_KEY, auth, login, upload_firmware


def _activity(db, action):
    from app.models import ActivityLog

    async def q(s):
        return (await s.execute(select(ActivityLog).where(ActivityLog.action == action))).scalars().all()
    return db(q)


def test_firmware_upload_succeeds_and_is_logged(client, db):
    from firmware_images import make_image
    h = auth(login(client))
    image = make_image("impress_class_s3", "1.2.3")
    r = client.post("/api/admin/firmware/upload", headers=h,
                    data={"device_type": "s3", "version": "1.2.3"},
                    files={"file": ("fw.bin", image, "application/octet-stream")})
    assert r.status_code == 200, r.text
    a = r.json()
    assert (a["target"], a["version"], a["status"], a["created"]) == ("s3", "1.2.3", "uploaded", True)
    assert (Path(os.environ["IMPRESS_FIRMWARE_DIR"]) / f"{a['sha256']}.bin").read_bytes() == image
    rows = _activity(db, "firmware.upload")
    assert len(rows) == 1 and rows[0].details["version"] == "1.2.3" and rows[0].details["target"] == "s3"


def test_bad_device_type_rejected(client):
    r = client.post("/api/admin/firmware/upload", headers=auth(login(client)),
                    data={"device_type": "toaster", "version": "1.0.0"},
                    files={"file": ("fw.bin", b"x", "application/octet-stream")})
    assert r.status_code == 400


def test_s3_ota_push_prompts_gateway_and_logs(client, db):
    from app.models import EspDevice
    h = auth(login(client))
    # a push needs an uploaded image (#33); this test used to rely on another test's upload
    upload_firmware(client, h, "impress_class_s3", "1.2.3")
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Lab", "code": "LAB1"}).json()["id"]
    assert client.post(f"/api/classes/{cid}/activate", headers=h).status_code == 200   # gateways link to active classes
    c6 = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "AA:00:00:00:00:C6", "device_type": "c6", "device_name": "gw"}).json()
    assert c6["class_id"] == cid                 # gateway auto-linked to the class
    s3 = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "AA:00:00:00:00:53", "device_type": "s3", "device_name": "hub"}).json()

    async def link(s):
        await s.execute(update(EspDevice).where(EspDevice.id == s3["device_id"]).values(gateway_id=c6["device_id"]))
    db(link)

    with client.websocket_connect(f"/ws/class/{cid}?role=device&api_key={DEVICE_KEY}") as ws:
        ws.receive_json()                        # connected
        r = client.post(f"/api/admin/modules/{s3['device_id']}/ota", headers=h, json={"version": "1.2.3"})
        assert r.status_code == 200, r.text
        frame = ws.receive_json()
    assert frame["event"] == "device_command" and frame["command"] == "ota_update"
    assert frame["payload"]["version"] == "1.2.3"
    rows = _activity(db, "module.ota.prompt")
    assert len(rows) == 1 and rows[0].details == {"to_class": cid, "version": "1.2.3"}
