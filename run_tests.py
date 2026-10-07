#!/usr/bin/env python3
"""imPress test runner: runs every test suite and prints one consolidated report.

    python run_tests.py                  # all default suites
    python run_tests.py --list           # show suites and exit
    python run_tests.py -s backend -s host   # only matching suites (prefix match)
    python run_tests.py --with-idf --with-frontend   # also firmware builds + frontend build
    python run_tests.py --json report.json --junit-dir reports

Default suites
  backend            pytest backend/tests        (FastAPI, fresh SQLite per test)
  firmware-static    pytest firmware/tests       (structural guards on C sources)
  repo               pytest tests                (CI / repository / docs consistency)
  host:<suite>       firmware/*/test_host/run*.sh (real firmware C + ASan/UBSan)
Optional suites
  idf:<project>      idf.py build (native ESP-IDF, else Docker espressif/idf:v6.1)
  frontend           npm install && npm run build

Exit status: 0 when nothing failed (skipped suites are reported, not failures).
Only the Python standard library is used, so the runner works before deps exist.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IDF_IMAGE = "espressif/idf:v6.1"
IDF_PROJECTS = ("class_c6", "class_s3", "student")

# ── Data ────────────────────────────────────────────────────────────────────


@dataclass
class Suite:
    name: str
    kind: str                 # "pytest" | "host" | "cmd"
    description: str
    cmd: list[str]
    cwd: Path = ROOT
    optional: bool = False
    requires: list[str] = field(default_factory=list)   # executables that must exist
    env: dict = field(default_factory=dict)


@dataclass
class CaseResult:
    name: str
    status: str               # passed | failed | skipped | error
    seconds: float = 0.0
    message: str = ""


@dataclass
class SuiteResult:
    name: str
    description: str
    status: str               # PASS | FAIL | SKIP
    seconds: float
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    cases: list[CaseResult] = field(default_factory=list)
    reason: str = ""          # why skipped / how it failed
    output_tail: str = ""

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped + self.errors


# ── Discovery ───────────────────────────────────────────────────────────────


def _pytest_suite(name, path, description):
    return Suite(name, "pytest", description,
                 [sys.executable, "-m", "pytest", path, "-q", "-p", "no:cacheprovider",
                  "-W", "ignore::DeprecationWarning"],
                 env={"PYTHONDONTWRITEBYTECODE": "1"})


def discover() -> list[Suite]:
    suites = [
        _pytest_suite("backend", "backend/tests", "Backend API, services and security (pytest)"),
        _pytest_suite("firmware-static", "firmware/tests", "Firmware structural guards (pytest)"),
        _pytest_suite("repo", "tests", "CI, repository and docs consistency (pytest)"),
    ]
    for script in sorted((ROOT / "firmware").glob("*/test_host/run*.sh")):
        project = script.parent.parent.name
        label = script.stem.replace("run_", "").replace("run", "") or "main"
        suites.append(Suite(f"host:{project}" + ("" if label == "main" else f":{label}"), "host",
                            f"Firmware host C tests: {project}/{script.name}",
                            ["bash", str(script.relative_to(ROOT))], requires=["bash", "cc"]))
    for project in IDF_PROJECTS:
        suites.append(Suite(f"idf:{project}", "cmd", f"ESP-IDF v6.1 build: {project}",
                            [], optional=True))
    suites.append(Suite("frontend", "cmd", "Frontend build (npm install + vite build)",
                        ["sh", "-c", "npm install --no-audit --no-fund --loglevel=error && npm run build"],
                        cwd=ROOT / "frontend", optional=True, requires=["npm"]))
    return suites


def _idf_command(project: str) -> tuple[list[str] | None, str]:
    if shutil.which("idf.py"):
        return ["idf.py", "-C", f"firmware/{project}", "build"], ""
    if shutil.which("docker"):
        return ["docker", "run", "--rm", "-v", f"{ROOT / 'firmware'}:/project",
                "-w", f"/project/{project}", IDF_IMAGE, "idf.py", "build"], ""
    return None, "needs idf.py or docker"


# ── Parsing ─────────────────────────────────────────────────────────────────


def parse_junit(path: Path) -> list[CaseResult]:
    """Test cases from a pytest JUnit XML file."""
    cases = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        name = f"{tc.get('classname', '')}::{tc.get('name', '')}".lstrip(":")
        status, message = "passed", ""
        for tag in ("failure", "error", "skipped"):
            node = tc.find(tag)
            if node is not None:
                status = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                message = (node.get("message") or node.text or "").strip().splitlines()[0:1]
                message = message[0] if message else ""
                break
        cases.append(CaseResult(name, status, float(tc.get("time", 0) or 0), message))
    return cases


_OK = re.compile(r"^ok\s+(\S+)", re.M)
_FAIL = re.compile(r"^FAIL\b(.*)$", re.M)


def parse_host_output(text: str) -> list[CaseResult]:
    """Cases from a firmware host test: 'ok   <name>' lines, 'FAIL …', 'PASS <suite>'."""
    cases = [CaseResult(m.group(1), "passed") for m in _OK.finditer(text)]
    for m in _FAIL.finditer(text):
        cases.append(CaseResult("assertion", "failed", message=m.group(1).strip()))
    if not cases and re.search(r"^PASS\s+\S+", text, re.M):
        cases.append(CaseResult(re.search(r"^PASS\s+(\S+)", text, re.M).group(1), "passed"))
    if re.search(r"ERROR: AddressSanitizer|runtime error:|ERROR: UndefinedBehavior", text):
        cases.append(CaseResult("sanitizer", "failed", message="sanitizer reported an error"))
    return cases


# ── Running ─────────────────────────────────────────────────────────────────


def _missing(suite: Suite) -> str:
    return ", ".join(exe for exe in suite.requires if not shutil.which(exe))


def _pytest_available() -> bool:
    try:
        import pytest  # noqa: F401
        return True
    except ImportError:
        return False


def run_suite(suite: Suite, junit_dir: Path | None, verbose: bool) -> SuiteResult:
    cmd = list(suite.cmd)
    if suite.name.startswith("idf:"):
        cmd, why = _idf_command(suite.name.split(":", 1)[1])
        if cmd is None:
            return SuiteResult(suite.name, suite.description, "SKIP", 0.0, reason=why)
    missing = _missing(suite)
    if missing:
        return SuiteResult(suite.name, suite.description, "SKIP", 0.0, reason=f"missing: {missing}")
    if suite.kind == "pytest":
        if not _pytest_available():
            return SuiteResult(suite.name, suite.description, "SKIP", 0.0,
                               reason="pytest not installed (pip install -r backend/requirements-dev.txt)")
        if not (ROOT / suite.cmd[3]).exists():
            return SuiteResult(suite.name, suite.description, "SKIP", 0.0, reason=f"{suite.cmd[3]} not found")

    xml_path = None
    if suite.kind == "pytest":
        out_dir = junit_dir or Path(tempfile.mkdtemp(prefix="impress-junit-"))
        out_dir.mkdir(parents=True, exist_ok=True)
        xml_path = out_dir / f"{suite.name.replace(':', '_')}.xml"
        cmd += [f"--junitxml={xml_path}"]

    env = {**os.environ, **suite.env}
    start = time.perf_counter()
    if verbose:
        print(f"\n$ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=suite.cwd, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seconds = time.perf_counter() - start
    output = proc.stdout or ""
    if verbose:
        print(output)

    if suite.kind == "pytest" and xml_path and xml_path.exists():
        cases = parse_junit(xml_path)
    elif suite.kind == "host":
        cases = parse_host_output(output)
    else:
        cases = [CaseResult(suite.name, "passed" if proc.returncode == 0 else "failed")]

    res = SuiteResult(suite.name, suite.description, "PASS", seconds, cases=cases)
    res.passed = sum(c.status == "passed" for c in cases)
    res.failed = sum(c.status == "failed" for c in cases)
    res.skipped = sum(c.status == "skipped" for c in cases)
    res.errors = sum(c.status == "error" for c in cases)
    if proc.returncode != 0 or res.failed or res.errors:
        res.status = "FAIL"
        res.reason = f"exit code {proc.returncode}"
        res.output_tail = "\n".join(output.rstrip().splitlines()[-25:])
        if proc.returncode != 0 and not (res.failed or res.errors):
            res.errors = 1   # crashed / collection error / build error without parsed cases
    return res


# ── Reporting ───────────────────────────────────────────────────────────────


class Paint:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    def __call__(self, text, code):
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def status(self, s):
        return self({"PASS": " PASS ", "FAIL": " FAIL ", "SKIP": " SKIP "}[s],
                    {"PASS": "30;42", "FAIL": "97;41", "SKIP": "30;43"}[s])


def fmt_secs(s: float) -> str:
    return f"{s:6.1f}s" if s < 60 else f"{int(s // 60)}m{s % 60:04.1f}s"


def print_report(results: list[SuiteResult], wall: float, paint: Paint, slowest: int) -> None:
    w = max(len(r.name) for r in results) + 2
    print()
    print(paint("imPress test report", "1"))
    print(paint(f"{'suite':<{w}} {'status':<8} {'passed':>7} {'failed':>7} {'skipped':>8} {'time':>9}", "2"))
    for r in results:
        failed = r.failed + r.errors
        counts = (f"{r.passed:>7} {paint(f'{failed:>7}', '31') if failed else f'{failed:>7}'} {r.skipped:>8}"
                  if r.status != "SKIP" else f"{'-':>7} {'-':>7} {'-':>8}")
        line = f"{r.name:<{w}} {paint.status(r.status)}  {counts} {fmt_secs(r.seconds):>9}"
        if r.status == "SKIP":
            line += paint(f"  ({r.reason})", "2")
        print(line)

    failures = [r for r in results if r.status == "FAIL"]
    for r in failures:
        print()
        print(paint(f"── {r.name}: {r.reason}", "31;1"))
        bad = [c for c in r.cases if c.status in ("failed", "error")]
        for c in bad[:20]:
            print(paint(f"   ✗ {c.name}", "31") + (f"  — {c.message}" if c.message else ""))
        if r.output_tail:
            print(paint("   last output:", "2"))
            for ln in r.output_tail.splitlines():
                print(paint(f"   │ {ln}", "2"))

    timed = sorted((c for r in results for c in r.cases if c.seconds > 0),
                   key=lambda c: c.seconds, reverse=True)[:slowest]
    if timed:
        print()
        print(paint(f"Slowest {len(timed)} tests", "1"))
        for c in timed:
            print(f"  {fmt_secs(c.seconds)}  {c.name}")

    ran = [r for r in results if r.status != "SKIP"]
    tot = {k: sum(getattr(r, k) for r in ran) for k in ("passed", "failed", "skipped", "errors")}
    print()
    verdict = paint(" ALL PASSED ", "30;42;1") if not failures else paint(f" {len(failures)} SUITE(S) FAILED ", "97;41;1")
    print(f"{verdict}  {len(ran)} suites run, {len(results) - len(ran)} skipped | "
          f"{tot['passed']} passed, {tot['failed'] + tot['errors']} failed, {tot['skipped']} skipped | "
          f"wall time {fmt_secs(wall).strip()}")


def markdown_report(results: list[SuiteResult], wall: float) -> str:
    icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "SKIP": "⏭ SKIP"}
    lines = ["## imPress test report", "",
             "| Suite | Status | Passed | Failed | Skipped | Time |", "|---|---|---:|---:|---:|---:|"]
    for r in results:
        lines.append(f"| `{r.name}` | {icon[r.status]} | {r.passed} | {r.failed + r.errors} | "
                     f"{r.skipped} | {r.seconds:.1f}s |" + (f" {r.reason}" if r.status == "SKIP" else ""))
    for r in (r for r in results if r.status == "FAIL"):
        lines += ["", f"### ❌ {r.name}", ""]
        lines += [f"- `{c.name}` {c.message}" for c in r.cases if c.status in ("failed", "error")][:20]
        if r.output_tail:
            lines += ["", "```", r.output_tail, "```"]
    lines += ["", f"Wall time: {wall:.1f}s"]
    return "\n".join(lines) + "\n"


# ── CLI ─────────────────────────────────────────────────────────────────────


def select(suites: list[Suite], patterns: list[str], with_idf: bool, with_frontend: bool) -> list[Suite]:
    chosen = []
    for s in suites:
        if patterns:
            if any(s.name == p or s.name.startswith(p.rstrip(":") + ":") or s.name.startswith(p) for p in patterns):
                chosen.append(s)
        elif not s.optional or (with_idf and s.name.startswith("idf:")) or (with_frontend and s.name == "frontend"):
            chosen.append(s)
    return chosen


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-s", "--suite", action="append", default=[], help="run suites matching this name/prefix (repeatable)")
    ap.add_argument("--list", action="store_true", help="list suites and exit")
    ap.add_argument("--with-idf", action="store_true", help="also build all firmware with ESP-IDF v6.1")
    ap.add_argument("--with-frontend", action="store_true", help="also build the React frontend")
    ap.add_argument("-x", "--fail-fast", action="store_true", help="stop after the first failing suite")
    ap.add_argument("-v", "--verbose", action="store_true", help="stream each suite's full output")
    ap.add_argument("--slowest", type=int, default=10, help="show the N slowest tests (default 10)")
    ap.add_argument("--json", type=Path, help="write a machine-readable report")
    ap.add_argument("--markdown", type=Path, help="write a Markdown report (default: $GITHUB_STEP_SUMMARY if set)")
    ap.add_argument("--junit-dir", type=Path, help="keep pytest JUnit XML files here")
    ap.add_argument("--no-color", action="store_true", help="disable ANSI colours (also honours NO_COLOR)")
    args = ap.parse_args(argv)

    all_suites = discover()
    if args.list:
        for s in all_suites:
            print(f"{s.name:<28} {'(optional) ' if s.optional else ''}{s.description}")
        return 0
    suites = select(all_suites, args.suite, args.with_idf, args.with_frontend)
    if not suites:
        print(f"no suite matches {args.suite}; use --list", file=sys.stderr)
        return 2

    color = (not args.no_color and "NO_COLOR" not in os.environ
             and (sys.stdout.isatty() or os.environ.get("FORCE_COLOR") or os.environ.get("GITHUB_ACTIONS")))
    if platform.system() == "Windows" and color:
        os.system("")  # enable ANSI escape processing on Windows terminals
    paint = Paint(bool(color))

    results: list[SuiteResult] = []
    wall_start = time.perf_counter()
    for suite in suites:
        print(f"{paint('▶', '36')} {suite.name:<28} {paint(suite.description, '2')}", flush=True)
        res = run_suite(suite, args.junit_dir, args.verbose)
        results.append(res)
        print(f"  {paint.status(res.status)} {fmt_secs(res.seconds).strip()}"
              + (f"  {res.passed} passed" if res.status != "SKIP" else f"  {res.reason}")
              + (paint(f", {res.failed + res.errors} failed", "31") if res.failed + res.errors else ""), flush=True)
        if args.fail_fast and res.status == "FAIL":
            break
    wall = time.perf_counter() - wall_start

    print_report(results, wall, paint, args.slowest)
    if args.json:
        args.json.write_text(json.dumps({
            "wall_seconds": round(wall, 3),
            "ok": not any(r.status == "FAIL" for r in results),
            "suites": [{**asdict(r), "total": r.total} for r in results],
        }, indent=2))
    md_target = args.markdown or (Path(os.environ["GITHUB_STEP_SUMMARY"]) if os.environ.get("GITHUB_STEP_SUMMARY") else None)
    if md_target:
        with md_target.open("a") as fh:
            fh.write(markdown_report(results, wall))
    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
