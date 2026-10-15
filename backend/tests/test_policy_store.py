"""The sealed policy store, flag conflicts, root's password and device binding."""

import hashlib
import json

import pytest

from app import fingerprint, gpc, gpcstore, rootauth
from conftest import auth, login, make_user

ROOT_PW = "Test-Root-Password-1!"


@pytest.fixture(autouse=True)
def _fresh(client):
    gpcstore.store_path().unlink(missing_ok=True)
    gpcstore.session_clear()
    yield
    gpcstore.store_path().unlink(missing_ok=True)
    gpcstore.session_clear()


def _load():
    from app.config import settings
    return gpc.load(settings)


def test_a_change_is_recorded_with_who_how_when_and_enforced(client):
    entry = gpcstore.set_flag("integrity.forensic_copies", "7", "root (console)", gpcstore.ROOT, "console", "keep more")
    assert entry["value"] == 7 and entry["set_by"] == "root (console)" and entry["note"] == "keep more"
    pol = _load()
    assert pol.values["integrity.forensic_copies"] == 7 and pol.sources["integrity.forensic_copies"] == "policy store"
    m = pol.meta["integrity.forensic_copies"]
    assert m["set_by"] == "root (console)" and m["authority"] == "root" and m["enforced_by"] and m["enforced_at"]
    h = gpcstore.history("integrity.forensic_copies")
    assert h[0]["old"] == 3 and h[0]["new"] == 7 and h[0]["rank"] == "root" and h[0]["via"] == "console"


def test_editing_the_file_by_hand_resets_it_and_keeps_the_evidence(client):
    gpcstore.set_flag("integrity.forensic_copies", "7", "root", gpcstore.ROOT, "console")
    path = gpcstore.store_path()
    doc = json.loads(path.read_text())
    doc["flags"]["integrity.forensic_copies"]["value"] = 99
    path.write_text(json.dumps(doc))
    pol = _load()
    assert pol.values["integrity.forensic_copies"] == 3                                  # defaults again
    assert list(path.parent.glob(path.name + ".tampered-*"))
    assert pol.notices and "edited outside imPress" in pol.notices[0]["message"]
    assert gpcstore.history()[0]["by"] == "system" and gpcstore.read()["resets"] == 1


@pytest.mark.parametrize("damage", [lambda d: d["history"].clear(), lambda d: d.update(flags={"x": 1}),
                                    lambda d: d["history"].append({"seq": 9})])
def test_any_edit_breaks_the_seal(client, damage):
    gpcstore.set_flag("integrity.forensic_copies", "7", "root", gpcstore.ROOT, "console")
    doc = json.loads(gpcstore.store_path().read_text())
    damage(doc)
    gpcstore.store_path().write_text(json.dumps(doc))
    assert gpcstore.load()[1] is not None


def test_garbage_is_reset_too(client):
    gpcstore.store_path().write_text("{ nope")
    assert "edited outside imPress" in gpcstore.load()[1]


def test_the_history_is_a_hash_chain(client):
    for v in ("4", "5", "6"):
        gpcstore.set_flag("integrity.forensic_copies", v, "root", gpcstore.ROOT, "console")
    rows = gpcstore.read()["history"]
    assert [r["seq"] for r in rows] == [1, 2, 3] and rows[1]["prev"] == rows[0]["hash"]


def test_administrators_and_faculty_cannot_change_policy(client):
    with pytest.raises(gpcstore.PolicyRefused) as e:
        gpcstore.set_flag("integrity.forensic_copies", "5", "adm", gpcstore.ADMIN, "web")
    assert e.value.code == "POLICY_FORBIDDEN"


def test_a_super_admin_changes_only_operational_flags(client):
    gpcstore.set_flag("integrity.forensic_copies", "5", "su", gpcstore.SUPER, "web")
    with pytest.raises(gpcstore.PolicyRefused) as e:
        gpcstore.set_flag("dual_control.delay_minutes", "5", "su", gpcstore.SUPER, "web")
    assert e.value.code == "POLICY_FORBIDDEN" and "root" in e.value.message


def test_what_root_set_a_super_admin_cannot_undo(client):
    gpcstore.set_flag("integrity.forensic_copies", "8", "root", gpcstore.ROOT, "console")
    with pytest.raises(gpcstore.PolicyRefused):
        gpcstore.set_flag("integrity.forensic_copies", "2", "su", gpcstore.SUPER, "web")
    with pytest.raises(gpcstore.PolicyRefused):
        gpcstore.reset_flags(["integrity.forensic_copies"], "su", gpcstore.SUPER, "web")
    assert gpcstore.reset_flags(["integrity.forensic_copies"], "root", gpcstore.ROOT, "console") == ["integrity.forensic_copies"]


@pytest.mark.parametrize("name,value,code", [("nope.flag", "1", "POLICY_UNKNOWN_FLAG"), ("integrity.forensic_copies", "-3", "POLICY_BAD_VALUE"),
                                             ("test_mode.forced", "true", "POLICY_UNKNOWN_FLAG")])
def test_bad_changes_are_refused_with_a_code(client, name, value, code):
    with pytest.raises(gpcstore.PolicyRefused) as e:
        gpcstore.set_flag(name, value, "root", gpcstore.ROOT, "console")
    assert e.value.code == code


def test_a_change_that_makes_flags_conflict_is_refused(client):
    with pytest.raises(gpcstore.PolicyRefused) as e:
        gpcstore.set_flag("dual_control.enabled", "false", "root", gpcstore.ROOT, "console")
        _load()                                                                         # the server reloads it within seconds
        gpcstore.set_flag("dual_control.mfa_required", "true", "root", gpcstore.ROOT, "console")
    assert e.value.code == "POLICY_CONFLICT"


def test_the_hardened_profile_is_never_loosened_by_the_store(client):
    gpc.current().profile = "hardened"
    try:
        with pytest.raises(gpcstore.PolicyRefused) as e:
            gpcstore.set_flag("audit.min_retention_days", "5", "root", gpcstore.ROOT, "console")
        assert e.value.code == "POLICY_LOOSENING"
    finally:
        gpc.current().profile = "standard"


def test_a_super_admin_edits_through_the_web_with_step_up(client):
    su = auth(login(client))
    r = client.put("/api/admin/system/policy/integrity.forensic_copies", headers=su,
                   json={"value": 6, "password": "wrong"})
    assert r.status_code == 403
    r = client.put("/api/admin/system/policy/integrity.forensic_copies", headers=su, json={"value": 6, "password": "admin123", "note": "n"})
    assert r.status_code == 200 and r.json()["set_via"] == "web"
    assert gpc.get("integrity.forensic_copies") == 6
    view = {f["name"]: f for f in client.get("/api/admin/system/policy", headers=su).json()["flags"]}
    assert view["integrity.forensic_copies"]["source"] == "policy store" and view["integrity.forensic_copies"]["set_by"] == "impress.default.superAdmin"
    r = client.put("/api/admin/system/policy/dual_control.delay_minutes", headers=su, json={"value": 3, "password": "admin123"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "POLICY_FORBIDDEN"
    assert client.get("/api/admin/system/policy/history", headers=su).json()["history"][0]["via"] == "web"
    assert client.delete("/api/admin/system/policy/integrity.forensic_copies?password=admin123", headers=su).json()["reset"]


def test_administrators_cannot_use_the_policy_api(client):
    su = auth(login(client))
    _, adm = make_user(client, su, "adm9", role="admin")
    assert client.put("/api/admin/system/policy/integrity.forensic_copies", headers=adm, json={"value": 6, "password": "x"}).status_code == 403
    assert client.get("/api/admin/system/policy", headers=adm).status_code == 200      # reading is allowed


# ── conflicts ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("inline,needle", [
    ("test_mode.forced=true,test_mode.allowed=false", "forced on"),
    ("dual_control.enabled=false,backups.restore_requires_approval=true", "no restore could ever run"),
    ("dual_control.enabled=false,dual_control.mfa_required=true", "second factor"),
    ("audit.min_retention_days=100,audit.purge_days=10", "sooner than the minimum"),
    ("iips.enabled=false,iips.device_binding=enforce", "device binding"),
])
def test_conflicting_flags_stop_the_policy_from_building(inline, needle):
    with pytest.raises(gpc.PolicyConflict) as e:
        gpc.build("standard", inline, None, None)
    assert needle in str(e.value) and e.value.conflicts


def test_every_conflict_is_listed_not_just_the_first():
    with pytest.raises(gpc.PolicyConflict) as e:
        gpc.build("standard", "test_mode.forced=true,test_mode.allowed=false,dual_control.enabled=false,dual_control.mfa_required=true", None, None)
    assert len(e.value.conflicts) == 2


def test_defaults_alone_never_conflict_and_no_test_mode_still_works():
    for profile in gpc.PROFILES:
        gpc.build(profile, "", None, None)
    gpc.build("standard", "test_mode.allowed=false", None, None)                        # --no-test-mode


def test_the_program_does_not_boot_with_conflicting_flags(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    env = {**os.environ, "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'c.db'}", "IMPRESS_GPC": ""}
    p = subprocess.run([sys.executable, "-m", "app.serve", "--plain", "--feature", "dual_control.enabled=false",
                        "--feature", "dual_control.mfa_required=true"], cwd=Path(__file__).resolve().parents[1],
                       env=env, capture_output=True, text=True, timeout=60)
    assert p.returncode == 2 and "FLAG_CONFLICT" in p.stderr and "second factor" in p.stderr
    assert not (tmp_path / "c.db").exists(), "nothing else was started or checked"


# ── root's password ────────────────────────────────────────────────────

def test_the_shipped_hash_is_a_sha512_digest_and_is_not_the_test_password():
    assert len(rootauth.DEFAULT_SHA512) == 128 and int(rootauth.DEFAULT_SHA512, 16)
    assert rootauth.DEFAULT_SHA512 != hashlib.sha512(ROOT_PW.encode()).hexdigest()


def test_check_is_exact_and_slows_wrong_tries(monkeypatch):
    waits = []
    monkeypatch.setattr(rootauth.time, "sleep", waits.append)
    assert rootauth.check(ROOT_PW) and not rootauth.check("") and not rootauth.check(ROOT_PW.lower())
    for _ in range(4):
        rootauth.check("wrong")
    rootauth.check("wrong again")
    assert waits and max(waits) > 0
    rootauth.check(ROOT_PW)
    assert rootauth._failures["n"] == 0


@pytest.mark.parametrize("command,sensitive", [
    ("policy set a b", True), ("policy show", False), ("iips rehash", True), ("iips status", False), ("system reset --confirm x", True),
    ("password reset", True), ("password show", False), ("superadmin create bob", True), ("mfa reset bob", True),
    ("backup restore x --yes", True), ("backup list", False), ("flags reset --file", True), ("flags reset", False),
    ("flash /dev/ttyUSB0", True), ("sessions end --all", True), ("sessions list", False), ("users set-password bob", True),
    ("users list", False), ("restart --rehash", True), ("restart", False), ("api POST /x {}", True), ("api GET /x", False), ("status", False)])
def test_which_commands_ask_for_it(command, sensitive):
    assert rootauth.is_sensitive(command) is sensitive


def test_the_console_refuses_a_sensitive_command_without_the_password(monkeypatch):
    import io

    from app.console import Console
    monkeypatch.delenv("IMPRESS_ROOT_PASSWORD")
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    con = Console(out=out)
    try:
        con.onecmd("policy set integrity.forensic_copies 4")
        con.root_password = "wrong"
        con.onecmd("policy set integrity.forensic_copies 4")
        con.root_password = ROOT_PW
        con.onecmd("policy set integrity.forensic_copies 4 --note test")
        con.onecmd("policy show")
        con.onecmd("policy history")
    finally:
        con.close()
    text = out.getvalue()
    assert "ROOT_PASSWORD_REQUIRED" in text and "ROOT_PASSWORD_WRONG" in text and "recorded" in text
    assert gpcstore.read()["flags"]["integrity.forensic_copies"]["value"] == 4 and "root (console)" in text


def test_rehash_at_start_needs_root_password(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    env = {k: v for k, v in os.environ.items() if k != "IMPRESS_ROOT_PASSWORD"}
    env.update(IMPRESS_DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'c.db'}", IMPRESS_GPC="")
    p = subprocess.run([sys.executable, "-m", "app.serve", "--plain", "--rehash"], cwd=Path(__file__).resolve().parents[1],
                       env=env, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    assert p.returncode == 2 and "ROOT_PASSWORD_REQUIRED" in p.stderr
    env["IMPRESS_ROOT_PASSWORD"] = "nope"
    p = subprocess.run([sys.executable, "-m", "app.serve", "--plain", "--rehash"], cwd=Path(__file__).resolve().parents[1],
                       env=env, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    assert p.returncode == 2 and "ROOT_PASSWORD_WRONG" in p.stderr


def test_the_screen_asks_for_the_password_masked_and_never_shows_or_keeps_it(monkeypatch):
    import os

    from app import rootscreen
    monkeypatch.setattr(rootscreen.shutil, "get_terminal_size", lambda _f: os.terminal_size((100, 28)))
    screen = rootscreen.Screen(["imPress", "running"])
    screen.key("PASTE:policy set integrity.forensic_copies 4")
    assert screen.key("ENTER") is None and screen.password_for
    screen.key("PASTE:Secret-pw")
    shown = rootscreen.plain("\n".join(screen.frame()))
    assert "Secret-pw" not in shown and "***" in shown and "root password>" in shown
    assert screen.key("ENTER") == "policy set integrity.forensic_copies 4\x1fSecret-pw"
    assert screen.password_for is None and not screen.secret and not screen.history
    screen.key("PASTE:iips rehash")
    screen.key("ENTER")
    screen.key("ESCAPE")
    assert screen.password_for is None and not screen.secret


# ── device binding ─────────────────────────────────────────────────────

def test_the_fingerprint_ignores_everything_that_changes(monkeypatch):
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-A")
    a = fingerprint.get()[0]
    monkeypatch.setattr("platform.release", lambda: "99.9")
    monkeypatch.setattr("socket.gethostname", lambda: "other-name")
    monkeypatch.setattr("os.getcwd", lambda: "/somewhere/else")
    assert fingerprint.get()[0] == a and len(a) == 64
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-B")
    assert fingerprint.get()[0] != a


def test_a_container_has_no_fingerprint(monkeypatch):
    monkeypatch.delenv("IMPRESS_DEVICE_ID", raising=False)
    monkeypatch.setattr("app.services.boot_verify.in_container", lambda: True)
    assert fingerprint.compute()[0] is None


def test_this_machine_has_a_stable_fingerprint():
    monkeypatch_free = fingerprint.compute()
    assert monkeypatch_free == fingerprint.compute()


@pytest.fixture
def tree(tmp_path, monkeypatch):
    from app.services import iips
    root = tmp_path / "src"
    (root / "backend/app").mkdir(parents=True)
    (root / "backend/app/a.py").write_text("a = 1\n")
    (root / "VERSION").write_text("2.2.0\n")
    monkeypatch.setattr(iips, "baseline_path", lambda: tmp_path / "state" / "x.iips.json")
    monkeypatch.setattr(iips, "build_marker", lambda root=None: "git:one")
    return root


def test_code_and_reference_copied_to_another_machine_are_flagged(tree, monkeypatch):
    from app.services import iips
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-A")
    assert iips.check(root=tree, binding="enforce")["status"] == "baseline_created"
    assert iips.check(root=tree, binding="enforce")["status"] == "ok"
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-B")                                  # the same files, another machine
    st = iips.check(root=tree, binding="enforce")
    assert st["status"] == "violation" and st["device_mismatch"] and "different device" in iips.violation_message()
    st = iips.check(root=tree, binding="warn")
    assert st["status"] == "ok" and "another device" in st["device_warning"]
    assert iips.check(root=tree, binding="off")["status"] == "ok"


def test_a_folder_move_or_rename_is_not_a_copy(tree, monkeypatch, tmp_path):
    from app.services import iips
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-A")
    iips.check(root=tree, binding="enforce")
    moved = tmp_path / "elsewhere" / "renamed"
    moved.parent.mkdir()
    tree.rename(moved)
    assert iips.check(root=moved, binding="enforce")["status"] == "ok"


def test_an_edited_reference_is_not_the_same_as_a_copied_one(tree, monkeypatch):
    from app.services import iips
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-A")
    iips.check(root=tree, binding="enforce")
    doc = json.loads(iips.baseline_path().read_text())
    doc["baseline"]["root_hash"] = "0" * 64
    iips.baseline_path().write_text(json.dumps(doc))
    st = iips.check(root=tree, binding="enforce")
    assert st["status"] == "violation" and not st["device_mismatch"] and "edited" in st["changes"][0]["change"]


def test_rehash_checks_what_is_there_first_and_records_it(tree, monkeypatch):
    from app.services import iips
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-A")
    iips.check(root=tree, binding="enforce")
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-B")
    assert iips.verify_baseline("enforce")["found"] == "other_device"
    st = iips.check(root=tree, rehash=True, binding="enforce")
    assert st["status"] == "rehashed" and st["replaced"] == "other_device"
    assert iips.check(root=tree, binding="enforce")["status"] == "ok"
    h = json.loads(iips.baseline_path().read_text())["baseline"]["history"]
    assert [x["found"] for x in h] == ["no reference before", "other_device"] and h[1]["prev"] == h[0]["hash"] and h[1]["by"].startswith("root")


def test_a_reference_made_before_binding_is_bound_at_the_next_start(tree, monkeypatch):
    from app.services import iips
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-A")
    iips.check(root=tree, binding="off")
    assert json.loads(iips.baseline_path().read_text())["baseline"]["device"] is None
    assert iips.check(root=tree, binding="enforce")["status"] == "ok"
    assert json.loads(iips.baseline_path().read_text())["baseline"]["device"] == fingerprint.get()[0]
    monkeypatch.setenv("IMPRESS_DEVICE_ID", "machine-B")
    assert iips.check(root=tree, binding="enforce")["status"] == "violation"


# ── --save and session flags ───────────────────────────────────────────

def test_save_keeps_feature_flags_and_their_explanations(tmp_path):
    from app import flagsfile
    target = tmp_path / "f.json"
    flagsfile.save({"test_mode.forced": True, "ota.enabled": False, "profile": "hardened"}, target)
    doc = json.loads(target.read_text())
    assert doc["flags"]["ota.enabled"]["value"] is False and doc["flags"]["ota.enabled"]["about"] and doc["profile"]["value"] == "hardened"
    assert flagsfile.load(target) == ("hardened", ["test_mode.forced=true", "ota.enabled=false"])


def test_save_refuses_policy_flags(tmp_path):
    from app import flagsfile
    with pytest.raises(flagsfile.FlagsFileError, match="FLAG_IS_POLICY"):
        flagsfile.save({"dual_control.delay_minutes": 5}, tmp_path / "f.json")


def test_save_on_the_command_line_writes_the_file_and_the_next_start_uses_it(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    flags = tmp_path / "flags.json"
    env = {**os.environ, "IMPRESS_FLAGS_FILE": str(flags), "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'c.db'}", "IMPRESS_GPC": ""}
    run = lambda *a: subprocess.run([sys.executable, "-m", "app.serve", "--plain", *a], cwd=Path(__file__).resolve().parents[1],  # noqa: E731
                                    env=env, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    p = run("--save", "--feature", "dual_control.delay_minutes=5")
    assert p.returncode == 2 and "FLAG_IS_POLICY" in p.stderr and not flags.exists() or "policy flag" in p.stderr
    from app import flagsfile
    flagsfile.save({"test_mode.export_allowed": False}, flags)
    assert flagsfile.load(flags)[1] == ["test_mode.export_allowed=false"]


def test_session_flags_apply_now_and_vanish_at_restart(client):
    gpcstore.session_write({"test_mode.export_allowed": False}, "root")
    pol = _load()
    assert pol.values["test_mode.export_allowed"] is False and pol.sources["test_mode.export_allowed"] == "session"
    gpcstore.session_clear()
    assert _load().values["test_mode.export_allowed"] is True


def test_session_flags_can_only_be_feature_flags(client):
    gpcstore.session_write({"dual_control.delay_minutes": 50}, "root")
    assert _load().values["dual_control.delay_minutes"] == 0


def test_console_flags_set_save_and_reset(tmp_path, monkeypatch):
    import io

    from app import flagsfile
    from app.console import Console
    target = tmp_path / "f.json"
    monkeypatch.setenv("IMPRESS_FLAGS_FILE", str(target))
    out = io.StringIO()
    con = Console(out=out)
    try:
        con.onecmd("flags set test_mode.export_allowed false")
        con.onecmd("flags set dual_control.delay_minutes 5")
        con.onecmd("flags show")
        assert gpcstore.session_read() == {"test_mode.export_allowed": False}
        con.onecmd("flags save")
        assert gpcstore.session_read() == {} and flagsfile.load(target)[1] == ["test_mode.export_allowed=false"]
        con.onecmd("flags set ota.enabled false")
        con.onecmd("flags reset")
        assert gpcstore.session_read() == {}
        con.root_password = ROOT_PW
        con.onecmd("flags reset --file")
    finally:
        con.close()
    text = out.getvalue()
    assert "for this session only" in text and "policy flag" in text and "saved to" in text
    assert flagsfile.load(target)[1] == []
