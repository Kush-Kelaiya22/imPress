"""Unit tests for the root test runner (run_tests.py)."""

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

import pytest

from conftest import ROOT

import run_tests


def test_discovery_lists_core_and_optional_suites():
    names = [s.name for s in run_tests.discover()]
    for required in ("backend", "firmware-static", "repo", "frontend",
                     "idf:class_c6", "idf:class_s3", "idf:student"):
        assert required in names
    assert any(n.startswith("host:protocol") for n in names)
    assert len(names) == len(set(names)), "suite names must be unique"


def test_selection_rules():
    suites = run_tests.discover()
    default = run_tests.select(suites, [], False, False)
    assert all(not s.optional for s in default)
    assert {s.name for s in run_tests.select(suites, ["host"], False, False)} == {
        s.name for s in suites if s.kind == "host"}
    assert [s.name for s in run_tests.select(suites, ["backend"], False, False)] == ["backend"]
    with_idf = run_tests.select(suites, [], True, False)
    assert sum(s.name.startswith("idf:") for s in with_idf) == 3


def test_parse_junit(tmp_path):
    xml = tmp_path / "r.xml"
    xml.write_text("""<testsuites><testsuite>
      <testcase classname="t.a" name="ok" time="0.5"/>
      <testcase classname="t.a" name="bad" time="1.25"><failure message="assert 1 == 2">trace</failure></testcase>
      <testcase classname="t.b" name="skip" time="0"><skipped message="no hw"/></testcase>
      <testcase classname="t.b" name="boom" time="0.1"><error message="fixture crashed"/></testcase>
    </testsuite></testsuites>""")
    cases = run_tests.parse_junit(xml)
    assert [c.status for c in cases] == ["passed", "failed", "skipped", "error"]
    assert cases[1].seconds == 1.25 and cases[1].message == "assert 1 == 2"


def test_parse_host_output():
    ok = run_tests.parse_host_output("ok   test_a\nok   test_b\nPASS test_x\n")
    assert [c.status for c in ok] == ["passed", "passed"]
    bad = run_tests.parse_host_output("ok   test_a\nFAIL t.c:12: x == y\n")
    assert [c.status for c in bad] == ["passed", "failed"] and "x == y" in bad[1].message
    asan = run_tests.parse_host_output("==1==ERROR: AddressSanitizer: heap-use-after-free\n")
    assert asan[-1].status == "failed"
    single = run_tests.parse_host_output("I spi: init\nPASS test_spi_slave\n")
    assert [c.name for c in single] == ["test_spi_slave"]


def test_missing_prerequisite_is_skip_not_failure():
    suite = run_tests.Suite("fake", "cmd", "needs a tool", ["true"], requires=["definitely-not-installed-xyz"])
    res = run_tests.run_suite(suite, None, False)
    assert res.status == "SKIP" and "definitely-not-installed-xyz" in res.reason


def test_failing_command_is_reported(tmp_path):
    suite = run_tests.Suite("fake", "cmd", "fails", [sys.executable, "-c", "import sys; print('boom'); sys.exit(3)"])
    res = run_tests.run_suite(suite, None, False)
    assert res.status == "FAIL" and "exit code 3" in res.reason and "boom" in res.output_tail


def test_markdown_report_lists_every_suite():
    rs = [run_tests.SuiteResult("a", "d", "PASS", 1.0, passed=3),
          run_tests.SuiteResult("b", "d", "FAIL", 2.0, failed=1, reason="exit code 1",
                                cases=[run_tests.CaseResult("t::x", "failed", message="nope")]),
          run_tests.SuiteResult("c", "d", "SKIP", 0.0, reason="missing: cc")]
    md = run_tests.markdown_report(rs, 3.0)
    assert "| `a` | ✅ PASS | 3 |" in md and "### ❌ b" in md and "`t::x` nope" in md and "missing: cc" in md


@pytest.mark.skipif(not shutil.which("cc") or not shutil.which("bash"), reason="needs cc + bash")
def test_end_to_end_json_report(tmp_path):
    out = tmp_path / "report.json"
    proc = subprocess.run([sys.executable, "run_tests.py", "--suite", "host:protocol", "--no-color", "--json", str(out)],
                          cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(out.read_text())
    assert report["ok"] is True and {s["name"] for s in report["suites"]} == {"host:protocol", "host:protocol:mesh_dedup"}
    assert all(s["status"] == "PASS" and s["passed"] > 0 and s["seconds"] > 0 for s in report["suites"])
    assert "ALL PASSED" in proc.stdout and "imPress test report" in proc.stdout


def test_unknown_suite_exits_2():
    proc = subprocess.run([sys.executable, "run_tests.py", "--suite", "nope-nothing"], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 2


def test_requirements_parsing_follows_includes_and_strips_specifiers(tmp_path):
    (tmp_path / "base.txt").write_text("fastapi>=0.115.0\nuvicorn[standard]>=0.30\n# comment\n\nsqlalchemy[asyncio] ; python_version>'3'\n")
    (tmp_path / "dev.txt").write_text("-r base.txt\npytest>=8  # inline comment\n--index-url https://x\n")
    assert run_tests._requirements(tmp_path / "dev.txt") == ["fastapi", "uvicorn", "sqlalchemy", "pytest"]


def test_dev_requirements_cover_every_runtime_requirement():
    names = run_tests._requirements(ROOT / run_tests.DEV_REQUIREMENTS)
    assert {"pytest", "httpx", "pyyaml", "fastapi", "aiosqlite"} <= set(names)


def test_missing_packages_reported_once_with_install_hint(tmp_path, monkeypatch):
    req = tmp_path / "req.txt"
    req.write_text("pytest\ndefinitely-not-a-real-package-xyz>=1\n")
    monkeypatch.setattr(run_tests, "ROOT", tmp_path)
    assert run_tests.missing_packages("req.txt") == ["definitely-not-a-real-package-xyz"]
    (tmp_path / "tests").mkdir()
    suite = run_tests._pytest_suite("fake", "tests", "needs a package", pip_requires="req.txt")
    res = run_tests.run_suite(suite, None, False)
    assert res.status == "FAIL" and res.errors == 1 and res.passed == 0
    assert "definitely-not-a-real-package-xyz" in res.reason
    assert "pip install -r req.txt" in res.output_tail


def test_suites_declare_their_requirements():
    suites = {s.name: s for s in run_tests.discover()}
    assert suites["backend"].pip_requires == run_tests.DEV_REQUIREMENTS
    assert suites["repo"].pip_requires == run_tests.DEV_REQUIREMENTS   # imports the app for docs checks
    assert suites["firmware-static"].pip_requires == ""


# ── Live progress, timeout and interruption (#24) ───────────────────────────

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups / signals")


def _py(code):
    return [sys.executable, "-c", code]


def test_timeout_stops_the_suite_quickly():
    suite = run_tests.Suite("slow", "cmd", "sleeps", _py("import time; print('started', flush=True); time.sleep(60)"))
    t0 = time.perf_counter()
    res = run_tests.run_suite(suite, None, False, timeout=1.0)
    assert time.perf_counter() - t0 < 15
    assert res.status == "FAIL" and res.reason.startswith("timed out after") and "started" in res.output_tail


def test_heartbeat_reports_progress_when_not_a_terminal(monkeypatch, capsys):
    monkeypatch.setattr(run_tests, "HEARTBEAT_SECONDS", 0.3)
    code, out, aborted = run_tests.run_streaming(
        _py("import time; print('[3/10] Building C object x.o', flush=True); time.sleep(1.2)"), ROOT, None)
    shown = capsys.readouterr().out
    assert code == 0 and aborted == "" and "[3/10] Building" in out
    assert "still running" in shown and "[3/10] Building C object x.o" in shown


def test_live_status_line_shows_latest_output_and_is_cleared(capsys):
    run_tests.run_streaming(_py("import time; print('step one', flush=True); time.sleep(0.8)"), ROOT, None, live=True)
    shown = capsys.readouterr().out
    assert "\r" in shown and "step one" in shown and shown.endswith("\r")


def test_partial_lines_and_ansi_colours_reach_the_status_line(monkeypatch, capsys):
    # pytest -q prints dots without a newline; ninja/npm may colour their output
    monkeypatch.setattr(run_tests, "HEARTBEAT_SECONDS", 0.3)
    run_tests.run_streaming(_py("import sys, time; sys.stdout.write('\\x1b[32m....\\x1b[0m'); sys.stdout.flush(); time.sleep(1)"),
                            ROOT, None)
    shown = capsys.readouterr().out
    assert "still running" in shown and "...." in shown and "\x1b[32m" not in shown


@posix_only
def test_ctrl_c_stops_the_whole_process_group():
    # the grandchild `sleep` must die too (npm -> vite, docker run -> container)
    cmd = ["sh", "-c", "sleep 60; echo should-not-print"]
    threading.Timer(0.7, os.kill, (os.getpid(), signal.SIGINT)).start()
    t0 = time.perf_counter()
    code, out, aborted = run_tests.run_streaming(cmd, ROOT, None)
    assert aborted == "interrupted" and code != 0 and "should-not-print" not in out
    assert time.perf_counter() - t0 < 15


@posix_only
def test_interrupt_prints_report_and_exits_130(tmp_path):
    script = tmp_path / "drive.py"
    script.write_text(f"""
import os, signal, sys, threading
sys.path.insert(0, {str(ROOT)!r})
import run_tests
run_tests.discover = lambda: [run_tests.Suite("hang", "cmd", "hangs", ["sleep", "60"]),
                              run_tests.Suite("never", "cmd", "not reached", ["true"])]
threading.Timer(1.0, os.kill, (os.getpid(), signal.SIGINT)).start()
sys.exit(run_tests.main(["--no-color"]))
""")
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 130, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert "interrupted" in proc.stdout and "imPress test report" in proc.stdout and "never" not in proc.stdout.split("imPress test report")[1]


def test_idf_docker_command_uses_init_and_skips_when_daemon_down(monkeypatch):
    monkeypatch.setattr(run_tests.shutil, "which", lambda exe: "/usr/bin/docker" if exe == "docker" else None)
    monkeypatch.setattr(run_tests.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    cmd, _ = run_tests._idf_command("student")
    assert cmd[:4] == ["docker", "run", "--rm", "--init"] and run_tests.IDF_IMAGE in cmd and cmd[-1] == "build"
    monkeypatch.setattr(run_tests.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 1))
    cmd, why = run_tests._idf_command("student")
    assert cmd is None and "daemon" in why


def test_pytest_children_are_unbuffered(monkeypatch):
    seen = {}

    def fake(cmd, cwd, env, *a):
        seen.update(env)
        return 0, "", ""
    monkeypatch.setattr(run_tests, "run_streaming", fake)
    run_tests.run_suite(run_tests.Suite("x", "cmd", "d", ["true"]), None, False)
    assert seen["PYTHONUNBUFFERED"] == "1"


def test_frontend_suite_does_not_write_a_lockfile():
    # a test run must leave the checkout clean (the project has no package-lock.json)
    frontend = {s.name: s for s in run_tests.discover()}["frontend"]
    assert "--no-package-lock" in " ".join(frontend.cmd)
