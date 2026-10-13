"""Boards report what they are; images must fit them (#129)."""

import pytest

from conftest import DEVICE, auth, login, upload_firmware
from firmware_images import make_image

MAC = "48:F6:EE:00:00:01"


def _register(client, caps=None, version="2.1.0"):
    body = {"mac_address": MAC, "device_type": "c6", "firmware_version": version}
    if caps is not None:
        body["caps"] = caps
    r = client.post("/api/device/register", headers=DEVICE, json=body)
    assert r.status_code == 200, r.text
    return r.json()["device_id"]


@pytest.fixture
def h(client):
    return auth(login(client))


def test_caps_are_stored_and_shown(client, h):
    dev = _register(client, {"chip_rev": 1, "flash_mb": 8, "psram_mb": 0, "slot_kb": 3968, "rollback": True})
    m = client.get(f"/api/admin/modules/{dev}", headers=h).json()
    assert (m["chip_rev"], m["flash_mb"], m["psram_mb"], m["ota_slot_kb"], m["rollback_supported"]) == (1, 8, 0, 3968, True)


def test_older_firmware_without_caps_is_unknown_not_refused(client, h):
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    dev = _register(client)
    m = client.get(f"/api/admin/modules/{dev}", headers=h).json()
    assert m["flash_mb"] is None and m["rollback_supported"] is None
    aid = client.get("/api/admin/firmware", headers=h).json()[0]["id"]
    r = client.post("/api/admin/deployments?dry_run=true", headers=h, json={"artifact_id": aid, "device_ids": [dev]})
    assert r.json()["excluded"] == []


def test_an_image_larger_than_the_board_slot_is_excluded(client, h):
    upload_firmware(client, h, "impress_class_c6", "2.2.0", payload=b"\x00" * 4096)
    dev = _register(client, {"flash_mb": 8, "slot_kb": 1})
    aid = client.get("/api/admin/firmware", headers=h).json()[0]["id"]
    r = client.post("/api/admin/deployments?dry_run=true", headers=h, json={"artifact_id": aid, "device_ids": [dev]})
    assert "OTA slot holds 1 KB" in r.json()["excluded"][0]["reason"]


def test_an_image_built_for_more_flash_than_the_board_has():
    """The 32 MB octal hub image on an 8 MB quad hub aborts at boot."""
    from app.models import EspDevice
    from app.services.trusted_installer import board_refusal
    data = bytearray(make_image("impress_class_s3"))
    data[3] = (5 << 4) | (data[3] & 0x0F)                    # header: 32 MB flash
    small = EspDevice(device_type="s3", flash_mb=8)
    assert "built for 32 MB flash, this board has 8 MB" in board_refusal(bytes(data), small)
    assert board_refusal(bytes(data), EspDevice(device_type="s3", flash_mb=32)) is None
    assert board_refusal(bytes(data), EspDevice(device_type="s3")) is None   # not reported: not refused here


def test_invalid_caps_are_rejected(client):
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": MAC, "device_type": "c6", "caps": {"flash_mb": -1}})
    assert r.status_code == 422
