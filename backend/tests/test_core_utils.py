"""Pure helpers: time (timeutil), schedule overlap maths (schedule), firmware
store path safety (services/firmware_store), WebSocket manager (ws/manager)."""

import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException


# ── timeutil ────────────────────────────────────────────────────────────────

def test_istnow_is_naive_and_utc_plus_0530():
    from app.timeutil import istnow, istnow_aware
    now = istnow()
    assert now.tzinfo is None
    utc = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs((now - utc).total_seconds() - 5.5 * 3600) < 5
    assert istnow_aware().utcoffset().total_seconds() == 5.5 * 3600


def test_as_ist_treats_naive_as_utc():
    from app.timeutil import as_ist
    assert as_ist(datetime(2026, 1, 1, 0, 0)) == datetime(2026, 1, 1, 5, 30)
    assert as_ist(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)) == datetime(2026, 1, 1, 5, 30)


def test_ist_epoch_ms_is_host_timezone_independent():
    from app.timeutil import ist_epoch_ms
    assert ist_epoch_ms(None) is None
    # 2026-01-01 05:30 IST == 2026-01-01 00:00 UTC
    assert ist_epoch_ms(datetime(2026, 1, 1, 5, 30)) == int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def test_ist_iso_has_offset():
    from app.timeutil import ist_iso
    assert ist_iso().endswith("+05:30")


# ── schedule ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,minutes", [("09:00", 540), ("9:05", 545), ("23:59", 1439), (" 00:00 ", 0),
                                          ("24:00", None), ("9:60", None), ("nine", None), ("", None)])
def test_parse_time(text, minutes):
    from app.schedule import _parse_time
    assert _parse_time(text) == minutes


@pytest.mark.parametrize("a,b,overlap", [
    (("09:00", "10:00"), ("09:30", "10:30"), True),
    (("09:00", "10:00"), ("10:00", "11:00"), False),   # touching is fine
    (("09:00", "12:00"), ("10:00", "11:00"), True),    # containment
    (("22:00", "01:00"), ("23:00", "23:30"), True),    # overnight clamps to 23:59
    (("09:00", "10:00"), ("bad", "11:00"), False),     # malformed never conflicts
])
def test_slots_conflict(a, b, overlap):
    from app.schedule import _slots_conflict
    assert _slots_conflict(*a, *b) is overlap
    assert _slots_conflict(*b, *a) is overlap          # symmetric


def test_same_academic_window_rules():
    from datetime import date
    from app.models import ClassSession
    from app.schedule import _same_academic_window as same
    a = ClassSession(term="Monsoon", year=2026)
    assert same(a, ClassSession(term="Monsoon", year=2026))
    assert not same(a, ClassSession(term="Winter", year=2026))
    d1 = ClassSession(start_date=date(2026, 1, 1), end_date=date(2026, 4, 30))
    assert same(d1, ClassSession(start_date=date(2026, 4, 1), end_date=date(2026, 8, 1)))
    assert not same(d1, ClassSession(start_date=date(2026, 5, 1), end_date=date(2026, 8, 1)))
    assert same(ClassSession(), ClassSession())        # unknown window → conservatively flag


# ── firmware store ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,norm", [("1.2.3", "1.2.3"), ("v1.2.3", "1.2.3"), (" V10.0.1 ", "10.0.1")])
def test_normalize_version(raw, norm):
    from app.services.firmware_store import normalize_version
    assert normalize_version(raw) == norm


@pytest.mark.parametrize("bad", ["", "1.2", "1.2.3.4", "1.2.3-beta", "../../etc/passwd", "1.2.3/../../x"])
def test_normalize_version_rejects_anything_else(bad):
    from app.services.firmware_store import normalize_version
    with pytest.raises(HTTPException):
        normalize_version(bad)


def test_get_firmware_path_cannot_escape_store(tmp_path, monkeypatch):
    from app.config import settings
    from app.services.firmware_store import get_firmware_path
    monkeypatch.setattr(settings, "FIRMWARE_DIR", str(tmp_path))
    (tmp_path / "s3-1.0.0.bin").write_bytes(b"x")
    assert get_firmware_path("s3", "1.0.0") == tmp_path / "s3-1.0.0.bin"
    for version in ("../1.0.0", "1.0.0/.."):
        with pytest.raises(HTTPException):
            get_firmware_path("s3", version)
    with pytest.raises(HTTPException) as e:
        get_firmware_path("s3", "9.9.9")
    assert e.value.status_code == 404


# ── WebSocket connection manager ────────────────────────────────────────────

class FakeWS:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def accept(self):
        pass

    async def send_text(self, text):
        if self.fail:
            raise RuntimeError("socket closed")
        self.sent.append(text)


def test_manager_role_routing_and_dead_socket_cleanup():
    from app.ws.manager import ConnectionManager
    m = ConnectionManager()
    teacher, device, dead = FakeWS(), FakeWS(), FakeWS(fail=True)

    async def scenario():
        await m.connect(teacher, 5, "teacher")
        await m.connect(device, 5, "device")
        await m.connect(dead, 5, "teacher")
        await m.broadcast_to_role(5, {"n": 1}, role="teacher")
        await m.broadcast_to_class(5, {"n": 2})
    asyncio.run(scenario())
    assert teacher.sent == ['{"n": 1}', '{"n": 2}']
    assert device.sent == ['{"n": 2}']
    assert m.get_connection_count(5) == 2              # dead socket pruned


def test_manager_disconnect_frees_empty_rooms():
    from app.ws.manager import ConnectionManager
    m = ConnectionManager()
    ws = FakeWS()
    asyncio.run(m.connect(ws, 9, "device"))
    m.disconnect(ws, 9)
    assert 9 not in m.active_connections and 9 not in m.connection_roles
    m.disconnect(ws, 9)                                # idempotent
    asyncio.run(m.broadcast_to_class(9, {"x": 1}))     # unknown room is a no-op
