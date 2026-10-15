"""The root console and the launch flags, run the way root runs them: as separate processes on a database of their own."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def box(tmp_path):
    env = {**os.environ, "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'c.db'}", "IMPRESS_TEMP_BACKUP_DIR": str(tmp_path / "b"),
           "IMPRESS_FIRMWARE_DIR": str(tmp_path / "fw"), "IMPRESS_GPC": "", "PYTHONPATH": str(BACKEND),
           "IMPRESS_DEFAULT_SUPERADMIN_PASSWORD": "Console-Test-Root-19!",
           "IMPRESS_ENV_FILE": str(tmp_path / ".env")}
    env.pop("IMPRESS_IN_CONTAINER", None)
    (tmp_path / ".env").write_text("IMPRESS_DEFAULT_SUPERADMIN_PASSWORD=Console-Test-Root-19!\n")

    def run(*cmds, module="app.console", extra=(), stdin=None, env_extra=None):
        args = [sys.executable, "-m", module, *extra]
        for c in cmds:
            args += ["-c", c]
        p = subprocess.run(args, cwd=tmp_path, env={**env, **(env_extra or {})}, capture_output=True, text=True, timeout=120, input=stdin)
        return p.returncode, p.stdout + p.stderr
    run.env = env
    return run


def test_status_and_version(box):
    rc, out = box("status", "version")
    assert rc == 0 and "profile" in out.lower() and "2.2" in out


def test_creating_accounts_and_the_pending_setup_state(box):
    rc, out = box("users create ann --role teacher --name 'Ann Lee'", "users list")
    assert rc == 0 and "temporary password:" in out and "pending" in out.lower()
    pw = next(l for l in out.splitlines() if l.startswith("temporary password:")).split(": ")[1]
    assert len(pw) >= 12
    rc, out = box("users create ann --role teacher")
    assert rc == 1 and "taken" in out.lower()


def test_super_admins_exist_only_from_the_console_and_start_pending(box):
    rc, out = box("superadmin create root2 --password Temp-root2-Pass1", "users list --role super_admin")
    assert rc == 0 and "root2" in out and "pending" in out.lower() and "super_admin" in out
    rc, out = box("users create x --role super_admin")
    assert rc == 1


def test_ta_designation_and_user_lifecycle(box):
    rc, out = box("users create tia --role teacher --ta", "users deactivate tia", "users activate tia", "users delete tia", "users trash",
                  "users restore tia", "users list")
    assert rc == 0 and "restorable for 30 days" in out and "ta" in out


def _seed_default(box):
    code = ("import asyncio; from app.database import init_db; from app.services import bootstrap;"
            "asyncio.run(init_db()); asyncio.run(bootstrap.ensure_default_superadmin())")
    subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=box.env, check=True, capture_output=True)


def test_the_default_super_admin_is_protected(box):
    _seed_default(box)
    rc, out = box("users deactivate impress.default.superAdmin")
    assert rc == 1 and "default" in out.lower()
    rc, out = box("users delete impress.default.superAdmin")
    assert rc == 1


def test_features_are_switched_as_root_and_can_be_locked(box):
    rc, out = box("feature search off --lock", "features", "policylog search")
    assert rc == 0 and "search" in out and "root (console)" in out
    rc, out = box("feature nope on")
    assert rc == 1 and "no feature" in out.lower()


def test_requirements_and_iips_and_release_commands(box):
    rc, out = box("requirements", "iips status", "iips rehash", "iips status", env_extra={"IMPRESS_MIN_CORES": "1"})
    assert rc == 0 and "Python" in out and "baseline_created" in out and "ok" in out


def test_the_console_reads_commands_from_a_pipe(box):
    _seed_default(box)
    rc, out = box(stdin="version\nusers list\nexit\n")
    assert rc == 0 and "impress.default.superAdmin" in out


def test_unknown_commands_fail_with_a_hint(box):
    rc, out = box("frobnicate")
    assert rc == 1 and "unknown command" in out


def test_the_separate_console_is_closed_in_a_container_but_the_root_screen_is_not(box):
    rc, out = box("version", env_extra={"IMPRESS_IN_CONTAINER": "1"})
    assert rc == 4 and "container" in out
    rc, out = box("version", env_extra={"IMPRESS_IN_CONTAINER": "1", "IMPRESS_ROOT_SCREEN": "1"})
    assert rc == 0


def test_system_reset_needs_the_exact_confirmation(box):
    rc, out = box("system reset")
    assert rc == 1
    rc, out = box("users create keep1 --role admin", 'system reset --confirm "RESET EVERYTHING"', "users list")
    assert rc == 0 and "keep1" not in out.split("the system was reset")[-1]


def test_backups_from_the_console(box):
    rc, out = box("backup save before-term", "backup list")
    assert rc == 0 and "saved/before-term" in out


# ── launch flags ────────────────────────────────────────────────────────

def test_serve_flags_become_policy_overrides():
    from app import serve
    args = serve.build_parser().parse_args(["--test-mode", "--no-ota", "--bypass-iips", "--feature", "features.disabled=search"])
    assert serve.overrides(args) == ["test_mode.forced=true", "ota.enabled=false", "iips.enabled=false", "features.disabled=search"]


def test_serve_is_fixed_to_all_interfaces_on_port_8000(monkeypatch):
    from app import serve
    monkeypatch.setenv("IMPRESS_HOST", "127.0.0.1")
    monkeypatch.setenv("IMPRESS_PORT", "9000")
    args = serve.build_parser().parse_args([])
    assert (args.host, args.port) == ("0.0.0.0", 8000)
    with pytest.raises(SystemExit):
        serve.build_parser().parse_args(["--host", "127.0.0.1"])
    with pytest.raises(SystemExit):
        serve.build_parser().parse_args(["--port", "9000"])


def test_serve_refuses_contradictory_flags(box):
    rc, out = box(module="app.serve", extra=["--test-mode", "--no-test-mode"])
    assert rc == 2 and "contradict" in out
    rc, out = box(module="app.serve", extra=["--rehash", "--bypass-iips"])
    assert rc == 2 and "contradict" in out
    rc, out = box(module="app.serve", extra=["--feature", "nope.nothing=1"])
    assert rc == 2


def test_serve_stops_with_the_integrity_message_when_files_changed(box, tmp_path):
    from app.services import iips
    base = tmp_path / "c.iips.json"
    doc = {"baseline": {**iips.snapshot(), "created_at": "x"}}
    doc["baseline"]["files"]["backend/app/main.py"] = "0" * 64                  # as if main.py had been edited
    # a baseline signed with the box's own secret: the console computes it exactly as the server would
    code = ("import json,sys; sys.path.insert(0,'.'); from app.services import iips; doc=iips.snapshot();"
            "doc['files']['backend/app/main.py']='0'*64; doc['created_at']='x'; doc['build']=iips.build_marker();"
            f"open({str(base)!r},'w').write(json.dumps({{'baseline':doc,'seal':iips._seal(doc)}}))")
    env = {**os.environ, "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'c.db'}", "IMPRESS_GPC": ""}
    subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=env, check=True)
    p = subprocess.run([sys.executable, "-m", "app.serve", "--plain"], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=60)
    assert p.returncode == 3 and "disabled by Root" in p.stderr and "--rehash" in p.stderr and "backend/app/main.py" in p.stderr
    assert json.loads(base.read_text())["baseline"]["files"]["backend/app/main.py"] == "0" * 64          # not silently repaired


def test_the_root_screen_wraps_by_visible_width_and_colours_by_level():
    from app import rootscreen
    lines = rootscreen.wrap_ansi("\033[31m" + "y" * 25 + "\033[0m", 10, indent=2)
    visible = [__import__("re").sub(r"\x1b\[[0-9;]*m", "", ln) for ln in lines]
    assert all(len(v) <= 10 for v in visible) and "".join(v.strip() for v in visible) == "y" * 25
    assert rootscreen.wrap_ansi("short", 80) == ["short"]
    wide = rootscreen.wrap_ansi("界" * 6, 5, indent=1)
    def cell_width(text):
        plain = __import__("re").sub(r"\x1b\[[0-9;]*m", "", text)
        return sum(rootscreen._cell_width(ch) for ch in plain)

    assert all(cell_width(line) <= 5 for line in wide)
    assert "ERROR" in rootscreen.style_line("ERROR:    boom") and "\033[" in rootscreen.style_line("WARNING: careful")
    assert rootscreen.style_line("just text").endswith("just text")


def test_root_screen_keeps_scrollable_log_history(monkeypatch, capsys):
    from app import rootscreen
    monkeypatch.setattr(rootscreen.shutil, "get_terminal_size", lambda _fallback: os.terminal_size((48, 10)))
    screen = rootscreen.Screen(["root", "status", "profile", "help"])
    for i in range(14):
        screen.log(f"startup-line-{i:02d}")
    screen.scroll("top")
    assert screen.scrollback == len(screen._wrapped_logs()) - screen.page
    screen.draw()
    assert "scrollback" in capsys.readouterr().out
    screen.scroll("live")
    assert screen.scrollback == 0
    screen.clear()
    assert not screen.messages


def test_read_only_dashboard_actions_and_recovery_after_root_session_revocation(box):
    _seed_default(box)
    from app.rootscreen import MENU
    commands = [c for _, c in MENU if c not in {"clear", "exit", "restart"} and not c.endswith(" ")]
    rc, out = box(*commands, "sessions end --all", "classes list", "uptime")
    assert rc == 0, out
    assert "Traceback" not in out and "sessions: ?" not in out


@pytest.mark.parametrize("command", ["classes create --room X --teacher ann", "students add --email a@x.io ROLL",
                                     "api POST /api/admin/classes invalid-json", "users unlock", "ls delete"])
def test_bad_arguments_do_not_crash_the_console(box, command):
    rc, out = box(command, "version")
    assert rc == 1 and "error:" in out and "Traceback" not in out and "2.2" in out


# ── root can do what a super admin can ──────────────────────────────────

def test_the_default_password_can_be_shown_and_reset_by_root(box, tmp_path):
    import hashlib
    checkout_env = BACKEND / ".env"
    before = hashlib.sha256(checkout_env.read_bytes()).digest() if checkout_env.exists() else None
    _seed_default(box)
    rc, out = box("password show", env_extra={"IMPRESS_INITIAL_ADMIN_PASSWORD": "Fixed-By-Root-9", "IMPRESS_DEFAULT_SUPERADMIN_PASSWORD": ""})
    assert rc == 0 and "Fixed-By-Root-9" in out
    rc, out = box("password show", env_extra={"IMPRESS_INITIAL_ADMIN_PASSWORD": "", "IMPRESS_DEFAULT_SUPERADMIN_PASSWORD": ""})
    assert rc == 0 and "random" in out
    rc, out = box("password reset --password Brand-New-Root-Pass-1")
    assert rc == 0 and "Brand-New-Root-Pass-1" in out
    assert "Brand-New-Root-Pass-1" in (tmp_path / ".env").read_text()
    assert (hashlib.sha256(checkout_env.read_bytes()).digest() if checkout_env.exists() else None) == before
    rc, out = box("password reset --password weak")
    assert rc == 1 and "password" in out.lower()


def test_root_calls_the_applications_own_api(box):
    _seed_default(box)
    rc, out = box("api GET /api/admin/users")
    assert rc == 0 and "impress.default.superAdmin" in out
    rc, out = box("api routes admin/users")
    assert rc == 0 and "/api/admin/users" in out
    rc, out = box("api GET /api/admin/nothing")
    assert rc == 1 and "404" in out
    rc, out = box("api POST /api/admin/users/999999/deactivate")
    assert rc == 1 and "404" in out


def test_classes_students_and_courses_from_the_shell(box):
    _seed_default(box)
    rc, out = box("users create ann --role teacher --name 'Ann Lee'", "classes create 'CS 101' CS101 --teacher ann --room RM-1 --icon rocket --color #2563eb",
                  "classes list", "courses add CS101 Programming", "courses list", "students add ABCDE12345 Asha Rao", "students list asha",
                  "activity 5", "ls classes")
    assert rc == 0, out
    assert "CS101" in out and "RM-1" in out and "Programming" in out and "ABCDE12345" in out and "console.api" in out or "class" in out


def test_help_is_grouped_and_familiar_names_work(box):
    rc, out = box("help", "whoami", "date", "ls")
    assert rc == 0 and "Accounts" in out and "root" in out and "password" in out


def test_a_domain_error_is_a_message_not_a_traceback(box):
    rc, out = box("backup save ../bad", "status")
    assert rc == 1 and "Traceback" not in out and "Name: 1-48 letters" in out and "active super admins" in out


def test_the_long_lived_worker_answers_many_commands_and_survives_errors(box):
    """The root screen keeps one console process: each command ends with a marker, and a failing one does not stop it."""
    p = subprocess.run([sys.executable, "-m", "app.console", "--serve"], cwd=BACKEND, env=box.env, capture_output=True,
                       text=True, timeout=120, input="version\nfrobnicate\nbackup save ../bad\nusers list\nexit\nversion\n")
    marks = [line for line in p.stdout.split("\n") if line.startswith("\x1e")]      # not splitlines(): it splits at \x1e too
    assert marks == ["\x1eOK", "\x1eFAIL", "\x1eFAIL", "\x1eOK", "\x1eOK", "\x1eOK"], p.stdout + p.stderr
    assert "Traceback" not in p.stdout + p.stderr and "unknown command: frobnicate" in p.stdout
    assert p.stdout.count("2.2.0") == 2


def test_verify_says_what_it_found_in_a_line(box):
    rc, out = box("verify")
    assert rc == 0 and "database: ok" in out and "rows verified" in out
