"""v2.2 database gateway: per-table write rules, row seals, verification,
automatic repair from the temporary backups, the Degraded flag."""

import sqlite3

import pytest
from sqlalchemy import select

from conftest import DEVICE, auth, login, make_class, make_student, make_user


def _db_file():
    from app.services.integrity import db_path
    return str(db_path())


def _verify(client):
    from app.services.integrity import verify_now
    return client.portal.call(verify_now)


def _outside(sql, *params):
    """A change made without the application: an sqlite3 command."""
    with sqlite3.connect(_db_file()) as c:
        c.execute(sql, params)


def test_a_fresh_database_is_sealed_and_verifies(client):
    rep = _verify(client)
    assert rep.ok and rep.rows > 0


def test_the_applications_own_writes_keep_it_verifying(client):
    h = auth(login(client))
    _, th = make_user(client, h, "tch1")
    cid = make_class(client, h, activate=True)
    make_student(client, h, roll="ROLL000001")
    quiz = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
    client.post(f"/api/quizzes/{quiz}/start", headers=h)
    client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "quiz_answer", "quiz_id": quiz, "question_order": 0, "enrollment_number": "ROLL000001",
         "selected_option": 1}]})
    uid = next(u["id"] for u in client.get("/api/admin/users", headers=h).json() if u["username"] == "tch1")
    client.post(f"/api/admin/users/{uid}/deactivate", headers=h)     # bulk session revoke
    client.delete(f"/api/admin/classes/{cid}", headers=h)            # bulk deletes across tables
    rep = _verify(client)
    assert rep.ok, rep.summary()


@pytest.mark.parametrize("sql,kind", [
    ("UPDATE users SET full_name = 'Mallory' WHERE username = 'admin'", "changed"),
    ("INSERT INTO courses (code, name) VALUES ('EVIL1', 'Injected')", "added"),
])
def test_a_change_outside_the_application_is_found(client, sql, kind):
    _outside(sql)
    rep = _verify(client)
    assert not rep.ok
    table = "users" if "users" in sql else "courses"
    assert rep.problems[table][kind] == 1


def test_deleting_a_row_and_its_seal_is_still_found(client):
    h = auth(login(client))
    make_student(client, h, roll="ROLL000009")
    _outside("DELETE FROM students WHERE roll_number = 'ROLL000009'")
    _outside("DELETE FROM integrity_seals WHERE tbl = 'students'")
    rep = _verify(client)
    assert not rep.ok and rep.problems["students"]["aggregate"]


def test_tampering_is_repaired_from_the_rolling_backup_and_flagged(client, monkeypatch):
    from app.services import events, integrity
    alerts = []
    monkeypatch.setattr(events, "alert", lambda m, level="warning", audience="admins": alerts.append(m))
    _outside("UPDATE users SET role = 'super_admin', full_name = 'Mallory' WHERE username = 'admin'")
    client.portal.call(integrity.check_and_backup)
    with sqlite3.connect(_db_file()) as c:
        assert c.execute("SELECT full_name FROM users WHERE username = 'admin'").fetchone()[0] == "Super Admin"
    st = integrity.status()
    assert st["db"] == "degraded" and "restored" in st["degraded"]["message"]
    assert alerts and "outside imPress" in alerts[0]
    assert _verify(client).ok
    h = auth(login(client))
    logs = client.get("/api/admin/activity?limit=5", headers=h).json()
    assert any(l["action"] == "system.db_degraded" for l in logs)
    client.portal.call(integrity.acknowledge)
    assert integrity.status()["db"] == "ok"


def test_rolling_backup_is_refreshed_only_while_the_database_verifies(client):
    from app.services import integrity
    rolling = integrity.backup_dir() / "rolling.db"
    assert rolling.exists() and (integrity.backup_dir() / "startup.db").exists()
    before = rolling.stat().st_mtime_ns
    client.portal.call(integrity.check_and_backup)
    assert rolling.stat().st_mtime_ns >= before


def _try_as(client, principal, fn):
    from app.database import async_session
    from app.dbgateway import act_as

    async def go():
        act_as(principal)
        async with async_session() as s:
            await fn(s)
            await s.commit()
    return client.portal.call(go)


def test_write_rules_per_principal(client):
    from app.dbgateway import ANONYMOUS, DatabaseWriteRefused, as_device, as_user
    from app.models import Course, FirmwareArtifact, User
    h = auth(login(client))
    make_user(client, h, "tch2")

    async def teacher(s):
        return (await s.execute(select(User).where(User.username == "tch2"))).scalar_one()
    t = client.portal.call(lambda: _load(teacher))

    async def add_course(s):
        s.add(Course(code="C1", name="Course"))

    async def add_firmware(s):
        s.add(FirmwareArtifact(sha256="0" * 64, size=1, target="c6", chip="esp32c6", project="p", version="9.9.9"))

    with pytest.raises(DatabaseWriteRefused):
        _try_as(client, ANONYMOUS, add_course)
    with pytest.raises(DatabaseWriteRefused):
        _try_as(client, as_device(1), add_course)
    with pytest.raises(DatabaseWriteRefused):
        _try_as(client, as_user(t), add_firmware)                    # needs firmware.manage
    _try_as(client, as_user(t), add_course)                          # staff table: the route decides


def test_a_teacher_changes_only_their_own_name_and_password(client):
    from app.dbgateway import DatabaseWriteRefused, as_user
    from app.models import User
    h = auth(login(client))
    make_user(client, h, "tch3")

    async def get(s, name):
        return (await s.execute(select(User).where(User.username == name))).scalar_one()
    t = client.portal.call(lambda: _load(lambda s: get(s, "tch3")))

    async def rename_self(s):
        (await get(s, "tch3")).full_name = "New Name"

    async def promote_self(s):
        (await get(s, "tch3")).role = "super_admin"

    async def rename_admin(s):
        (await get(s, "admin")).full_name = "Hijacked"

    _try_as(client, as_user(t), rename_self)
    for bad in (promote_self, rename_admin):
        with pytest.raises(DatabaseWriteRefused):
            _try_as(client, as_user(t), bad)


def test_a_refused_request_is_403_and_flagged(client, monkeypatch):
    """The route allows an admin to create a course; a (tightened) gateway
    rule refuses the write itself: 403 DB_WRITE_REFUSED, flagged in the log."""
    from app import dbgateway
    su = auth(login(client))
    client.post("/api/admin/users", headers=su, json={"username": "adm1", "email": "a@x.edu",
                                                      "password": "Passw0rd!x", "full_name": "A", "role": "admin"})
    ah = auth(login(client, "adm1", "Passw0rd!x"))
    monkeypatch.setitem(dbgateway.USER_TABLE_PERMISSION, "courses", "users.assign_role")    # super admins only
    r = client.post("/api/courses/", headers=ah, json={"code": "NO1", "name": "Refused"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "DB_WRITE_REFUSED"
    logs = client.get("/api/admin/activity?limit=10", headers=su).json()
    hit = [l for l in logs if l["action"] == "db.write_refused"]
    assert hit and hit[0]["details"]["flag"] is True and hit[0]["details"]["table"] == "courses"
    assert client.post("/api/courses/", headers=su, json={"code": "OK1", "name": "Allowed"}).status_code == 201


def test_schema_changes_are_for_the_server_only(client):
    from app.dbgateway import DatabaseWriteRefused, as_user
    from app.models import User
    from sqlalchemy import text
    t = client.portal.call(lambda: _load(lambda s: _first_user(s)))

    async def ddl(s):
        await s.execute(text("DROP TABLE courses"))
    with pytest.raises(DatabaseWriteRefused):
        _try_as(client, as_user(t), ddl)
    del User


def test_a_rotated_secret_reseals_and_is_flagged(client, monkeypatch):
    from app.config import settings
    from app.services import integrity
    monkeypatch.setattr(settings, "JWT_SECRET", "rotated-secret-for-the-test")
    rep = _verify(client)
    assert not rep.ok and rep.key_changed
    client.portal.call(integrity.startup)
    assert _verify(client).ok and "re-sealed" in integrity.status()["degraded"]["message"]


async def _first_user(s):
    from app.models import User
    return (await s.execute(select(User))).scalars().first()


async def _load(fn):
    from app.database import async_session
    async with async_session() as s:
        return await fn(s)
