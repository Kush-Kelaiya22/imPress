"""Backups an administrator can see, save and restore (v2.2).

Two kinds of copy live in the backup folder (services/integrity.py): the automatic ones (start-up, rolling,
forensic, before a clear or a restore) and the **named** ones an administrator saves from the web app.
A named backup is the database plus a small description of the **system state** at that moment (version,
profile, the effective policy, what the tables held), so you can see what you would be going back to.

Restoring replaces the live database with the chosen copy (after verifying that the copy itself verifies, and
after keeping a `before-restore` copy of what was there), then signs everyone out of the old state. It is a
dangerous action: it needs the account's password and a typed confirmation, and in the hardened profile a
second super admin's approval (policy backups.restore_requires_approval).
"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from .. import gpc
from ..config import APP_VERSION
from ..timeutil import istnow
from . import events, integrity

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,47}$")
KINDS = {"saved": "Saved", "startup": "Start-up", "rolling": "Rolling (last good)", "forensic": "Failed database kept",
         "before-clear": "Taken before a clear", "before-restore": "Taken before a restore"}
COUNTED = ("users", "students", "class_sessions", "quizzes", "polls", "quiz_answers", "poll_votes", "attendance",
           "esp_devices", "firmware_artifacts", "activity_logs")


class BackupError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def saved_dir() -> Path:
    d = integrity.backup_dir() / "saved"
    d.mkdir(exist_ok=True)
    try:
        d.chmod(0o700)
    except OSError:
        pass
    return d


def system_state() -> dict:
    return {"version": APP_VERSION, "profile": gpc.profile(),
            "policy": {f["name"]: f["value"] for f in gpc.describe()["flags"]}, "taken_at": istnow().isoformat()}


def _counts(path: Path) -> dict:
    out: dict = {}
    try:
        with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as c:
            for t in COUNTED:
                try:
                    out[t] = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                except sqlite3.DatabaseError:
                    pass
            try:
                out["schema_version"] = c.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
                out["super_admins"] = c.execute("SELECT COUNT(*) FROM users WHERE role = 'super_admin' AND is_active = 1").fetchone()[0]
            except sqlite3.DatabaseError:
                pass
    except sqlite3.DatabaseError:
        out["unreadable"] = True
    return out


def _kind_of(path: Path) -> str:
    n = path.name
    if path.parent.name == "saved":
        return "saved"
    for prefix, kind in (("forensic-", "forensic"), ("before-clear-", "before-clear"), ("before-restore-", "before-restore")):
        if n.startswith(prefix):
            return kind
    return "startup" if n == "startup.db" else "rolling" if n == "rolling.db" else "other"


def _files() -> list[Path]:
    d = integrity.backup_dir()
    found = [p for p in (d / "startup.db", d / "rolling.db") if p.exists()]
    found += sorted(d.glob("forensic-*.db"), reverse=True) + sorted(d.glob("before-clear-*.db"), reverse=True)
    found += sorted(d.glob("before-restore-*.db"), reverse=True) + sorted(saved_dir().glob("*.db"), reverse=True)
    return found


def _entry(path: Path, with_counts: bool = False) -> dict:
    st = path.stat()
    kind = _kind_of(path)
    meta = {}
    if kind == "saved":
        try:
            meta = json.loads(path.with_suffix(".json").read_text())
        except (OSError, ValueError):
            pass
    out = {"id": f"{kind}/{path.stem if kind == 'saved' else path.name}", "kind": kind, "label": KINDS.get(kind, kind),
           "name": meta.get("name") or (path.stem if kind == "saved" else path.name), "file": path.name,
           "size": st.st_size, "modified": istnow().fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
           "by": meta.get("by", ""), "note": meta.get("note", "")}
    if with_counts:
        out["counts"] = _counts(path)
        out["system"] = meta.get("system")
    return out


def listing() -> list[dict]:
    return [_entry(p) for p in _files()]


def resolve(backup_id: str) -> Path:
    for p in _files():
        if _entry(p)["id"] == backup_id:
            return p
    raise BackupError("NO_BACKUP", "No such backup", 404)


def describe(backup_id: str) -> dict:
    return _entry(resolve(backup_id), with_counts=True)


async def save(name: str, by: str, note: str = "") -> dict:
    name = name.strip()
    if not NAME_RE.match(name):
        raise BackupError("BAD_NAME", "Name: 1-48 letters, digits, spaces, . _ -", 422)
    dst = saved_dir() / f"{name}.db"
    if dst.exists():
        raise BackupError("NAME_TAKEN", f"A backup named {name} exists already", 409)
    async with integrity._lock:
        rep = await integrity.verify_now()
        if not rep.ok:
            raise BackupError("DB_NOT_VERIFIED", "The database does not verify (" + rep.summary() + "): resolve that before saving a backup", 409)
        await integrity.copy_live_to(dst)
    dst.with_suffix(".json").write_text(json.dumps({"name": name, "by": by, "note": note[:200], "system": system_state(),
                                                    "created_at": istnow().isoformat()}))
    try:
        dst.with_suffix(".json").chmod(0o600)
    except OSError:
        pass
    return _entry(dst, with_counts=True)


def delete(backup_id: str) -> None:
    p = resolve(backup_id)
    if _kind_of(p) != "saved":
        raise BackupError("NOT_DELETABLE", "Only backups you saved can be deleted: the automatic ones manage themselves", 409)
    p.unlink(missing_ok=True)
    p.with_suffix(".json").unlink(missing_ok=True)


async def restore(backup_id: str, by: str) -> dict:
    """Replace the live database with the chosen copy. Returns what happened."""
    src = resolve(backup_id)
    async with integrity._lock:
        probe = integrity_copy_check(src)
        if probe:
            raise BackupError("BACKUP_UNREADABLE", f"That backup can't be used: {probe}", 409)
        before = integrity.backup_dir() / f"before-restore-{istnow():%Y%m%d-%H%M%S}.db"
        await integrity.copy_live_to(before)
        await integrity.restore_from(src)
        rep = await integrity.verify_now()
        if not rep.ok:                                      # a copy that does not verify is never accepted
            await integrity.restore_from(before)
            await integrity.verify_now()
            raise BackupError("BACKUP_DOES_NOT_VERIFY", "That backup does not verify (" + rep.summary()
                              + "): nothing was changed", 409)
        await integrity.check_and_backup_locked()
    events.alert(f"{by} restored the system from the backup '{_entry(src)['name']}'. Everyone is signed out.", "warning", "all")
    events.status({"restored": True})
    return {"restored": _entry(src)["name"], "kept": before.name}


def integrity_copy_check(path: Path) -> str:
    try:
        with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as c:
            if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                return "SQLite's own integrity check failed"
            c.execute("SELECT COUNT(*) FROM users").fetchone()
    except sqlite3.DatabaseError as exc:
        return str(exc)
    return ""
