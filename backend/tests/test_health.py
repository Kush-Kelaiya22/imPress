"""#39: device health states from the latest heartbeat diagnostics."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from conftest import DEVICE, auth, login

NOW = datetime(2026, 10, 8, 12, 0, 0)
GW = "48:F6:EE:00:00:C6"


def _dev(**kw):
    from app.models import EspDevice
    base = dict(last_seen=NOW - timedelta(seconds=5), is_connected=True, ota_status="idle", rssi=-55,
                reset_reason=None, uptime_s=None, diag_at=None, s3_link_ok=None, min_free_heap=None)
    return EspDevice(**{**base, **kw})


@pytest.mark.parametrize("kw,state,reason", [
    ({"last_seen": None}, "UNKNOWN", "never seen"),
    ({"last_seen": NOW - timedelta(seconds=31)}, "OFFLINE", "silent for 31 s"),
    ({"is_connected": False}, "OFFLINE", "silent"),
    ({"ota_status": "downloading"}, "UPDATING", "OTA downloading"),
    ({"ota_status": "failed"}, "ERROR", "last OTA update failed"),
    ({"ota_status": "rolled_back"}, "ERROR", "last OTA update rolled back"),
    ({"reset_reason": "panic", "uptime_s": 60, "diag_at": NOW - timedelta(seconds=60)}, "ERROR",
     "reset by panic 2 min ago"),
    ({"reset_reason": "brownout", "uptime_s": 590, "diag_at": NOW}, "ERROR", "reset by brownout"),
    ({"s3_link_ok": False}, "DEGRADED", "S3 link down"),
    ({"rssi": -81}, "DEGRADED", "weak Wi-Fi (-81 dBm)"),
    ({"min_free_heap": 20 * 1024 - 1}, "DEGRADED", "low memory"),
    ({}, "ONLINE", None),
    ({"rssi": -80, "min_free_heap": 20 * 1024, "s3_link_ok": True}, "ONLINE", None),     # thresholds are exclusive
    ({"reset_reason": "panic", "uptime_s": 600, "diag_at": NOW}, "ONLINE", None),        # crash > 10 min ago
    ({"reset_reason": "poweron", "uptime_s": 5, "diag_at": NOW}, "ONLINE", None),        # a normal power-up
    ({"rssi": 0}, "ONLINE", None),                     # pre-#39 rows: 0 is "not reported"
])
def test_rules(kw, state, reason):
    from app.services.health import health
    got, reasons = health(_dev(**kw), NOW)
    assert got == state
    assert (reason is None and reasons == []) or any(reason in r for r in reasons), reasons


def test_precedence_offline_over_updating_over_error_over_degraded():
    from app.services.health import health
    worst = dict(ota_status="downloading", s3_link_ok=False, reset_reason="panic", uptime_s=1, diag_at=NOW)
    assert health(_dev(**worst, is_connected=False), NOW)[0] == "OFFLINE"
    assert health(_dev(**worst), NOW)[0] == "UPDATING"
    assert health(_dev(**{**worst, "ota_status": "idle"}), NOW)[0] == "ERROR"
    errors_and_degraded = health(_dev(ota_status="failed", s3_link_ok=False), NOW)
    assert errors_and_degraded == ("ERROR", ["last OTA update failed"])


def test_heartbeat_stores_diagnostics_and_old_firmware_still_works(client, db):
    from app.models import EspDevice
    client.post("/api/device/register", headers=DEVICE, json={"mac_address": GW, "device_type": "c6"})
    old = client.post("/api/device/heartbeat", headers=DEVICE, json={"mac_address": GW, "rssi": -60})
    assert old.status_code == 200

    async def get(s):
        return await s.scalar(select(EspDevice).where(EspDevice.mac_address == GW))
    d = db(get)
    assert (d.reset_reason, d.diag_at, d.s3_link_ok) == (None, None, None)

    r = client.post("/api/device/heartbeat", headers=DEVICE, json={
        "mac_address": GW, "rssi": -60, "uptime_s": 42, "reset_reason": "task_wdt", "boot_count": 7,
        "min_free_heap": 51200, "s3_link_ok": False, "s3_uptime_s": 40})
    assert r.status_code == 200
    d = db(get)
    assert (d.uptime_s, d.reset_reason, d.boot_count, d.min_free_heap, d.s3_link_ok, d.s3_uptime_s) == \
        (42, "task_wdt", 7, 51200, False, 40)
    assert d.diag_at is not None

    h = auth(login(client))
    [m] = client.get("/api/admin/modules", headers=h).json()
    assert m["health"] == "ERROR" and m["health_reasons"] == ["reset by task_wdt 0 min ago"]
    assert (m["boot_count"], m["s3_link_ok"]) == (7, False)


@pytest.mark.parametrize("bad", [{"uptime_s": -1}, {"reset_reason": "x" * 17}, {"min_free_heap": -5}])
def test_invalid_diagnostics_are_rejected(client, bad):
    client.post("/api/device/register", headers=DEVICE, json={"mac_address": GW, "device_type": "c6"})
    r = client.post("/api/device/heartbeat", headers=DEVICE, json={"mac_address": GW, **bad})
    assert r.status_code == 422
