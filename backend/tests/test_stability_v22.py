"""Start-up and run-time stability: the integrity check never raises a false alarm while the server writes, a normal
start never keeps a leftover forced test mode, test mode makes no backups, and an update is not tampering."""

import asyncio

import pytest

from conftest import auth, login


def test_integrity_check_sees_one_snapshot_while_requests_commit(client):
    """Before: every SELECT of the check saw a different moment, so a commit in the middle looked like a change made
    outside imPress (a false alarm, then an unwanted restore of an older backup)."""
    from app.database import async_session
    from app.dbgateway import SYSTEM, act_as
    from app.models import ActivityLog
    from app.services import integrity
    from app.timeutil import istnow

    async def go():
        act_as(SYSTEM)
        stop = asyncio.Event()

        async def writer():
            n = 0
            while not stop.is_set():
                async with async_session() as db:
                    db.add(ActivityLog(action="stress.write", entity_type="x", details={"n": n}, timestamp=istnow()))
                    await db.commit()
                n += 1
                await asyncio.sleep(0)

        tasks = [asyncio.create_task(writer()) for _ in range(3)]
        try:
            return [(await integrity.verify_now()).summary() for _ in range(25) if not (await integrity.verify_now()).ok]
        finally:
            stop.set()
            await asyncio.gather(*tasks)
    assert client.portal.call(go) == []


def test_the_database_runs_in_wal_mode(client, db):
    from sqlalchemy import text

    async def mode(s):
        return (await s.execute(text("PRAGMA journal_mode"))).scalar()
    assert db(mode) == "wal"


def test_a_leftover_forced_test_mode_ends_at_a_normal_start(client):
    from app import gpc
    from app.services import integrity, test_mode
    client.portal.call(test_mode.enable, None, None, None)            # what `--test-mode` does at start-up
    assert test_mode.state()["on"] and (integrity.read_state()["test_mode"])["forced"] is True
    saved = gpc.current().values["test_mode.forced"]
    gpc.current().values["test_mode.forced"] = False                  # the next start has no --test-mode
    try:
        assert client.portal.call(test_mode.release_leftover_forced) is True
    finally:
        gpc.current().values["test_mode.forced"] = saved
    assert test_mode.state()["on"] is False
    assert client.get("/api/system/status").json()["test_mode"] is False
    assert test_mode.state()["pending"], "the test data is kept for the super admin to save or delete"


def test_a_test_mode_a_super_admin_chose_survives_a_restart(client):
    from app.services import test_mode
    h = auth(login(client))
    assert client.post("/api/admin/test-mode/enable", headers=h, json={}).json()["on"] is True
    assert client.portal.call(test_mode.release_leftover_forced) is False
    assert test_mode.state()["on"] is True


def test_test_mode_makes_and_restores_no_backups(client):
    from app.services import backups, integrity
    h = auth(login(client))
    startup = integrity.backup_dir() / "startup.db"
    before = startup.stat().st_mtime_ns if startup.exists() else None
    assert client.post("/api/admin/test-mode/enable", headers=h, json={}).json()["on"] is True
    assert integrity.backups_suspended()
    r = client.post("/api/admin/backups", headers=h, json={"name": "during test mode"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "TEST_MODE"
    client.portal.call(integrity.check_and_backup)                     # the periodic check: verifies, copies nothing
    assert (startup.stat().st_mtime_ns if startup.exists() else None) == before
    with pytest.raises(backups.BackupError):
        client.portal.call(backups.restore, "startup/startup.db", "test")
    client.post("/api/admin/test-mode/disable", headers=h)
    assert not integrity.backups_suspended()
    assert client.post("/api/admin/backups", headers=h, json={"name": "after test mode"}).status_code == 201


def test_a_changed_test_database_is_flagged_not_restored(client, db):

    from app.services import integrity
    h = auth(login(client))
    client.post("/api/admin/test-mode/enable", headers=h, json={}).json()
    import sqlite3
    path = integrity.db_path()
    with sqlite3.connect(str(path)) as c:                              # a change made outside imPress
        c.execute("UPDATE users SET full_name = 'Edited outside' WHERE id = 1")
    client.portal.call(integrity.check_and_backup)
    assert integrity.status()["degraded"]["restored_from"] is None
    assert not list(integrity.backup_dir().glob("forensic-*.db"))


def test_a_clear_in_test_mode_keeps_no_copy(client):
    from app.services import rootops
    h = auth(login(client))
    client.post("/api/admin/test-mode/enable", headers=h, json={})
    assert client.portal.call(rootops.clear_data, "class_data") == ""


# ── IIPS: an update is not tampering ────────────────────────────────────────

@pytest.fixture
def tree(tmp_path, monkeypatch):
    from app.services import iips
    root = tmp_path / "src"
    (root / "backend/app").mkdir(parents=True)
    (root / "backend/app/a.py").write_text("a = 1\n")
    (root / "VERSION").write_text("2.2.0\n")
    monkeypatch.setattr(iips, "baseline_path", lambda: tmp_path / "state" / "x.iips.json")
    monkeypatch.setattr(iips, "build_marker", lambda root=None: marker[0])
    marker = ["git:one"]
    return root, marker


def test_an_update_becomes_the_reference_when_the_policy_allows_it(tree):
    from app.services import iips
    root, marker = tree
    assert iips.check(root=root, auto_accept=True)["status"] == "baseline_created"
    (root / "backend/app/a.py").write_text("a = 2\n")
    marker[0] = "git:two"                                              # pulled or checked out another commit
    st = iips.check(root=root, auto_accept=True)
    assert st["status"] == "updated" and "git:two" in st["note"]
    assert iips.check(root=root, auto_accept=True)["status"] == "ok"


def test_files_edited_under_the_same_build_still_lock_it(tree):
    from app.services import iips
    root, _ = tree
    iips.check(root=root, auto_accept=True)
    (root / "backend/app/a.py").write_text("a = 3\n")
    assert iips.check(root=root, auto_accept=True)["status"] == "violation"


def test_without_the_policy_an_update_still_locks(tree):
    from app.services import iips
    root, marker = tree
    iips.check(root=root)
    (root / "backend/app/a.py").write_text("a = 2\n")
    marker[0] = "git:two"
    assert iips.check(root=root)["status"] == "violation"


def test_the_hardened_profile_never_accepts_an_update_by_itself():
    from app import gpc
    assert gpc.FLAGS["iips.auto_accept_updates"].standard is True and gpc.FLAGS["iips.auto_accept_updates"].hardened is False


# ── The database and .env are found from backend/, not from where the server was started ──

def test_the_default_database_and_env_do_not_depend_on_the_working_directory():
    from app.config import BACKEND_DIR, Settings
    default = Settings.model_fields["DATABASE_URL"].default
    assert default.startswith("sqlite+aiosqlite:///") and BACKEND_DIR.as_posix() in default


# ── Disk encryption is checked where it can be seen (D16, #212) ─────────────

def test_volume_encryption_is_read_from_the_platform(monkeypatch, tmp_path):
    import subprocess
    import sys
    from types import SimpleNamespace

    from app.services import boot_verify

    def run_with(outputs):
        def fake(cmd, **kw):
            return SimpleNamespace(stdout=outputs[cmd[0]])
        monkeypatch.setattr(subprocess, "run", fake)

    monkeypatch.setattr(sys, "platform", "darwin")
    run_with({"fdesetup": "FileVault is On.\n"})
    assert boot_verify.volume_encrypted(tmp_path) is True
    run_with({"fdesetup": "FileVault is Off.\n"})
    assert boot_verify.volume_encrypted(tmp_path) is False
    run_with({"fdesetup": "something else"})
    assert boot_verify.volume_encrypted(tmp_path) is None

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(boot_verify, "in_container", lambda: False)
    run_with({"findmnt": "/dev/mapper/data\n", "lsblk": "crypt\npart\ndisk\n"})
    assert boot_verify.volume_encrypted(tmp_path) is True
    run_with({"findmnt": "/dev/sda2\n", "lsblk": "part\ndisk\n"})
    assert boot_verify.volume_encrypted(tmp_path) is False
    run_with({"findmnt": "server:/export\n", "lsblk": ""})
    assert boot_verify.volume_encrypted(tmp_path) is None            # a network volume: cannot tell
    monkeypatch.setattr(boot_verify, "in_container", lambda: True)
    assert boot_verify.volume_encrypted(tmp_path) is None
    monkeypatch.setattr(sys, "platform", "win32")
    assert boot_verify.volume_encrypted(tmp_path) is None
