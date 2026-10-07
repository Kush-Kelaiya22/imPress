"""Unit tests for the root test runner (run_tests.py)."""

import json
import shutil
import subprocess
import sys

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
