"""#36: firmware version manager: approval, deprecation, retention, usage."""

import os
from pathlib import Path

import pytest
from sqlalchemy import update

from conftest import DEVICE, auth, login, make_user, upload_firmware

S3 = "a1b2c3d4e5f6"


@pytest.fixture
def h(client):
    return auth(login(client))


def _artifact(client, h, target, version):
    return next(a for a in client.get("/api/admin/firmware", headers=h).json()
                if (a["target"], a["version"]) == (target, version))


def _hub(client):
    return client.post("/api/device/register", headers=DEVICE,
                       json={"mac_address": S3, "device_type": "s3", "device_name": "hub"}).json()["device_id"]


def _push(client, h, dev, version):
    return client.post(f"/api/admin/modules/{dev}/ota", headers=h, json={"version": version})


def _set(db, **values):
    from app.models import EspDevice

    async def go(s):
        await s.execute(update(EspDevice).where(EspDevice.mac_address == S3).values(**values))
    db(go)


def test_only_approved_images_can_be_pushed(client, h):
    upload_firmware(client, h, "impress_class_s3", "2.2.0", approve=False)
    dev = _hub(client)
    r = _push(client, h, dev, "2.2.0")
    assert r.status_code == 409 and "is uploaded; only approved" in r.json()["detail"]
    a = _artifact(client, h, "s3", "2.2.0")
    approved = client.post(f"/api/admin/firmware/{a['id']}/approve", headers=h).json()
    assert approved["status"] == "approved" and approved["approved_by"] and approved["approved_at"]
    assert _push(client, h, dev, "2.2.0").status_code == 200


def test_deprecated_images_are_not_pushed_but_in_flight_updates_finish(client, h):
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    dev = _hub(client)
    assert _push(client, h, dev, "2.2.0").status_code == 200
    a = _artifact(client, h, "s3", "2.2.0")
    assert client.post(f"/api/admin/firmware/{a['id']}/deprecate", headers=h).json()["status"] == "deprecated"
    dl = client.get("/api/device/firmware/download", headers=DEVICE, params={"mac_address": S3, "version": "2.2.0"})
    assert dl.status_code == 200                           # the device already told to update can finish
    again = _push(client, h, dev, "2.2.0")
    assert again.status_code == 409 and "deprecated" in again.json()["detail"]
    # re-approval is allowed (undo)
    assert client.post(f"/api/admin/firmware/{a['id']}/approve", headers=h).json()["deprecated_at"] is None


def test_list_shows_latest_approved_and_device_usage(client, db, h):
    for v, approve in (("2.0.0", True), ("2.1.0", True), ("2.2.0", False)):
        upload_firmware(client, h, "impress_class_s3", v, approve=approve)
    upload_firmware(client, h, "impress_class_c6", "2.1.0")
    _hub(client)
    _set(db, firmware_version="2.0.0", pending_version="2.1.0")
    listed = client.get("/api/admin/firmware", headers=h).json()
    s3 = [a for a in listed if a["target"] == "s3"]
    assert [a["version"] for a in s3] == ["2.2.0", "2.1.0", "2.0.0"]            # newest first
    flags = {a["version"]: (a["latest_approved"], a["devices_running"], a["devices_pending"]) for a in s3}
    assert flags == {"2.2.0": (False, 0, 0), "2.1.0": (True, 0, 1), "2.0.0": (False, 1, 0)}
    c6 = next(a for a in listed if a["target"] == "c6")
    assert c6["latest_approved"] is True                   # per target


def test_only_notes_and_channel_are_editable(client, h):
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    a = _artifact(client, h, "s3", "2.2.0")
    r = client.patch(f"/api/admin/firmware/{a['id']}", headers=h,
                     json={"channel": "beta", "release_notes": "Fixes SPI link", "sha256": "0" * 64, "version": "9.9.9"})
    assert r.status_code == 200
    b = r.json()
    assert (b["channel"], b["release_notes"]) == ("beta", "Fixes SPI link")
    assert (b["sha256"], b["version"]) == (a["sha256"], "2.2.0")       # immutable fields ignored
    assert client.patch(f"/api/admin/firmware/{a['id']}", headers=h, json={"channel": "nightly"}).status_code == 422


def test_deletion_keeps_anything_a_device_needs(client, db, h):
    for v in ("2.0.0", "2.1.0", "2.2.0", "2.3.0"):
        upload_firmware(client, h, "impress_class_s3", v, approve=False)
    _hub(client)
    _set(db, firmware_version="2.0.0", pending_version="2.1.0")
    ids = {v: _artifact(client, h, "s3", v)["id"] for v in ("2.0.0", "2.1.0", "2.2.0", "2.3.0")}
    running = client.delete(f"/api/admin/firmware/{ids['2.0.0']}", headers=h)
    assert running.status_code == 409 and "1 device(s) run this version" in running.json()["detail"]
    assert client.delete(f"/api/admin/firmware/{ids['2.1.0']}", headers=h).status_code == 409   # pending
    client.post(f"/api/admin/firmware/{ids['2.2.0']}/approve", headers=h)
    assert "Deprecate" in client.delete(f"/api/admin/firmware/{ids['2.2.0']}", headers=h).json()["detail"]
    unused = _artifact(client, h, "s3", "2.3.0")
    assert client.delete(f"/api/admin/firmware/{ids['2.3.0']}", headers=h).status_code == 200
    assert not (Path(os.environ["IMPRESS_FIRMWARE_DIR"]) / f"{unused['sha256']}.bin").exists()
    assert [a["version"] for a in client.get("/api/admin/firmware", headers=h).json()] == ["2.2.0", "2.1.0", "2.0.0"]


def test_detail_lists_devices_and_history(client, db, h):
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    dev = _hub(client)
    _push(client, h, dev, "2.2.0")
    a = _artifact(client, h, "s3", "2.2.0")
    d = client.get(f"/api/admin/firmware/{a['id']}", headers=h).json()
    assert d["artifact"]["devices_pending"] == 1
    assert [x["mac_address"] for x in d["devices"]] == [S3]
    actions = [x["action"] for x in d["history"]]
    assert {"firmware.upload", "firmware.approve", "module.ota"} <= set(actions)
    assert client.get("/api/admin/firmware/999", headers=h).status_code == 404


def test_admin_only(client, h):
    upload_firmware(client, h, "impress_class_s3", "2.2.0", approve=False)
    a = _artifact(client, h, "s3", "2.2.0")
    _, teacher = make_user(client, h, "teach1")
    for method, path in (("post", f"/{a['id']}/approve"), ("post", f"/{a['id']}/deprecate"),
                         ("delete", f"/{a['id']}"), ("get", f"/{a['id']}"), ("patch", f"/{a['id']}")):
        kw = {"json": {}} if method == "patch" else {}
        assert getattr(client, method)(f"/api/admin/firmware{path}", headers=teacher, **kw).status_code == 403
