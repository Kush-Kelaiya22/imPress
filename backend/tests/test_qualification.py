"""TrustedInstaller qualification (#154): analysis + OTA client simulation."""

import hashlib
import struct

import pytest
from sqlalchemy import text

from conftest import DEVICE, auth, login, upload_firmware
from firmware_images import make_image


def _resign(data: bytes) -> bytes:
    """Re-append a valid SHA-256 so only the property under test is wrong."""
    body = data[:-32]
    return body + hashlib.sha256(body).digest()


def _problems(data, target="c6"):
    from app.services.qualification import analysis
    return analysis(data, target)["problems"]


@pytest.mark.parametrize("project,target", [("impress_class_c6", "c6"), ("impress_class_s3", "s3"),
                                            ("impress_student", "student")])
def test_a_valid_image_qualifies(project, target):
    from app.services.qualification import qualify
    r = qualify(make_image(project, "2.2.0"), target, "2.2.0")
    assert r["status"] == "qualified"
    assert [s["stage"] for s in r["stages"]] == ["analysis", "ota_client", "emulator"]
    assert r["stages"][2]["passed"] is None                   # not run on the binary, and says why


def test_a_segment_outside_the_chip_memory():
    data = bytearray(make_image())
    struct.pack_into("<I", data, 24, 0x3C000020)              # an S3 address, not mapped on the C6
    assert any("outside esp32c6 memory" in p for p in _problems(_resign(bytes(data))))


def test_an_entry_point_that_is_not_executable():
    data = bytearray(make_image())
    struct.pack_into("<I", data, 4, 0x3FC00000)
    assert any("entry point" in p for p in _problems(_resign(bytes(data))))


def test_a_wrong_checksum_byte():
    data = bytearray(make_image())
    data[-33] ^= 0x01
    assert "segment checksum byte does not match" in _problems(_resign(bytes(data)))


def test_an_empty_chip_revision_range():
    data = bytearray(make_image())
    struct.pack_into("<HH", data, 15, 300, 100)
    assert any("chip revision range" in p for p in _problems(_resign(bytes(data))))


def test_the_simulated_device_refuses_a_version_mismatch():
    from app.services.qualification import ota_client
    stage = ota_client(make_image(version="2.2.0"), "c6", "9.9.9")
    assert not stage["passed"] and "rebooted into 2.2.0, expected 9.9.9" in stage["problems"][0]


@pytest.fixture
def h(client):
    return auth(login(client))


def _artifact(client, h):
    return client.get("/api/admin/firmware", headers=h).json()[0]


def test_upload_stores_the_report_and_shows_it(client, h):
    upload_firmware(client, h, "impress_class_c6", "2.2.0", approve=False)
    a = _artifact(client, h)
    assert a["qualification"]["status"] == "qualified"


FAILED = {"status": "failed", "stages": [{"stage": "analysis", "passed": False,
                                           "problems": ["forced by test"], "proves": ""}]}


def _set_report(db, make):
    """Store make(artifact) as the qualification report of every artifact."""
    async def put(s):
        from sqlalchemy import select
        from app.models import FirmwareArtifact
        for a in (await s.execute(select(FirmwareArtifact))).scalars():
            a.qualification = make(a)
        await s.commit()
    db(put)


def _fail_report(db):
    """As if the TrustedInstaller had run and failed the image."""
    from app.services.qualification import attest
    _set_report(db, lambda a: attest(FAILED, a))


def test_approval_needs_a_passing_report(client, h, db):
    upload_firmware(client, h, "impress_class_c6", "2.2.0", approve=False)
    _fail_report(db)
    r = client.post(f"/api/admin/firmware/{_artifact(client, h)['id']}/approve", headers=h)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "NOT_QUALIFIED"


def test_offers_recheck_the_report(client, h, db):
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    dev = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:01", "device_type": "c6", "firmware_version": "2.1.0"}).json()["device_id"]
    _fail_report(db)
    r = client.post("/api/admin/deployments?dry_run=true", headers=h,
                    json={"artifact_id": _artifact(client, h)["id"], "device_ids": [dev]}).json()
    assert "not qualified (analysis: forced by test)" in r["excluded"][0]["reason"]


def test_images_from_before_qualification_are_checked_on_demand(client, h, db):
    upload_firmware(client, h, "impress_class_c6", "2.2.0")

    async def legacy(s):
        await s.execute(text("UPDATE firmware_artifacts SET qualification = NULL"))
    db(legacy)
    dev = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:01", "device_type": "c6", "firmware_version": "2.1.0"}).json()["device_id"]
    r = client.post("/api/admin/deployments?dry_run=true", headers=h,
                    json={"artifact_id": _artifact(client, h)["id"], "device_ids": [dev]}).json()
    assert r["excluded"] == []


# ── Attestation (v2.2): a stored report is trusted only for its own image ──

def _register_c6(client):
    return client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:01", "device_type": "c6", "firmware_version": "2.1.0"}).json()["device_id"]


def _excluded(client, h, dev):
    return client.post("/api/admin/deployments?dry_run=true", headers=h,
                       json={"artifact_id": _artifact(client, h)["id"], "device_ids": [dev]}).json()["excluded"]


def test_upload_stores_an_attested_report_for_these_bytes(client, h):
    upload_firmware(client, h, "impress_class_c6", "2.2.0", approve=False)
    r = _artifact(client, h)["qualification"]
    assert r["subject"]["sha256"] == _artifact(client, h)["sha256"] and len(r["attestation"]) == 64


def test_a_forged_passing_report_is_not_trusted(client, h, db, monkeypatch):
    """Someone with database access marks an image qualified. The report is
    not attested, so the TrustedInstaller recomputes it from the bytes; here
    the bytes fail (qualify is replaced to stand for a bad image)."""
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    dev = _register_c6(client)
    _set_report(db, lambda a: {"status": "qualified", "stages": []})
    from app.services import trusted_installer
    monkeypatch.setattr(trusted_installer, "qualify", lambda *a: FAILED)
    assert "not qualified (analysis: forced by test)" in _excluded(client, h, dev)[0]["reason"]


def test_an_edited_attested_report_is_not_trusted(client, h, db, monkeypatch):
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    dev = _register_c6(client)
    from app.services.qualification import attest
    _set_report(db, lambda a: {**attest(FAILED, a), "status": "qualified"})       # seal kept, content changed
    from app.services import trusted_installer
    monkeypatch.setattr(trusted_installer, "qualify", lambda *a: FAILED)
    assert _excluded(client, h, dev)[0]["reason"].startswith("not qualified")


def test_a_report_copied_from_another_image_is_not_trusted():
    from types import SimpleNamespace
    from app.services.qualification import SUBJECT_FIELDS, attest, attested
    a = SimpleNamespace(**{f: f"a-{f}" for f in SUBJECT_FIELDS})
    b = SimpleNamespace(**{**vars(a), "sha256": "b-sha256"})
    r = attest({"status": "qualified", "stages": []}, a)
    assert attested(r, a) and not attested(r, b)


def test_rotating_the_server_secret_invalidates_reports(monkeypatch):
    from types import SimpleNamespace
    from app.config import settings
    from app.services.qualification import SUBJECT_FIELDS, attest, attested
    a = SimpleNamespace(**{f: f"a-{f}" for f in SUBJECT_FIELDS})
    r = attest({"status": "qualified", "stages": []}, a)
    monkeypatch.setattr(settings, "JWT_SECRET", "a-new-secret-after-rotation")
    assert not attested(r, a)


def test_an_unattested_report_is_recomputed_from_the_bytes(client, h, db):
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    dev = _register_c6(client)
    _set_report(db, lambda a: {"status": "failed", "stages": []})   # untrusted either way
    assert _excluded(client, h, dev) == []                          # the real bytes qualify
