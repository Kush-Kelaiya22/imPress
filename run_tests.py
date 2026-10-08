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
import signal
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Same pinned image as the CI build job (tag for humans, digest for reproducibility).
IDF_IMAGE = "espressif/idf:v6.1@sha256:81893c71bb5e570088901f21def8684c25cd2a9020281bd01b843a7655edb18c"
IDF_PROJECTS = ("class_c6", "class_s3", "student")
HEARTBEAT_SECONDS = 30.0      # progress line interval when stdout is not a terminal (CI)

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
    pip_requires: str = ""    # requirements file whose packages must be installed


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
    coverage: float | None = None   # line coverage %, when --coverage was used

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped + self.errors


# ── Discovery ───────────────────────────────────────────────────────────────


DEV_REQUIREMENTS = "backend/requirements-dev.txt"


def _pytest_suite(name, path, description, pip_requires=DEV_REQUIREMENTS):
    return Suite(name, "pytest", description,
                 [sys.executable, "-m", "pytest", path, "-q", "-p", "no:cacheprovider",
                  "-W", "ignore::DeprecationWarning"],
                 env={"PYTHONDONTWRITEBYTECODE": "1"}, pip_requires=pip_requires)


def discover() -> list[Suite]:
    suites = [
        _pytest_suite("backend", "backend/tests", "Backend API, services and security (pytest)"),
        _pytest_suite("firmware-static", "firmware/tests", "Firmware structural guards (pytest)", pip_requires=""),
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
    # npm ci installs exactly the committed lockfile and never rewrites it
    install = ("npm ci --no-audit --no-fund --loglevel=error" if (ROOT / "frontend/package-lock.json").exists()
               else "npm install --no-audit --no-fund --no-package-lock --loglevel=error")
    suites.append(Suite("frontend", "cmd", "Frontend build (npm ci + vite build)",
                        ["sh", "-c", f"{install} && npm run build"],
                        cwd=ROOT / "frontend", optional=True, requires=["npm"]))
    return suites


def _idf_command(project: str) -> tuple[list[str] | None, str]:
    if shutil.which("idf.py"):
        return ["idf.py", "-C", f"firmware/{project}", "build"], ""
    if shutil.which("docker"):
        try:
            up = subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
        except subprocess.TimeoutExpired:
            up = False
        if not up:
            return None, "docker daemon not reachable (start Docker Desktop or install ESP-IDF)"
        # --init: idf.py would otherwise be PID 1 and ignore the SIGTERM sent on Ctrl-C / timeout
        return ["docker", "run", "--rm", "--init", "-v", f"{ROOT / 'firmware'}:/project",
                "-w", f"/project/{project}", IDF_IMAGE, "idf.py", "build"], ""
    return None, "needs idf.py or docker"


def _idf_image_present() -> bool:
    return subprocess.run(["docker", "image", "inspect", IDF_IMAGE], capture_output=True).returncode == 0


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


def _requirements(path: Path) -> list[str]:
    """Distribution names from a requirements file, following -r includes."""
    names = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("-r"):
            names += _requirements(path.parent / line[2:].strip())
        elif line and not line.startswith("-"):
            names.append(re.split(r"[\[<>=!~;\s]", line, maxsplit=1)[0])
    return names


def missing_packages(requirements: str) -> list[str]:
    """Packages from `requirements` (plus pytest) not installed in this interpreter."""
    from importlib.metadata import PackageNotFoundError, distribution
    names = ["pytest"] + (_requirements(ROOT / requirements) if requirements else [])
    missing = []
    for name in dict.fromkeys(names):
        try:
            distribution(name)
        except PackageNotFoundError:
            missing.append(name)
    return missing


def _stop(proc: subprocess.Popen) -> None:
    """Terminate the child and everything it started (npm, ninja, docker run)."""
    try:
        if os.name == "nt":
            proc.terminate()
        else:
            os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if os.name != "nt":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()


def run_streaming(cmd, cwd, env, verbose=False, live=False, timeout=0.0) -> tuple[int, str, str]:
    """Run `cmd` and return (exit code, combined output, abort reason).

    Output is read on a thread so the caller can show progress while the child runs:
    `verbose` echoes everything, `live` keeps one status line (elapsed time + latest
    output) on a terminal, otherwise a heartbeat is printed every HEARTBEAT_SECONDS.
    Ctrl-C or `timeout` stops the whole process group; the reason is returned.
    """
    group = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
             else {"start_new_session": True})
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **group)
    chunks: list[bytes] = []
    latest = [""]

    def reader():
        tail = b""
        for data in iter(lambda: proc.stdout.read1(4096), b""):
            chunks.append(data)
            if verbose:
                sys.stdout.write(data.decode(errors="replace"))
                sys.stdout.flush()
            tail = (tail + data)[-4096:]
            lines = [ln for ln in re.split(rb"[\r\n]", tail) if ln.strip()]
            if lines:
                latest[0] = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", lines[-1].decode(errors="replace")).strip()

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    start, next_beat, aborted = time.perf_counter(), HEARTBEAT_SECONDS, ""
    width = shutil.get_terminal_size((100, 20)).columns - 1
    try:
        while proc.poll() is None:
            time.sleep(0.25)
            elapsed = time.perf_counter() - start
            if timeout and elapsed > timeout:
                aborted = f"timed out after {fmt_secs(timeout).strip()}"
                _stop(proc)
                break
            if live:
                sys.stdout.write("\r" + f"   ... {fmt_secs(elapsed).strip():>7}  {latest[0]}"[:width].ljust(width))
                sys.stdout.flush()
            elif not verbose and elapsed >= next_beat:
                print(f"   ... still running ({fmt_secs(elapsed).strip()}): {latest[0][:120]}", flush=True)
                next_beat += HEARTBEAT_SECONDS
    except KeyboardInterrupt:
        aborted = "interrupted"
        _stop(proc)
    except BaseException:                 # e.g. BrokenPipeError on the status line
        _stop(proc)                       # never leave the suite running orphaned
        raise
    finally:
        if live:
            sys.stdout.write("\r" + " " * width + "\r")
            sys.stdout.flush()
    proc.wait()
    thread.join(timeout=5)
    return proc.returncode, b"".join(chunks).decode(errors="replace"), aborted


COVERAGE_SOURCES = {"backend": "backend/app"}   # pytest suites measured with --coverage


def parse_coverage(path: Path) -> float:
    """Total line coverage (%) from a Cobertura XML report (pytest-cov)."""
    return round(float(ET.parse(path).getroot().get("line-rate", 0)) * 100, 1)


def run_suite(suite: Suite, junit_dir: Path | None, verbose: bool, live: bool = False,
              timeout: float = 0.0, coverage_dir: Path | None = None) -> SuiteResult:
    cmd = list(suite.cmd)
    if suite.name.startswith("idf:"):
        cmd, why = _idf_command(suite.name.split(":", 1)[1])
        if cmd is None:
            return SuiteResult(suite.name, suite.description, "SKIP", 0.0, reason=why)
        if cmd[0] == "docker" and not _idf_image_present():
            print(f"   note: pulling {IDF_IMAGE} (several GB, first run only)", flush=True)
    missing = _missing(suite)
    if missing:
        return SuiteResult(suite.name, suite.description, "SKIP", 0.0, reason=f"missing: {missing}")
    if suite.kind == "pytest":
        if not (ROOT / suite.cmd[3]).exists():
            return SuiteResult(suite.name, suite.description, "SKIP", 0.0, reason=f"{suite.cmd[3]} not found")
        # Mandatory suites: a missing package is one clear FAIL, not a skip (a skip
        # would hide a broken install in CI) and not hundreds of per-test errors.
        missing_pkgs = missing_packages(suite.pip_requires)
        if missing_pkgs:
            req = suite.pip_requires or "pytest"
            return SuiteResult(suite.name, suite.description, "FAIL", 0.0, errors=1,
                               reason=f"missing Python packages: {', '.join(missing_pkgs)}",
                               output_tail=f"{sys.executable} has no {', '.join(missing_pkgs)}.\n"
                                           f"Install with:  {sys.executable} -m pip install -r {req}\n"
                                           f"(or activate the venv that has them and rerun)"
                                           if suite.pip_requires else
                                           f"Install with:  {sys.executable} -m pip install pytest")

    xml_path = None
    if suite.kind == "pytest":
        out_dir = junit_dir or Path(tempfile.mkdtemp(prefix="impress-junit-"))
        out_dir.mkdir(parents=True, exist_ok=True)
        xml_path = out_dir / f"{suite.name.replace(':', '_')}.xml"
        cmd += [f"--junitxml={xml_path}"]
    cov_xml = None
    if coverage_dir and suite.name in COVERAGE_SOURCES:
        coverage_dir.mkdir(parents=True, exist_ok=True)
        cov_xml = coverage_dir / f"coverage-{suite.name}.xml"
        cmd += [f"--cov={COVERAGE_SOURCES[suite.name]}", f"--cov-report=xml:{cov_xml}", "--cov-report="]

    env = {**os.environ, "PYTHONUNBUFFERED": "1", **suite.env}
    start = time.perf_counter()
    if verbose:
        print(f"\n$ {' '.join(cmd)}", flush=True)
    returncode, output, aborted = run_streaming(cmd, suite.cwd, env, verbose, live, timeout)
    seconds = time.perf_counter() - start

    if suite.kind == "pytest" and xml_path and xml_path.exists():
        cases = parse_junit(xml_path)
    elif suite.kind == "host":
        cases = parse_host_output(output)
    else:
        cases = [CaseResult(suite.name, "passed" if returncode == 0 else "failed")]

    res = SuiteResult(suite.name, suite.description, "PASS", seconds, cases=cases)
    if cov_xml and cov_xml.exists():
        res.coverage = parse_coverage(cov_xml)
    res.passed = sum(c.status == "passed" for c in cases)
    res.failed = sum(c.status == "failed" for c in cases)
    res.skipped = sum(c.status == "skipped" for c in cases)
    res.errors = sum(c.status == "error" for c in cases)
    if returncode != 0 or res.failed or res.errors:
        res.status = "FAIL"
        res.reason = aborted or f"exit code {returncode}"
        res.output_tail = "\n".join(output.rstrip().splitlines()[-25:])
        if aborted and not (res.failed or res.errors):
            res.cases.append(CaseResult(suite.name, "error", seconds, aborted))
            res.errors = 1
        elif returncode != 0 and not (res.failed or res.errors):
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

    timed = sorted((c for r in results for c in r.cases if c.seconds >= 0.05),
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
    covered = [r for r in results if r.coverage is not None]
    if covered:
        lines += ["", "| Coverage | Lines |", "|---|---:|"]
        lines += [f"| `{r.name}` ({COVERAGE_SOURCES.get(r.name, '')}) | {r.coverage}% |" for r in covered]
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
    ap.add_argument("--timeout", type=float, default=0, metavar="SECONDS",
                    help="stop a suite that runs longer than this (default: no limit)")
    ap.add_argument("--slowest", type=int, default=10, help="show the N slowest tests (default 10)")
    ap.add_argument("--json", type=Path, help="write a machine-readable report")
    ap.add_argument("--markdown", type=Path, help="write a Markdown report (default: $GITHUB_STEP_SUMMARY if set)")
    ap.add_argument("--junit-dir", type=Path, help="keep pytest JUnit XML files here")
    ap.add_argument("--coverage", type=Path, metavar="DIR",
                    help="measure backend line coverage (pytest-cov); XML report written to DIR")
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
        try:
            res = run_suite(suite, args.junit_dir, args.verbose,
                            live=sys.stdout.isatty() and not args.verbose, timeout=args.timeout,
                            coverage_dir=args.coverage)
        except KeyboardInterrupt:   # Ctrl-C outside the child process (preflight, parsing)
            res = SuiteResult(suite.name, suite.description, "FAIL", 0.0, errors=1, reason="interrupted")
        results.append(res)
        print(f"  {paint.status(res.status)} {fmt_secs(res.seconds).strip()}"
              + (f"  {res.passed} passed" if res.status != "SKIP" else f"  {res.reason}")
              + (paint(f", {res.failed + res.errors} failed", "31") if res.failed + res.errors else "")
              + (f", coverage {res.coverage}%" if res.coverage is not None else "")
              + (paint(f"  ({res.reason})", "31") if res.status == "FAIL" and not res.reason.startswith("exit code")
                 else ""), flush=True)
        if res.reason == "interrupted":
            print(paint("   interrupted: remaining suites not run", "33"), flush=True)
            break
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
    if any(r.reason == "interrupted" for r in results):
        return 130
    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # stdout was piped into something that stopped reading (`| head`)
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
