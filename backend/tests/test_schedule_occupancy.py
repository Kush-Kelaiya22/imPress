"""Dated timetable changes and room occupancy (#126).

2026-10-12 is a Monday, 2026-10-14 a Wednesday, 2026-10-15 a Thursday."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

from conftest import auth, login, make_class, make_user

MON, WED, THU = "2026-10-12", "2026-10-14", "2026-10-15"


@pytest.fixture
def su(client):
    return auth(login(client))


@pytest.fixture
def phy(client, su):
    return make_class(client, su, name="Physics", code="PHY1", classroom_code="RM-1",
                      start_date="2026-08-01", end_date="2026-12-15",
                      meeting_schedule=[{"day": "Monday", "start": "09:00", "end": "10:00"},
                                        {"day": "Monday", "start": "14:00", "end": "15:00"}])


def _busy(client, su, room, start, end):
    r = client.get(f"/api/admin/rooms/{room}/occupancy", headers=su, params={"start": start, "end": end})
    assert r.status_code == 200, r.text
    return r.json()


def _times(occ):
    return [(b["start"][11:16], b["end"][11:16], b["why"]) for b in occ["busy"]]


def _add(client, h, cid, **body):
    return client.post(f"/api/classes/{cid}/exceptions", headers=h, json=body)


def test_regular_slots_inside_the_class_dates(client, su, phy):
    assert _times(_busy(client, su, "RM-1", f"{MON}T00:00", f"{MON}T23:59")) == [
        ("09:00", "10:00", "regular"), ("14:00", "15:00", "regular")]
    assert _busy(client, su, "RM-1", "2026-12-21T00:00", "2026-12-21T23:59")["busy"] == []   # after end_date
    assert _busy(client, su, "rm-1", f"{MON}T09:30", f"{MON}T09:45")["busy"]                 # case, overlap


def test_cancelled_moved_and_extra(client, su, phy):
    assert _add(client, su, phy, kind="cancelled", date=MON, slot_start="09:00").status_code == 201
    assert _times(_busy(client, su, "RM-1", f"{MON}T00:00", f"{MON}T23:59")) == [("14:00", "15:00", "regular")]
    r = _add(client, su, phy, kind="moved", date=MON, slot_start="14:00", new_date=WED,
             new_start="16:00", new_end="17:00", classroom_code="RM-2")
    assert r.status_code == 201
    assert _busy(client, su, "RM-1", f"{MON}T00:00", f"{MON}T23:59")["busy"] == []
    assert _times(_busy(client, su, "RM-2", f"{WED}T00:00", f"{WED}T23:59")) == [("16:00", "17:00", "moved")]
    assert _add(client, su, phy, kind="extra", date=THU, new_start="11:00", new_end="12:30").status_code == 201
    assert _times(_busy(client, su, "RM-1", f"{THU}T00:00", f"{THU}T23:59")) == [("11:00", "12:30", "extra")]


def test_a_cancelled_day_frees_every_slot(client, su, phy):
    _add(client, su, phy, kind="cancelled", date=MON)
    assert _busy(client, su, "RM-1", f"{MON}T00:00", f"{MON}T23:59")["busy"] == []


def test_stale_authoritative_data_is_unknown(client, su, phy, db, monkeypatch):
    from app.config import settings
    old = (datetime.now() - timedelta(days=3)).isoformat(sep=" ")

    async def synced(s):
        await s.execute(text("INSERT INTO schedule_sources (source, last_synced_at, note) VALUES ('auris', :t, '')"),
                        {"t": old})
    db(synced)
    occ = _busy(client, su, "RM-1", f"{MON}T00:00", f"{MON}T23:59")
    assert occ["known"] is False and occ["busy"] == []
    monkeypatch.setattr(settings, "SCHEDULE_MAX_AGE_HOURS", 0)
    assert _busy(client, su, "RM-1", f"{MON}T00:00", f"{MON}T23:59")["known"] is True


def test_clash_warning_for_a_moved_or_extra_occurrence(client, su, phy):
    make_class(client, su, name="Chem", code="CHM1", classroom_code="RM-2",
               meeting_schedule=[{"day": "Wednesday", "start": "16:30", "end": "17:30"}])
    r = _add(client, su, phy, kind="moved", date=MON, slot_start="14:00", new_date=WED,
             new_start="16:00", new_end="17:00", classroom_code="RM-2")
    assert r.status_code == 201 and [w["type"] for w in r.json()["warnings"]] == ["room"]


@pytest.mark.parametrize("body", [
    {"kind": "moved", "date": MON, "new_start": "10:00", "new_end": "11:00"},          # which slot?
    {"kind": "extra", "date": THU},                                                    # when?
    {"kind": "extra", "date": THU, "new_start": "25:00", "new_end": "26:00"},
    {"kind": "postponed", "date": THU},
])
def test_invalid_changes_are_refused(client, su, phy, body):
    assert _add(client, su, phy, **body).status_code == 422


def test_only_class_staff_change_its_timetable(client, su, phy):
    _, outsider = make_user(client, su, "outsider")
    assert _add(client, outsider, phy, kind="cancelled", date=MON).status_code == 403
    assert client.get(f"/api/classes/{phy}/exceptions", headers=outsider).status_code == 403


def test_auris_rows_are_not_deleted_locally(client, su, phy, db):
    async def imported(s):
        await s.execute(text("INSERT INTO class_occurrence_exceptions (class_session_id, kind, date, slot_start, "
                             "new_start, new_end, classroom_code, source, note, updated_at) VALUES "
                             "(:c, 'cancelled', :d, '', '', '', '', 'auris', '', CURRENT_TIMESTAMP)"), {"c": phy, "d": MON})
    db(imported)
    eid = client.get(f"/api/classes/{phy}/exceptions", headers=su).json()[0]["id"]
    r = client.delete(f"/api/classes/{phy}/exceptions/{eid}", headers=su)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "SOURCE_MANAGED"
    local = _add(client, su, phy, kind="extra", date=THU, new_start="11:00", new_end="12:00").json()["id"]
    assert client.delete(f"/api/classes/{phy}/exceptions/{local}", headers=su).status_code == 204


def test_deleting_the_class_removes_its_changes(client, su, phy, db):
    _add(client, su, phy, kind="cancelled", date=MON)
    assert client.delete(f"/api/admin/classes/{phy}", headers=su).status_code == 200

    async def count(s):
        return (await s.execute(text("SELECT COUNT(*) FROM class_occurrence_exceptions"))).scalar()
    assert db(count) == 0
