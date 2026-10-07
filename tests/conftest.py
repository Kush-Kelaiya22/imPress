"""Shared helpers for repository-level tests (CI, hygiene, docs, test runner)."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))          # import run_tests
sys.path.insert(0, str(ROOT / "backend"))


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


@pytest.fixture(scope="session")
def tracked_files() -> list[str]:
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    return git("ls-files").splitlines()


@pytest.fixture(scope="session")
def workflow():
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
