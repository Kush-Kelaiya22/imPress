"""scripts/backup.sh: a consistent, checksummed archive of the database, firmware and .env."""

import sqlite3
import subprocess
import tarfile

from conftest import ROOT


def _run(tmp_path, *extra):
    db = tmp_path / "impress.db"
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE t (x TEXT)")
        c.execute("INSERT INTO t VALUES ('hello')")
    (tmp_path / "fw").mkdir(exist_ok=True)
    (tmp_path / "fw" / "a.bin").write_bytes(b"image")
    (tmp_path / "env").write_text("IMPRESS_JWT_SECRET=x\n")
    dest = tmp_path / "dest"
    return dest, subprocess.run(["bash", str(ROOT / "scripts/backup.sh"), "--db", str(db), "--firmware", str(tmp_path / "fw"),
                                 "--env", str(tmp_path / "env"), "--dest", str(dest), *extra], capture_output=True, text=True)


def test_the_backup_is_complete_checksummed_and_restorable(tmp_path):
    dest, r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "NOT encrypted" in r.stderr                              # .env inside: the script says so
    archive = next(dest.glob("impress-backup-*.tar.gz"))
    assert oct(archive.stat().st_mode & 0o777) == "0o600"
    check = subprocess.run(["shasum", "-a", "256", "-c", archive.name + ".sha256"], cwd=dest, capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    out = tmp_path / "restore"
    with tarfile.open(archive) as t:
        t.extractall(out, filter="data")
    root = next(out.iterdir())
    assert {p.name for p in root.iterdir()} == {"impress.db", "firmware_bins", "dot-env", "MANIFEST.sha256"}
    with sqlite3.connect(root / "impress.db") as c:
        assert c.execute("SELECT x FROM t").fetchone()[0] == "hello"
    assert (root / "firmware_bins" / "a.bin").read_bytes() == b"image"


def test_it_refuses_without_a_destination_or_a_database(tmp_path):
    r = subprocess.run(["bash", str(ROOT / "scripts/backup.sh"), "--db", str(tmp_path / "nope.db"), "--dest", str(tmp_path / "d")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "database not found" in r.stderr
    assert subprocess.run(["bash", str(ROOT / "scripts/backup.sh")], capture_output=True).returncode == 2
