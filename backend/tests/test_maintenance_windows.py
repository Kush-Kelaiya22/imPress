"""Hub and gateway updates only in classroom downtime (#128).

The room RM-1 has Physics on Mondays 09:00-10:00. 2026-10-12 is a Monday.
Default window: 20 min for the update, 10 min buffer before and after."""

from datetime import datetime

import pytest
from sqlalchemy import text

from conftest import DEVICE, auth, login, make_class, make_user, upload_firmware

MON = datetime(2026, 10, 12)


def at(h, m=0):
    return MON.replace(hour=h, minute=m)


@pytest.fixture
def h(client):
    h = auth(login(client))
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    return h


@pytest.fixture
def room(client, h):
    return make_class(client, h, name="Physics", code="PHY1", classroom_code="RM-1",
                      meeting_schedule=[{"day": "Monday", "start": "09:00", "end": "10:00"}])


def _gateway(client, mac="48:F6:EE:00:00:01", room_code="RM-1"):
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": mac, "device_type": "c6", "firmware_version": "2.1.0", "classroom_code": room_code})
    assert r.status_code == 200, r.text
    return r.json()["device_id"]


@pytest.fixture
def clock(monkeypatch):
    """Set the time the deployment engine and the preview see."""
    import app.routers.deployments as route
    import app.services.deployments as engine

    def set_to(when):
        monkeypatch.setattr(engine, "istnow", lambda: when)
        monkeypatch.setattr(route, "istnow", lambda: when)
    return set_to


def _artifact(client, h):
    return client.get("/api/admin/firmware", headers=h).json()[0]["id"]


def _deploy(client, h, ids, **strategy):
    return client.post("/api/admin/deployments", headers=h, json={
        "artifact_id": _artifact(client, h), "device_ids": ids, "strategy": strategy})


def _targets(client, h, dep_id):
    return client.get(f"/api/admin/deployments/{dep_id}", headers=h).json()["targets"]


def _advance(db):
    from app.services import deployments
    db(lambda s: deployments.advance_all(s))


# ── the window rule ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("now,free,next_at", [
    (at(7, 0), True, None),             # long before the class
    (at(8, 30), True, None),            # 08:30-08:50 + 10 min buffer ends exactly at 09:00: fits
    (at(8, 31), False, at(10, 10)),     # one minute later it would run into the class
    (at(9, 30), False, at(10, 10)),     # during the class
    (at(10, 5), False, at(10, 10)),     # inside the after-class buffer
    (at(10, 10), True, None),           # after the class and its buffer
])
def test_window_before_during_and_after_a_class(client, h, room, db, now, free, next_at):
    from app.models import EspDevice
    from app.services.maintenance import next_window
    gw = _gateway(client)

    async def ask(s):
        return await next_window(s, await s.get(EspDevice, gw), now, 20, 10)
    until, why = db(ask)
    assert (until is None) == free and until == next_at, why


def test_a_device_without_a_class_is_free(client, h, db):
    from app.models import EspDevice
    from app.services.maintenance import next_window
    gw = _gateway(client, room_code="")

    async def ask(s):
        return await next_window(s, await s.get(EspDevice, gw), at(9, 30), 20, 10)
    assert db(ask) == (None, "")


# ── deployments wait, and re-check before every offer ───────────────────────

def test_a_deployment_during_class_is_deferred_then_offered(client, h, room, db, clock):
    gw = _gateway(client)
    clock(at(9, 30))
    dep = _deploy(client, h, [gw]).json()["deployment"]
    t = _targets(client, h, dep["id"])[0]
    assert t["state"] == "deferred" and t["deferred_until"].startswith("2026-10-12T10:10")
    clock(at(10, 0))
    _advance(db)
    assert _targets(client, h, dep["id"])[0]["state"] == "deferred"     # still inside the buffer
    clock(at(10, 15))
    _advance(db)
    assert _targets(client, h, dep["id"])[0]["state"] == "queued"


def test_a_change_made_after_creation_still_blocks(client, h, room, db, clock):
    """Two rooms; the second gets an extra session after the deployment started."""
    other = make_class(client, h, name="Chem", code="CHM1", classroom_code="RM-2")
    first, second = _gateway(client), _gateway(client, "48:F6:EE:00:00:02", "RM-2")
    clock(at(7, 0))
    dep = _deploy(client, h, [first, second], canary=1, batch_size=1).json()["deployment"]
    assert [t["state"] for t in _targets(client, h, dep["id"])] == ["queued", "waiting"]
    assert client.post(f"/api/classes/{other}/exceptions", headers=h, json={
        "kind": "extra", "date": "2026-10-12", "new_start": "07:30", "new_end": "08:30"}).status_code == 201
    client.post("/api/device/ota/status", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:01", "state": "success", "version": "2.2.0"})
    clock(at(7, 10))
    _advance(db)
    assert [t["state"] for t in _targets(client, h, dep["id"])][1] == "deferred"


def test_a_live_quiz_or_activated_class_defers(client, h, room, db, clock):
    gw = _gateway(client)
    assert client.post(f"/api/classes/{room}/activate", headers=h).status_code == 200
    clock(at(7, 0))
    t = _targets(client, h, _deploy(client, h, [gw]).json()["deployment"]["id"])[0]
    assert t["state"] == "deferred" and "in session" in t["error"]


def test_stale_timetable_fails_closed(client, h, room, db, clock):
    async def stale(s):
        await s.execute(text("INSERT INTO schedule_sources (source, last_synced_at, note) "
                             "VALUES ('auris', '2026-10-01 00:00:00', '')"))
    db(stale)
    gw = _gateway(client)
    clock(at(7, 0))
    t = _targets(client, h, _deploy(client, h, [gw]).json()["deployment"]["id"])[0]
    assert t["state"] == "deferred" and "fail closed" in t["error"]


def test_preview_shows_the_next_window(client, h, room, clock):
    gw = _gateway(client)
    clock(at(9, 30))
    r = client.post("/api/admin/deployments?dry_run=true", headers=h, json={
        "artifact_id": _artifact(client, h), "device_ids": [gw]}).json()
    w = r["included"][0]["window"]
    assert w["now"] is False and w["next_at"].startswith("2026-10-12T10:10") and "room busy" in w["reason"]


def test_only_a_super_admin_overrides_the_schedule(client, h, room, clock):
    gw = _gateway(client)
    _, adm = make_user(client, h, "adm1", role="admin")
    clock(at(9, 30))
    assert _deploy(client, adm, [gw], ignore_schedule=True).status_code == 403
    dep = _deploy(client, h, [gw], ignore_schedule=True).json()["deployment"]
    assert _targets(client, h, dep["id"])[0]["state"] == "queued"


def test_deferred_targets_can_be_cancelled(client, h, room, clock):
    gw = _gateway(client)
    clock(at(9, 30))
    dep = _deploy(client, h, [gw]).json()["deployment"]
    assert client.post(f"/api/admin/deployments/{dep['id']}/cancel", headers=h).status_code == 200
    assert _targets(client, h, dep["id"])[0]["state"] == "cancelled"
