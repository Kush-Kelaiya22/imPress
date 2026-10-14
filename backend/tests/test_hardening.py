"""v2.2 hardening: dual control, the policy view, the external audit trail, forensic copies,
test-data gates and expiry, signed exports and the signed code manifest."""

import io
import json
import time
import zipfile

import pytest

from conftest import approved, auth, login, make_class, make_student, make_user

CLEAR = {"scope": "class_data", "confirm": "DELETE CLASS DATA"}


def _two_super_admins(client):
    su = auth(login(client))
    _, boss = make_user(client, su, "boss2", role="super_admin")
    return su, boss


# ── dual control ────────────────────────────────────────────────────────

def test_a_dangerous_action_needs_an_approval(client):
    su = auth(login(client))
    r = client.post("/api/admin/system/clear", headers=su, json=CLEAR)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "APPROVAL_REQUIRED"
    r = client.post("/api/admin/system/integrity/acknowledge", headers=su, json={"accept_current": True})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "APPROVAL_REQUIRED"
    # plain acknowledgement of a Degraded flag needs no approval
    assert client.post("/api/admin/system/integrity/acknowledge", headers=su, json={}).status_code == 200


def test_only_a_different_super_admin_can_approve_when_there_are_two(client):
    su, boss = _two_super_admins(client)
    aid = client.post("/api/admin/approvals", headers=su, json={"action": "system.clear.class_data", "password": "admin123"}).json()["id"]
    r = client.post(f"/api/admin/approvals/{aid}/approve", headers=su, json={"password": "admin123"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SELF_APPROVAL"
    r = client.post(f"/api/admin/approvals/{aid}/approve", headers=boss, json={"password": "wrong"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "STEP_UP_FAILED"
    assert client.post(f"/api/admin/approvals/{aid}/approve", headers=boss, json={"password": "Passw0rd!x"}).status_code == 200
    # only the requester runs it, and only once
    assert client.post("/api/admin/system/clear", headers=boss, json={**CLEAR, "approval_id": aid}).status_code == 403
    assert client.post("/api/admin/system/clear", headers=su, json={**CLEAR, "approval_id": aid}).status_code == 200
    r = client.post("/api/admin/system/clear", headers=su, json={**CLEAR, "approval_id": aid})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "NOT_APPROVED"            # spent


def test_an_approval_is_for_one_action_only(client):
    su = auth(login(client))
    aid = approved(client, su, "system.clear.class_data")
    r = client.post("/api/admin/system/clear", headers=su,
                    json={"scope": "everything", "confirm": "RESET EVERYTHING", "approval_id": aid})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "APPROVAL_MISMATCH"
    r = client.post("/api/admin/system/integrity/acknowledge", headers=su, json={"accept_current": True, "approval_id": aid})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "APPROVAL_MISMATCH"


def test_step_up_locks_after_repeated_wrong_passwords(client):
    su = auth(login(client))
    for _ in range(5):
        assert client.post("/api/admin/approvals", headers=su,
                           json={"action": "system.clear.class_data", "password": "nope"}).status_code == 403
    r = client.post("/api/admin/approvals", headers=su, json={"action": "system.clear.class_data", "password": "admin123"})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "STEP_UP_LOCKED"


def test_the_delay_and_the_expiry_are_enforced(client, policy):
    policy({"dual_control.delay_minutes": 10})
    su = auth(login(client))
    aid = approved(client, su, "system.clear.class_data")
    r = client.post("/api/admin/system/clear", headers=su, json={**CLEAR, "approval_id": aid})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "NOT_YET"
    from datetime import timedelta
    from sqlalchemy import update
    from app.database import async_session
    from app.models import Approval
    from app.timeutil import istnow

    async def age():
        async with async_session() as db:
            await db.execute(update(Approval).where(Approval.id == aid).values(
                not_before=istnow() - timedelta(minutes=90), expires_at=istnow() - timedelta(minutes=30)))
            await db.commit()
    client.portal.call(age)
    r = client.post("/api/admin/system/clear", headers=su, json={**CLEAR, "approval_id": aid})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "EXPIRED"


def test_the_hardened_policy_refuses_a_lone_super_admin_approving_themselves(client, policy):
    policy({"dual_control.single_operator_ok": False})
    su = auth(login(client))
    aid = client.post("/api/admin/approvals", headers=su, json={"action": "system.clear.class_data", "password": "admin123"}).json()["id"]
    r = client.post(f"/api/admin/approvals/{aid}/approve", headers=su, json={"password": "admin123"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SELF_APPROVAL"


def test_root_can_switch_dual_control_and_the_full_reset_off(client, policy):
    su = auth(login(client))
    policy({"dual_control.enabled": False})
    assert client.post("/api/admin/system/clear", headers=su, json=CLEAR).status_code == 200
    policy({"dual_control.enabled": True, "system.reset_everything_allowed": False})
    assert "everything" not in client.get("/api/admin/system/clear", headers=su).json()["scopes"]
    r = client.post("/api/admin/approvals", headers=su, json={"action": "system.clear.everything", "password": "admin123"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "POLICY_DISABLED"
    r = client.post("/api/admin/system/clear", headers=su,
                    json={"scope": "everything", "confirm": "RESET EVERYTHING", "approval_id": 1})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "POLICY_DISABLED"


def test_approvals_are_for_super_admins_only(client):
    su = auth(login(client))
    _, admin = make_user(client, su, "adm1", role="admin")
    _, teacher = make_user(client, su, "tch1")
    for h in (admin, teacher):
        assert client.get("/api/admin/approvals", headers=h).status_code == 403
        assert client.post("/api/admin/approvals", headers=h, json={"action": "system.clear.class_data", "password": "x"}).status_code == 403
        assert client.post("/api/admin/approvals/1/approve", headers=h, json={"password": "x"}).status_code == 403
        assert client.post("/api/admin/approvals/1/deny", headers=h).status_code == 403
    assert client.get("/api/admin/approvals").status_code == 401


def test_a_reset_keeps_recent_audit_entries(client, policy):
    policy({"audit.min_retention_days": 180})
    su = auth(login(client))
    make_user(client, su, "tch2")
    aid = approved(client, su, "system.clear.everything")
    assert client.post("/api/admin/system/clear", headers=su,
                       json={"scope": "everything", "confirm": "RESET EVERYTHING", "approval_id": aid}).status_code == 200
    log = client.get("/api/admin/activity?limit=200", headers=su).json()
    actions = {e["action"] for e in log}
    assert {"approval.request", "approval.approve", "approval.execute", "system.clear_everything"} <= actions
    assert all(e["user_id"] in (None, 1) for e in log)                        # deleted accounts are not referenced


# ── policy view ─────────────────────────────────────────────────────────

def test_the_policy_is_visible_and_cannot_be_written(client):
    su = auth(login(client))
    p = client.get("/api/admin/system/policy", headers=su).json()
    assert p["profile"] == "standard" and {f["name"] for f in p["flags"]} >= {"dual_control.enabled", "test_mode.allowed"}
    _, teacher = make_user(client, su, "tch3")
    assert client.get("/api/admin/system/policy", headers=teacher).status_code == 403
    for method in ("post", "put", "patch", "delete"):
        assert getattr(client, method)("/api/admin/system/policy", headers=su).status_code in (404, 405)


def test_the_signing_key_is_public_and_only_the_public_half(client):
    k = client.get("/api/system/signing-key").json()
    assert k["alg"] == "ed25519" and len(k["key_id"]) == 16 and len(__import__("base64").b64decode(k["public_key"])) == 32
    assert "private" not in json.dumps(k).lower() and "seed" not in k


# ── external audit trail ────────────────────────────────────────────────

def test_the_audit_sink_is_a_verifiable_hash_chain(client, policy, tmp_path):
    from app.services import auditsink
    sink = tmp_path / "audit" / "chain.jsonl"
    policy({"audit.sink_path": str(sink)})
    su = auth(login(client))
    make_user(client, su, "tch4")
    make_class(client, su)
    lines = sink.read_text().splitlines()
    assert len(lines) >= 2 and json.loads(lines[0])["prev"] == "0" * 64
    assert auditsink.verify_file(sink) == []
    assert oct(sink.stat().st_mode & 0o777) == "0o600"
    # edit one line, drop another, truncate: each is found
    edited = [json.loads(l) for l in lines]
    edited[0]["details"] = {"forged": True}
    forged = tmp_path / "forged.jsonl"
    forged.write_text("\n".join(json.dumps(e) for e in edited) + "\n")
    assert any("edited" in p for p in auditsink.verify_file(forged))
    dropped = tmp_path / "dropped.jsonl"
    dropped.write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    assert auditsink.verify_file(dropped)
    reordered = tmp_path / "reordered.jsonl"
    reordered.write_text("\n".join([lines[1], lines[0]] + lines[2:]) + "\n")
    assert auditsink.verify_file(reordered)


def test_the_sink_resumes_the_chain_after_a_restart(client, policy, tmp_path):
    from app.services import auditsink
    sink = tmp_path / "chain.jsonl"
    policy({"audit.sink_path": str(sink)})
    su = auth(login(client))
    make_user(client, su, "tch5")
    auditsink._head.clear()                              # a new process: reads the last line
    make_user(client, su, "tch6")
    assert auditsink.verify_file(sink) == []


def test_the_manage_command_verifies_a_chain(tmp_path):
    from app.services import auditsink
    sink = tmp_path / "c.jsonl"
    auditsink._append(sink, {"ts": "t", "action": "a", "user_id": None, "entity_type": "", "entity_id": None, "details": {}})
    auditsink._append(sink, {"ts": "t", "action": "b", "user_id": None, "entity_type": "", "entity_id": None, "details": {}})
    assert auditsink.verify_file(sink) == []
    sink.write_text(sink.read_text().replace('"action": "a"', '"action": "x"'))
    assert auditsink.verify_file(sink)


# ── forensic copy ───────────────────────────────────────────────────────

def test_a_failed_database_is_kept_before_it_is_replaced(client):
    import sqlite3
    from app.services import integrity
    su = auth(login(client))
    make_user(client, su, "tch7")
    client.portal.call(integrity.check_and_backup)
    db = integrity.db_path()
    with sqlite3.connect(db) as c:
        c.execute("UPDATE users SET full_name = 'Forged' WHERE username = 'admin'")
    client.portal.call(integrity.check_and_backup)                        # detects, keeps, restores
    kept = sorted(integrity.backup_dir().glob("forensic-*.db"))
    assert len(kept) == 1 and oct(kept[0].stat().st_mode & 0o777) == "0o600"
    with sqlite3.connect(kept[0]) as c:
        assert c.execute("SELECT full_name FROM users WHERE username = 'admin'").fetchone()[0] == "Forged"
    msg = integrity.status()["degraded"]["message"]
    assert "min ago" in msg and "lost" in msg and kept[0].name in msg
    assert any(b["kind"] == "forensic" for b in integrity.backups_info())


def test_old_forensic_copies_are_pruned(client, policy):
    from app.services import integrity
    policy({"integrity.forensic_copies": 2})
    for i in range(4):
        (integrity.backup_dir() / f"forensic-20260101-00000{i}.db").write_bytes(b"x")
    client.portal.call(integrity.keep_forensic_copy)
    assert len(list(integrity.backup_dir().glob("forensic-*.db"))) == 2


# ── test mode gates, expiry, permissions, signed exports ────────────────

def test_policy_can_switch_test_mode_and_exports_off(client, policy):
    su = auth(login(client))
    policy({"test_mode.allowed": False})
    r = client.post("/api/admin/test-mode/enable", headers=su, json={})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "POLICY_DISABLED"
    policy({"test_mode.allowed": True})
    assert client.post("/api/admin/test-mode/enable", headers=su, json={}).status_code == 200
    policy({"test_mode.allowed": False})
    assert client.post("/api/admin/test-data/generate", headers=su, json={"seed": 1}).status_code == 403
    policy({"test_mode.allowed": True})
    client.post("/api/admin/test-mode/disable", headers=su)
    pending = client.get("/api/admin/test-mode", headers=su).json()["pending"][0]["id"]
    policy({"test_mode.export_allowed": False})
    assert client.get(f"/api/admin/test-mode/pending/{pending}/export.zip", headers=su).status_code == 403
    # leaving test data behind is always possible, whatever the policy
    policy({"test_mode.allowed": False})
    assert client.post(f"/api/admin/test-mode/pending/{pending}", headers=su, json={"action": "delete"}).status_code == 200


def test_expired_test_data_is_deleted_and_directories_are_private(client, policy):
    from app.services import test_mode
    su = auth(login(client))
    client.post("/api/admin/test-mode/enable", headers=su, json={})
    client.post("/api/admin/test-mode/disable", headers=su)
    root = test_mode._root()
    for d in (root, root / "snapshots", root / "pending", root / "datasets"):
        assert oct(d.stat().st_mode & 0o777) == "0o700", d
    pend = next((root / "pending").glob("*.db"))
    assert oct(pend.stat().st_mode & 0o777) == "0o600"
    policy({"test_mode.pending_ttl_hours": 24})
    assert test_mode.sweep_expired() == []                                       # fresh
    assert test_mode.sweep_expired(now=time.time() + 25 * 3600) == [f"pending/{pend.stem}"] and not pend.exists()
    policy({"test_mode.pending_ttl_hours": 0, "test_mode.dataset_ttl_days": 0})
    assert test_mode.sweep_expired(now=time.time() + 10**9) == []                # 0 = keep


def test_test_data_actions_are_audited_and_exports_are_signed(client):
    from app import ed25519, signing
    su = auth(login(client))
    client.post("/api/admin/test-mode/enable", headers=su, json={})
    client.post("/api/admin/test-mode/disable", headers=su)
    pid = client.get("/api/admin/test-mode", headers=su).json()["pending"][0]["id"]
    r = client.get(f"/api/admin/test-mode/pending/{pid}/export.zip", headers=su)
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    files = {n: z.read(n) for n in z.namelist() if n != "SIGNATURE.json"}
    pub = __import__("base64").b64decode(client.get("/api/system/signing-key").json()["public_key"])
    assert signing.verify_files(z.read("SIGNATURE.json"), files, pub) == []
    files["students.csv"] += b"x"
    assert any("changed: students.csv" in p for p in signing.verify_files(z.read("SIGNATURE.json"), files, pub))
    assert signing.verify_files(z.read("SIGNATURE.json"), {k: v for k, v in files.items() if k != "teachers.csv"}, pub)
    assert signing.verify_files(z.read("SIGNATURE.json"), files, ed25519.public_key(bytes(32)))      # another key
    assert oct(signing._key_path().stat().st_mode & 0o777) == "0o600"
    assert "system.test_data_export" in {e["action"] for e in client.get("/api/admin/activity?limit=100", headers=su).json()}


# ── signed code manifest ────────────────────────────────────────────────

def test_the_code_manifest_detects_every_kind_of_change(tmp_path):
    from app import ed25519, signing
    code = tmp_path / "app"
    (code / "static").mkdir(parents=True)
    (code / "main.py").write_text("print('hi')\n")
    (code / "static" / "app.js").write_text("1\n")
    (code / "__pycache__").mkdir()
    (code / "__pycache__" / "x.pyc").write_bytes(b"noise")
    seed = ed25519.generate_seed()
    signing.write_manifest(seed, code, "2.2.0")
    pub = ed25519.public_key(seed)
    assert signing.verify_manifest(pub, code) == []
    (code / "main.py").write_text("print('evil')\n")
    assert signing.verify_manifest(pub, code) == ["changed: main.py"]
    (code / "main.py").write_text("print('hi')\n")
    (code / "extra.py").write_text("x")
    assert signing.verify_manifest(pub, code) == ["not in the manifest: extra.py"]
    (code / "extra.py").unlink()
    (code / "static" / "app.js").unlink()
    assert signing.verify_manifest(pub, code) == ["missing: static/app.js"]
    (code / "static" / "app.js").write_text("1\n")
    assert signing.verify_manifest(ed25519.public_key(bytes(32)), code)                          # another key
    (code / "MANIFEST.json").write_text((code / "MANIFEST.json").read_text().replace("2.2.0", "9.9.9"))
    assert "signature" in signing.verify_manifest(pub, code)[0]                                   # manifest edited
    (code / "MANIFEST.sig").unlink()
    assert "missing" in signing.verify_manifest(pub, code)[0]


# ── start-up in the hardened profile ─────────────────────────────────────

def test_the_hardened_profile_will_not_start_below_its_floor(tmp_path, monkeypatch):
    """A server started with PROFILE=hardened and the lab settings of the test suite is refused, with reasons."""
    import asyncio

    from app import gpc
    from app.config import settings
    from app.main import app, lifespan

    monkeypatch.setattr(settings, "PROFILE", "hardened")

    async def start():
        async with lifespan(app):
            pass
    try:
        with pytest.raises(RuntimeError) as err:
            asyncio.run(start())
    finally:
        monkeypatch.setattr(settings, "PROFILE", "standard")
        gpc.load(settings)
    msg = str(err.value)
    assert "hardened profile" in msg and "audit sink" in msg and "ALLOW_UNSIGNED" in msg


def test_a_bad_policy_file_stops_a_hardened_start_and_only_warns_a_standard_one(tmp_path, monkeypatch):
    import asyncio

    from app import gpc
    from app.config import settings
    from app.main import app, lifespan

    bad = tmp_path / "gpc.json"
    bad.write_text("{not json")
    monkeypatch.setattr(settings, "GPC_FILE", str(bad))
    monkeypatch.setattr(settings, "PROFILE", "hardened")

    async def start():
        async with lifespan(app):
            pass
    try:
        with pytest.raises(RuntimeError, match="Global policy"):
            asyncio.run(start())
    finally:
        monkeypatch.setattr(settings, "PROFILE", "standard")
        monkeypatch.setattr(settings, "GPC_FILE", "")
        gpc.load(settings)


# ── erasure and the audit trail ──────────────────────────────────────────

def test_erasing_a_student_leaves_no_name_or_number_in_the_log_or_the_sink(client, policy, tmp_path):
    from app.services.records import student_ref
    sink = tmp_path / "chain.jsonl"
    policy({"audit.sink_path": str(sink)})
    su = auth(login(client))
    cid = make_class(client, su)
    sid = make_student(client, su, roll="ERASE00001", name="Erin Asure")
    assert client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": sid}).status_code in (200, 201)
    assert "Erin Asure" in client.get("/api/admin/activity?limit=100", headers=su).text      # logged while the record exists
    assert client.delete(f"/api/students/{sid}/hard-delete", headers=su).status_code == 200
    log = client.get("/api/admin/activity?limit=200", headers=su).text
    assert "Erin Asure" not in log and "ERASE00001" not in log
    assert student_ref("ERASE00001") in log
    assert "Erin Asure" not in sink.read_text() and "ERASE00001" not in sink.read_text()
    from app.services import auditsink
    assert auditsink.verify_file(sink) == []


def test_copies_taken_before_a_clear_expire(client, policy):
    from app.services import integrity
    su = auth(login(client))
    aid = approved(client, su, "system.clear.class_data")
    backup = client.post("/api/admin/system/clear", headers=su, json={**CLEAR, "approval_id": aid}).json()["backup"]
    path = integrity.backup_dir() / backup
    assert integrity.sweep_old_copies() == [] and path.exists()
    assert integrity.sweep_old_copies(now=time.time() + 15 * 86400) == []             # standard keeps 30 days
    assert integrity.sweep_old_copies(now=time.time() + 31 * 86400) == [backup] and not path.exists()
    policy({"integrity.before_clear_days": 0})
    assert integrity.sweep_old_copies(now=time.time() + 10**9) == []                 # 0 = keep


def test_old_activity_is_purged_by_policy_and_never_before_the_minimum(client, policy):
    from datetime import timedelta
    from sqlalchemy import select, update
    from app.database import async_session
    from app.models import ActivityLog
    from app.services import housekeeping
    from app.timeutil import istnow
    su = auth(login(client))
    make_user(client, su, "tch9")

    async def age_all(days):
        async with async_session() as db:
            await db.execute(update(ActivityLog).values(timestamp=istnow() - timedelta(days=days)))
            await db.commit()

    async def count():
        async with async_session() as db:
            return len((await db.execute(select(ActivityLog))).scalars().all())
    client.portal.call(age_all, 100)
    assert client.portal.call(housekeeping.purge_activity) == 0                      # 0 = never (standard)
    policy({"audit.purge_days": 30, "audit.min_retention_days": 180})
    assert client.portal.call(housekeeping.purge_activity) == 0 and client.portal.call(count) > 0   # not sooner than 180 days
    policy({"audit.min_retention_days": 0})
    purged = client.portal.call(housekeeping.purge_activity)
    assert purged > 0 and client.portal.call(count) == 1                             # only the purge's own entry is left


def test_deleting_an_account_settles_its_approvals(client):
    su, boss = _two_super_admins(client)
    aid = client.post("/api/admin/approvals", headers=su, json={"action": "system.clear.class_data", "password": "admin123"}).json()["id"]
    client.post(f"/api/admin/approvals/{aid}/approve", headers=boss, json={"password": "Passw0rd!x"})
    boss_id = next(u["id"] for u in client.get("/api/admin/users", headers=su).json() if u["username"] == "boss2")
    assert client.delete(f"/api/admin/users/{boss_id}", headers=su).status_code == 204
    rows = client.get("/api/admin/approvals", headers=su).json()["requests"]
    assert rows[0]["status"] == "approved" and rows[0]["approved_by"] is None                 # the approver is gone, the request stays
    log = client.get("/api/admin/activity?limit=100", headers=su).json()
    assert any(e["action"] == "approval.approve" for e in log)                                 # the trail still says what happened
