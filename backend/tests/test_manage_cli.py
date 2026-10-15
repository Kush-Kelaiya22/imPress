"""Offline recovery of a locked-out installation (#120)."""

import pytest
from sqlalchemy import text

from conftest import auth, login, make_user


def _sql(db, sql, **p):
    async def go(s):
        return (await s.execute(text(sql), p)).all() if sql.lstrip().upper().startswith("SELECT") else \
            await s.execute(text(sql), p)
    return db(go)


def _lock_out(db):
    """A database from before #116: no triggers, every super admin inactive."""
    _sql(db, "DROP TRIGGER users_keep_super_admin_update")
    _sql(db, "UPDATE users SET is_active = 0 WHERE role = 'super_admin'")


def _restore(client, username, create=False):
    from app.manage import restore_super_admin
    return client.portal.call(restore_super_admin, username, create)


def test_restores_a_locked_out_installation(client, db):
    old = auth(login(client))
    _lock_out(db)
    assert client.post("/api/auth/login", json={"username": "impress.default.superAdmin", "password": "admin123"}).status_code == 403

    password = _restore(client, "impress.default.superAdmin")

    assert client.get("/api/auth/me", headers=old).status_code == 401        # old sessions revoked
    assert client.get("/api/admin/users", headers=auth(login(client, "impress.default.superAdmin", password))).status_code == 200
    entry = _sql(db, "SELECT user_id, json_extract(details, '$.via') FROM activity_logs WHERE action = 'user.recovery'")
    assert entry == [(None, "cli")]


def test_promotes_an_existing_account(client, db):
    su = auth(login(client))
    make_user(client, su, "tch1")
    password = _restore(client, "tch1")
    me = client.get("/api/auth/me", headers=auth(login(client, "tch1", password))).json()
    assert me["role"] == "super_admin" and me["is_active"]


def test_unknown_user_needs_create(client):
    with pytest.raises(LookupError):
        _restore(client, "nobody")
    password = _restore(client, "rescue", create=True)
    assert login(client, "rescue", password)


def test_cli_exit_codes(client, capsys):
    from app.manage import main
    assert main(["restore-super-admin", "--username", "nobody"]) == 2
    assert "add --create" in capsys.readouterr().err


def test_no_http_route_exposes_recovery(client):
    from app.main import app
    assert not [r for r in app.routes if "restore" in getattr(r, "path", "") or "recover" in getattr(r, "path", "")]
