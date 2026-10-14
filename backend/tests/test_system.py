"""v2.2 system routes: status, live events, integrity, clearing data."""

import json

from conftest import approved, auth, login, make_class, make_student, make_user


def test_status_is_public(client):
    s = client.get("/api/system/status").json()
    assert s["test_mode"] is False and s["version"]
    assert "db" not in s                      # the integrity state is for administrators only


def test_event_stream_starts_with_the_status_and_needs_a_session(client):
    assert client.get("/api/events").status_code == 401
    tok = login(client)
    from app.models import User
    from app.routers.system import stream_events
    from app.services import events
    from sqlalchemy import select

    async def go():
        from app.database import async_session
        async with async_session() as s:
            user = (await s.execute(select(User).where(User.username == "impress.default.superAdmin"))).scalar_one()

        async def connected():
            return False
        gen = stream_events(tok, user, connected)
        first = await gen.__anext__()
        events.alert("hello admins", "info")
        second = await gen.__anext__()
        await gen.aclose()
        return first, second, events.subscriber_count()
    first, second, left = client.portal.call(go)
    assert json.loads(first[5:])["type"] == "status"
    assert json.loads(second[5:]) == {"type": "alert", "level": "info", "message": "hello admins"}
    assert left == 0                                    # unsubscribed when the stream closes


def test_changes_are_published_as_topics(client):
    from app.services import events
    seen = []
    orig = events._deliver
    events._deliver = lambda e, audience="all": seen.append(e)
    try:
        h = auth(login(client))
        make_student(client, h, roll="ROLL000001")
        client.portal.call(events._flush)
    finally:
        events._deliver = orig
    assert any(e["type"] == "changed" and "students" in e["topics"] for e in seen)


def test_integrity_info_for_administrators(client):
    h = auth(login(client))
    info = client.get("/api/admin/system/integrity", headers=h).json()
    assert info["db"] == "ok" and {b["name"] for b in info["backups"]} >= {"startup.db", "rolling.db"}
    r = client.post("/api/admin/system/integrity/verify", headers=h).json()
    assert r["last_verification"]["ok"] is True


def test_clearing_needs_a_super_admin_and_the_typed_phrase(client):
    su = auth(login(client))
    _, th = make_user(client, su, "tch9")
    assert client.post("/api/admin/system/clear", headers=th, json={"scope": "class_data",
                                                                    "confirm": "DELETE CLASS DATA"}).status_code == 403
    r = client.post("/api/admin/system/clear", headers=su, json={"scope": "class_data", "confirm": "yes"})
    assert r.status_code == 422


def test_clearing_class_data_keeps_accounts_and_verifies(client):
    su = auth(login(client))
    make_user(client, su, "tch8")
    make_class(client, su)
    make_student(client, su, roll="ROLL000002")
    aid = approved(client, su, "system.clear.class_data")
    r = client.post("/api/admin/system/clear", headers=su,
                    json={"scope": "class_data", "confirm": "DELETE CLASS DATA", "approval_id": aid})
    assert r.status_code == 200 and r.json()["backup"].startswith("before-clear-")
    assert client.get("/api/admin/classes", headers=su).json() == []
    assert any(u["username"] == "tch8" for u in client.get("/api/admin/users", headers=su).json())
    from app.services.integrity import backup_dir, verify_now
    assert (backup_dir() / r.json()["backup"]).exists()
    assert client.portal.call(verify_now).ok


def test_reset_everything_keeps_only_the_acting_super_admin(client):
    su = auth(login(client))
    make_user(client, su, "tch7")
    aid = approved(client, su, "system.clear.everything")
    r = client.post("/api/admin/system/clear", headers=su,
                    json={"scope": "everything", "confirm": "RESET EVERYTHING", "approval_id": aid})
    assert r.status_code == 200
    assert [u["username"] for u in client.get("/api/admin/users", headers=su).json()] == ["impress.default.superAdmin"]


def test_the_database_state_is_for_administrators_only(client):
    from app.services import events
    admin_sub, teacher_sub = events.subscribe(True, 1), events.subscribe(False, 2)
    try:
        events.status({"db": "degraded"}, "admins")
        events.status({"test_mode": True})
        got = lambda sub: [json.loads(sub.queue.get_nowait()) for _ in range(sub.queue.qsize())]
        assert [e.get("db") for e in got(admin_sub)] == ["degraded", None]
        assert got(teacher_sub) == [{"type": "status", "test_mode": True}]
    finally:
        events.unsubscribe(admin_sub), events.unsubscribe(teacher_sub)
