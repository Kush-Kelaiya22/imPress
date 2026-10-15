"""An upgrade changes the schema (new columns change every row's seal): that is re-sealed, not treated as tampering;
and a backup made by an older version is brought up to date when it is restored."""

import sqlite3

from conftest import _TMP, auth, login

from app import migrations
from app.services import integrity


def _db():
    return str(_TMP / "test.db")


def _outside(sql):
    with sqlite3.connect(_db()) as c:
        c.execute(sql)


def test_a_database_that_changed_during_an_upgrade_is_resealed_not_restored(client, monkeypatch):
    _outside("UPDATE users SET full_name = 'Changed by the upgrade' WHERE username = 'impress.default.superAdmin'")
    monkeypatch.setattr(migrations, "APPLIED_AT_START", [13])
    client.portal.call(integrity.startup)
    assert integrity.status()["db"] == "ok"
    with sqlite3.connect(_db()) as c:
        assert c.execute("SELECT full_name FROM users WHERE username = 'impress.default.superAdmin'").fetchone()[0] == "Changed by the upgrade"
    assert client.portal.call(integrity.verify_now).ok


def test_the_same_change_without_an_upgrade_is_still_tampering(client, monkeypatch):
    monkeypatch.setattr(migrations, "APPLIED_AT_START", [])
    _outside("UPDATE users SET full_name = 'Mallory' WHERE username = 'impress.default.superAdmin'")
    client.portal.call(integrity.startup)
    assert integrity.status()["db"] == "degraded"


def test_a_backup_from_an_older_schema_is_upgraded_when_restored(client, tmp_path):
    old = tmp_path / "old.db"
    client.portal.call(integrity.copy_live_to, old)
    with sqlite3.connect(old) as c:                       # what a v2.1-era copy looks like
        c.execute("DROP TABLE approvals")
        c.execute("DELETE FROM schema_migrations WHERE version >= 13")
    client.portal.call(integrity.restore_from, old)
    with sqlite3.connect(_db()) as c:
        assert c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = 'approvals'").fetchone()[0] == 1
        assert c.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == migrations.LATEST
    assert client.portal.call(integrity.verify_now).ok
    assert client.get("/api/admin/approvals", headers=auth(login(client, password="admin123"))).status_code == 200
