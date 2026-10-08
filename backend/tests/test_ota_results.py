"""#33: OTA outcomes are recorded only from what the device really runs, and a
push needs an uploaded image."""

import pytest
from sqlalchemy import select

from conftest import DEVICE, auth, login, upload_firmware

S3_MAC = "a1b2c3d4e5f6"          # the S3 registers its MAC as 12 hex digits
C6_MAC = "48:F6:EE:00:00:01"


@pytest.fixture
def hub(client):
    h = auth(login(client))
    r = client.post("/api/device/register", headers=DEVICE,
                    json={"mac_address": S3_MAC, "device_type": "s3", "device_name": "hub"})
    assert r.status_code == 200, r.text
    upload_firmware(client, h, "impress_class_s3", "2.1.0")
    return h, r.json()["device_id"]


def _device(db):
    from app.models import EspDevice

    async def q(s):
        return (await s.execute(select(EspDevice).where(EspDevice.mac_address == S3_MAC))).scalar_one()
    return db(q)


def _report(client, result, version="2.1.0", error=0, mac=S3_MAC):
    return client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "ota_result", "mac_address": mac, "version": version, "result": result,
         "error": error, "device_mac": C6_MAC}]})


def _push(client, hub, version="2.1.0"):
    h, dev = hub
    return client.post(f"/api/admin/modules/{dev}/ota", headers=h, json={"version": version})


def test_push_of_a_version_that_was_never_uploaded_is_refused(client, db, hub):
    r = _push(client, hub, "9.9.9")
    assert r.status_code == 404 and "upload it first" in r.json()["detail"]
    d = _device(db)
    assert d.pending_version == "" and d.ota_status != "downloading"     # was: 'downloading' forever


def test_push_normalises_the_version(client, db, hub):
    assert _push(client, hub, "v2.1.0").status_code == 200
    assert _device(db).pending_version == "2.1.0"


def test_applied_with_the_pushed_version_completes_the_update(client, db, hub):
    _push(client, hub)
    r = _report(client, "applied")
    assert r.status_code == 200 and r.json()["processed"] == 1
    d = _device(db)
    assert (d.firmware_version, d.pending_version, d.ota_status) == ("2.1.0", "", "success")
    # the loop is gone: the device is no longer offered the same update
    chk = client.post("/api/device/firmware/check", headers=DEVICE,
                      json={"mac_address": S3_MAC, "current_version": "2.1.0"}).json()
    assert chk["update_available"] is False

    from app.models import ActivityLog

    async def log(s):
        return await s.scalar(select(ActivityLog).where(ActivityLog.action == "module.ota_result"))
    entry = db(log)
    assert entry.details["result"] == "applied" and entry.details["gateway_mac"] == C6_MAC


def test_applied_with_another_version_is_not_success(client, db, hub):
    _push(client, hub)
    _report(client, "applied", version="2.0.9")
    d = _device(db)
    assert d.firmware_version == "2.0.9" and d.ota_status == "failed"


def test_rollback_is_recorded_and_not_offered_again(client, db, hub):
    _push(client, hub)
    d0 = _device(db).firmware_version
    _report(client, "rolled_back")
    d = _device(db)
    assert (d.ota_status, d.pending_version, d.firmware_version) == ("rolled_back", "", d0)


def test_failure_keeps_the_pending_version_for_a_retry(client, db, hub):
    _push(client, hub)
    _report(client, "failed", error=0x108)
    d = _device(db)
    assert (d.ota_status, d.pending_version) == ("failed", "2.1.0")


@pytest.mark.parametrize("kw", [{"result": "bogus"}, {"result": "applied", "mac": "000000000000"},
                                {"result": "applied", "mac": ""}])
def test_malformed_or_unknown_reports_are_skipped(client, db, hub, kw):
    result = kw.pop("result")
    r = _report(client, result, **kw)
    assert r.status_code == 200 and r.json()["skipped"] == 1
    assert _device(db).ota_status == "idle"
