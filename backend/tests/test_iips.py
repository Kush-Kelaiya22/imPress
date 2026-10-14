"""IIPS: the program's own files are hashed at first start and checked at every later one."""

import json

import pytest

from app.services import iips


@pytest.fixture
def tree(tmp_path, monkeypatch):
    root = tmp_path / "src"
    (root / "backend/app/sub").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "backend/app/a.py").write_text("a = 1\n")
    (root / "backend/app/sub/b.py").write_text("b = 2\n")
    (root / "scripts/run.sh").write_text("echo hi\n")
    (root / "VERSION").write_text("2.2.0\n")
    monkeypatch.setattr(iips, "baseline_path", lambda: tmp_path / "state" / "x.iips.json")
    return root


def _check(root, **kw):
    return iips.check(root=root, **kw)


def test_first_start_makes_the_baseline_and_the_next_passes(tree):
    assert _check(tree)["status"] == "baseline_created"
    assert _check(tree)["status"] == "ok"
    saved = json.loads(iips.baseline_path().read_text())["baseline"]
    assert "backend/app/sub/b.py" in saved["files"] and "backend/app/sub" in saved["folders"] and saved["root_hash"]


@pytest.mark.parametrize("edit,kind", [
    (lambda r: (r / "backend/app/a.py").write_text("a = 2\n"), "changed"),
    (lambda r: (r / "backend/app/new.py").write_text("x"), "added"),
    (lambda r: (r / "scripts/run.sh").unlink(), "removed"),
])
def test_any_difference_disables(tree, edit, kind):
    _check(tree)
    edit(tree)
    st = _check(tree)
    assert st["status"] == "violation" and st["changes"][0]["change"] == kind and iips.locked()
    assert "disabled by Root" in iips.violation_message() and "--rehash" in iips.violation_message()


def test_moving_a_folder_is_flagged_even_though_no_file_changed(tree):
    _check(tree)
    (tree / "scripts/sub").mkdir()
    (tree / "backend/app/sub/b.py").rename(tree / "scripts/sub/b.py")
    st = _check(tree)
    assert st["status"] == "violation" and {"path": "backend/app/sub/b.py", "change": "moved", "to": "scripts/sub/b.py"} in st["changes"]


def test_rehash_accepts_the_current_files_and_bypass_skips(tree):
    _check(tree)
    (tree / "backend/app/a.py").write_text("changed\n")
    assert _check(tree, rehash=True)["status"] == "rehashed" and _check(tree)["status"] == "ok"
    (tree / "backend/app/a.py").write_text("changed again\n")
    assert _check(tree, enabled=False)["status"] == "bypassed" and not iips.locked()


def test_caches_databases_and_logs_are_not_covered(tree):
    _check(tree)
    (tree / "backend/app/__pycache__").mkdir()
    (tree / "backend/app/__pycache__/a.pyc").write_bytes(b"\x00")
    (tree / "backend/app/impress.db").write_bytes(b"db")
    (tree / "backend/app/server.log").write_text("x")
    assert _check(tree)["status"] == "ok"


def test_a_hand_edited_baseline_does_not_help(tree):
    _check(tree)
    (tree / "backend/app/a.py").write_text("evil\n")
    doc = json.loads(iips.baseline_path().read_text())
    doc["baseline"]["files"]["backend/app/a.py"] = iips.snapshot(tree)["files"]["backend/app/a.py"]
    iips.baseline_path().write_text(json.dumps(doc))
    assert _check(tree)["status"] == "violation"


def test_this_programs_own_files_pass_at_the_second_check(tmp_path, monkeypatch):
    monkeypatch.setattr(iips, "baseline_path", lambda: tmp_path / "own.iips.json")
    assert iips.check()["status"] == "baseline_created" and iips.check()["status"] == "ok"
