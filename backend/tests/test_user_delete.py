"""DELETE /api/admin/users/{id} removes the account and settles references (#117)."""

import pytest
from sqlalchemy import text

from conftest import PASSWORD, auth, login, make_class, make_student, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


def _rows(db, sql, **p):
    async def go(s):
        return (await s.execute(text(sql), p)).all()
    return db(go)


def _exec(db, sql, **p):
    async def go(s):
        await s.execute(text(sql), p)
    db(go)


def test_every_foreign_key_to_users_has_a_delete_rule():
    """A new column pointing at users.id must decide what deletion does to it."""
    from app.database import Base
    from app.services.accounts import DELETE_RULES
    import app.models  # noqa: F401
    fks = {(t.name, fk.parent.name) for t in Base.metadata.tables.values()
           for fk in t.foreign_keys if fk.column.table.name == "users"}
    assert fks == set(DELETE_RULES)


def test_delete_removes_account_and_keeps_history(client, su, db):
    uid, teacher = make_user(client, su, "tch1")
    co_class = make_class(client, su, name="Chem", code="CHM101")
    _exec(db, "INSERT INTO class_faculty (class_session_id, user_id) VALUES (:c, :u)", c=co_class, u=uid)
    student = make_student(client, teacher, roll="ROLL000001")              # registered_by = tch1
    _exec(db, "INSERT INTO activity_logs (user_id, action, entity_type, details, timestamp) "
              "VALUES (:u, 'quiz.start', 'quiz', '{}', CURRENT_TIMESTAMP)", u=uid)

    assert client.delete(f"/api/admin/users/{uid}", headers=su).status_code == 204

    assert _rows(db, "SELECT id FROM users WHERE id = :u", u=uid) == []
    assert _rows(db, "SELECT id FROM user_sessions WHERE user_id = :u", u=uid) == []
    assert _rows(db, "SELECT user_id FROM class_faculty WHERE user_id = :u", u=uid) == []
    assert _rows(db, "SELECT registered_by FROM students WHERE id = :s", s=student) == [(None,)]
    logs = _rows(db, "SELECT user_id, json_extract(details, '$.deleted_user') FROM activity_logs "
                     "WHERE action = 'quiz.start'")
    assert logs == [(None, "tch1")]
    assert _rows(db, "PRAGMA foreign_key_check") == []
    assert client.get("/api/auth/me", headers=teacher).status_code == 401
    assert client.post("/api/auth/login", json={"username": "tch1", "password": PASSWORD}).status_code == 401


def test_primary_teacher_cannot_be_deleted(client, su, db):
    uid, _ = make_user(client, su, "tch1")
    cid = make_class(client, su, teacher_id=uid)
    r = client.delete(f"/api/admin/users/{uid}", headers=su)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "USER_OWNS_CLASSES"
    assert f"#{cid}" in r.json()["detail"]["message"]
    assert _rows(db, "SELECT id FROM users WHERE id = :u", u=uid) == [(uid,)]


def test_last_super_admin_cannot_be_deleted_by_another_path(client, su):
    other, other_h = make_user(client, su, "root2", role="super_admin")
    me = client.get("/api/auth/me", headers=su).json()["id"]
    assert client.post(f"/api/admin/users/{me}/deactivate", headers=other_h).status_code == 200
    # root2 is now the only active super admin; nobody else can remove it, and it can't remove itself
    assert client.delete(f"/api/admin/users/{other}", headers=other_h).status_code == 403


def test_failed_delete_changes_nothing(client, su, db, monkeypatch):
    uid, teacher = make_user(client, su, "tch1")
    from app.services import accounts
    real = accounts.delete_user

    async def boom(db_, target):
        await real(db_, target)
        raise RuntimeError("injected failure after the delete statements")
    monkeypatch.setattr(accounts, "delete_user", boom)
    with pytest.raises(RuntimeError):
        client.delete(f"/api/admin/users/{uid}", headers=su)
    assert _rows(db, "SELECT id FROM users WHERE id = :u", u=uid) == [(uid,)]
    assert client.get("/api/auth/me", headers=teacher).status_code == 200


def test_deleted_username_can_be_reused(client, su):
    uid, _ = make_user(client, su, "tch1")
    assert client.delete(f"/api/admin/users/{uid}", headers=su).status_code == 204
    make_user(client, su, "tch1")
