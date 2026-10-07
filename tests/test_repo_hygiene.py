"""Nothing generated at runtime or compiled is tracked; scripts are portable."""

import re

from conftest import ROOT, git

import run_tests

GENERATED = re.compile(r"(\.(db|sqlite3?|pyc|pyo|log|elf|map|o|a)$|\.db\.bak|__pycache__/|/build/|node_modules/|"
                       r"(^|/)\.env$|sdkconfig\.old$|\.DS_Store$)")


def test_no_generated_or_compiled_files_tracked(tracked_files):
    bad = [f for f in tracked_files if GENERATED.search(f)]
    assert bad == []


def test_no_tracked_file_is_gitignored(tracked_files):
    assert git("ls-files", "-ci", "--exclude-standard").split() == []


def test_runtime_paths_are_ignored(tracked_files):
    for path in ("backend/impress.db", "logs/x.log", "backend/.env", "firmware/class_c6/build/x.bin",
                 "backend/app/__pycache__/x.pyc", "frontend/node_modules/x", "backend/firmware_bins/s3-1.0.0.bin"):
        assert git("check-ignore", "-q", path) == "", path
    assert "backend/.env.example" in tracked_files


def test_shell_scripts_are_executable_with_shebang_and_lf(tracked_files):
    modes = {line.split()[3]: line.split()[0] for line in git("ls-files", "-s", "*.sh").splitlines()
             if "managed_components/" not in line}           # vendored ESP-IDF components aren't ours
    assert modes, "expected tracked shell scripts"
    for path, mode in modes.items():
        assert mode == "100755", f"{path} is not executable in git"
        raw = (ROOT / path).read_bytes()
        assert raw.startswith(b"#!/usr/bin/env bash"), path
        assert b"\r\n" not in raw, f"{path} has CRLF line endings"


def test_gitattributes_enforces_lf_and_binaries():
    text = (ROOT / ".gitattributes").read_text()
    assert "* text=auto eol=lf" in text and "*.sh      text eol=lf" in text and "*.bin     binary" in text


def test_runner_discovers_every_host_suite():
    scripts = sorted((ROOT / "firmware").glob("*/test_host/run*.sh"))
    host = [s for s in run_tests.discover() if s.kind == "host"]
    assert len(host) == len(scripts) >= 6


def test_run_tests_is_executable_entry_point(tracked_files):
    line = next(line for line in git("ls-files", "-s", "run_tests.py").splitlines())
    assert line.startswith("100755")
    assert (ROOT / "run_tests.py").read_text().startswith("#!/usr/bin/env python3")
