"""TrustedInstaller (#123): firmware reaches a device only after its own checks,
re-run at every offer and download, whatever the database or the request says."""

import pytest
from sqlalchemy import text

from conftest import DEVICE, auth, login, make_user, upload_firmware

MAC = "a1b2c3d4e501"


@pytest.fixture
def h(client):
    return auth(login(client))


def _register(client, version="2.1.0"):
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": MAC, "device_type": "s3", "firmware_version": version})
    assert r.status_code == 200, r.text
    return r.json()["device_id"]


def _artifact(client, h):
    return client.get("/api/admin/firmware", headers=h).json()[0]


def _deploy(client, h, dev, dry_run=False):
    return client.post(f"/api/admin/deployments{'?dry_run=true' if dry_run else ''}", headers=h,
                       json={"artifact_id": _artifact(client, h)["id"], "device_ids": [dev]})


def _download(client):
    return client.get("/api/device/firmware/download", headers=DEVICE,
                      params={"mac_address": MAC, "version": "2.2.0"})


@pytest.fixture
def strict(monkeypatch):
    """The production defaults: no unsigned images, no self-approval."""
    from app.config import settings
    monkeypatch.setattr(settings, "FIRMWARE_ALLOW_UNSIGNED", False)
    monkeypatch.setattr(settings, "FIRMWARE_SINGLE_APPROVER", False)
    monkeypatch.setattr(settings, "DEBUG", False)


def test_unsigned_images_need_an_explicit_site_decision(client, h, monkeypatch):
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    dev = _register(client)
    from app.config import settings
    monkeypatch.setattr(settings, "FIRMWARE_ALLOW_UNSIGNED", False)
    r = _deploy(client, h, dev, dry_run=True).json()
    assert "IMPRESS_FIRMWARE_ALLOW_UNSIGNED" in r["excluded"][0]["reason"]
    monkeypatch.setattr(settings, "FIRMWARE_ALLOW_UNSIGNED", True)
    assert _deploy(client, h, dev, dry_run=True).json()["excluded"] == []


def test_a_tampered_file_is_never_served(client, h):
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    dev = _register(client)
    assert _deploy(client, h, dev).status_code == 200
    from app.services.firmware_store import artifact_path
    path = artifact_path(_artifact(client, h)["sha256"])
    data = bytearray(path.read_bytes())
    data[-40] ^= 0xFF                                          # same size, different bytes
    path.write_bytes(bytes(data))
    r = _download(client)
    assert r.status_code == 403 and "SHA-256" in r.json()["detail"]


def test_the_site_policy_is_rechecked_at_download(client, h, monkeypatch):
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    dev = _register(client)
    assert _deploy(client, h, dev).status_code == 200
    assert _download(client).status_code == 200
    from app.config import settings
    monkeypatch.setattr(settings, "FIRMWARE_ALLOW_UNSIGNED", False)   # the site tightened its policy
    r = _download(client)
    assert r.status_code == 403 and "TrustedInstaller" in r.json()["detail"]


def test_a_database_edit_to_approved_is_not_enough(client, h, db):
    upload_firmware(client, h, "impress_class_s3", "2.2.0", approve=False)
    dev = _register(client)

    async def forge(s):
        await s.execute(text("UPDATE firmware_artifacts SET status = 'approved'"))  # approved_by stays NULL
    db(forge)
    r = _deploy(client, h, dev).json()
    assert "not approved" in r["detail"]["excluded"][0]["reason"]


def test_uploader_cannot_approve_their_own_image(client, h, strict):
    upload_firmware(client, h, "impress_class_s3", "2.2.0", approve=False)
    aid = _artifact(client, h)["id"]
    r = client.post(f"/api/admin/firmware/{aid}/approve", headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SEPARATION_OF_DUTIES"
    _, other = make_user(client, h, "adm2", role="admin")
    assert client.post(f"/api/admin/firmware/{aid}/approve", headers=other).status_code == 200


def test_single_approver_sites_allow_a_super_admin_only(client, h, strict, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "FIRMWARE_SINGLE_APPROVER", True)
    _, adm = make_user(client, h, "adm2", role="admin")
    upload_firmware(client, adm, "impress_class_s3", "2.2.0", approve=False)
    aid = _artifact(client, h)["id"]
    assert client.post(f"/api/admin/firmware/{aid}/approve", headers=adm).status_code == 403
    upload_firmware(client, h, "impress_class_c6", "2.2.0", approve=False)
    c6 = next(a["id"] for a in client.get("/api/admin/firmware", headers=h).json() if a["target"] == "c6")
    assert client.post(f"/api/admin/firmware/{c6}/approve", headers=h).status_code == 200
    logs = client.get("/api/admin/activity", headers=h).json()
    assert any(e["action"] == "firmware.approve" and e["details"].get("self_approval") for e in logs)


def test_chip_and_type_must_both_match():
    from app.models import EspDevice, FirmwareArtifact
    from app.services.trusted_installer import refusal
    s3 = EspDevice(device_type="s3", is_active=True)
    forged = FirmwareArtifact(target="s3", chip="esp32c6", status="approved", approved_by=1, sha256="0" * 64, size=1)
    assert "incompatible" in refusal(forged, s3)
    other = FirmwareArtifact(target="c6", chip="esp32c6", status="approved", approved_by=1, sha256="0" * 64, size=1)
    assert "incompatible" in refusal(other, s3)


def test_no_route_reaches_the_trusted_installer_directly():
    from test_policy import _routes
    assert not [r.path for r in _routes() if "trusted" in r.path.lower() or "installer" in r.path.lower()]
