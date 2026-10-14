"""Debug (test) mode (v2.2): work on a copy of the database with test data.

Turning it on (super admin only):
  1. the database must verify (dbgateway seals); otherwise it is refused;
  2. the real database is copied to test-data/snapshots/ and its SHA-256
     recorded;
  3. imPress keeps running on the live file, which from now on is the
     sandbox (a copy of the real data, or a saved dataset loaded into it);
  4. every page shows the test-mode banner (GET /api/system/status).

Turning it off:
  1. the sandbox is set aside in test-data/pending/;
  2. the real snapshot is checked against its SHA-256 and restored;
  3. the super admin's own sign-in is carried over; everyone else who
     signed in during test mode signs in again;
  4. the integrity backups are refreshed from the real data, so they never
     hold test data;
  5. the super admin then saves the test data as a dataset (it can be loaded
     again when test mode is next turned on), exports it as sheet-format CSV
     files, or deletes it.

Gateways and modules keep reporting while test mode is on; what they send
goes into the test data and is not kept in the real database.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import secrets
import sqlite3
from contextlib import closing
import zipfile
from pathlib import Path

from .. import gpc, signing
from ..timeutil import istnow
from . import events, integrity

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,47}$")


class TestModeError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


def _root() -> Path:
    db = integrity.db_path()
    d = (db.parent if db else Path(".")) / "test-data"
    for sub in ("snapshots", "pending", "datasets"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    for path in (d, d / "snapshots", d / "pending", d / "datasets"):
        _private(path, 0o700)                       # copies of the data: the server's user only
    return d


def _private(path: Path, mode: int = 0o600) -> None:
    try:
        os.chmod(path, mode)
    except OSError:                                   # e.g. a filesystem without permissions
        pass


def test_password() -> str | None:
    """The password generated teachers get while debug mode is on: random for
    each debug-mode session, so a published default can't open the accounts
    of a server that is being tested."""
    tm = integrity.read_state().get("test_mode") or {}
    return tm.get("password") if tm.get("on") else None


def state() -> dict:
    tm = integrity.read_state().get("test_mode") or {}
    return {"on": bool(tm.get("on")), "since": tm.get("since"), "by": tm.get("by"),
            "forced": bool(gpc.get("test_mode.forced")), "pending": _pending(), "datasets": datasets()}


def _pending() -> list[dict]:
    out = []
    for p in sorted((_root() / "pending").glob("*.db")):
        out.append({"id": p.stem, "size": p.stat().st_size})
    return out


def datasets() -> list[dict]:
    out = []
    for p in sorted((_root() / "datasets").glob("*.db")):
        meta = {}
        try:
            meta = json.loads(p.with_suffix(".json").read_text())
        except (OSError, ValueError):
            pass
        out.append({"name": p.stem, "size": p.stat().st_size, **meta})
    return out


async def _carry_session(source: Path, token_hash: str | None, user_id: int) -> None:
    """Copy the acting super admin's account and session from `source` into the
    live database (through the gateway, as the system)."""
    if not token_hash:
        return
    from sqlalchemy import select
    from ..database import async_session
    from ..dbgateway import SYSTEM, act_as
    from ..models import User, UserSession
    act_as(SYSTEM)
    with closing(sqlite3.connect(str(source))) as s:
        s.row_factory = sqlite3.Row
        srow = s.execute("SELECT * FROM user_sessions WHERE token_hash = ?", (token_hash,)).fetchone()
        urow = s.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if srow is None or urow is None:
        return
    async with async_session() as db:
        user = await db.get(User, user_id)
        if user is None or user.username != urow["username"]:
            return                                       # not the same account: don't carry anything
        existing = (await db.execute(select(UserSession).where(UserSession.token_hash == token_hash))).scalar_one_or_none()
        if existing is None:
            cols = {c.name for c in UserSession.__table__.columns} - {"id"}
            db.add(UserSession(**{k: _parse(UserSession.__table__.columns[k], srow[k]) for k in cols if k in srow.keys()}))
        else:
            existing.revoked = False
            existing.last_activity_at = istnow()
        await db.commit()


def _parse(col, v):
    from sqlalchemy import DateTime
    from datetime import datetime
    if v is not None and isinstance(col.type, DateTime) and isinstance(v, str):
        return datetime.fromisoformat(v)
    return v


async def _refresh_backups() -> None:
    d = integrity.backup_dir()
    await integrity.copy_live_to(d / "startup.db")
    await integrity.copy_live_to(d / "rolling.db")


async def enable(user, session, dataset: str | None = None) -> dict:
    if state()["on"]:
        raise TestModeError("ALREADY_ON", "Debug mode is already on")
    async with integrity._lock:
        rep = await integrity.verify_now()
        if not rep.ok:
            raise TestModeError("DB_NOT_VERIFIED", "The database does not verify (" + rep.summary() + "). "
                                "Resolve the Degraded state before turning on debug mode.")
        ts = f"{istnow():%Y%m%d-%H%M%S}"
        snap = _root() / "snapshots" / f"real-{ts}.db"
        await integrity.copy_live_to(snap)
        sha = integrity.file_sha256(snap)
        if dataset:
            src = _root() / "datasets" / f"{dataset}.db"
            if not src.exists():
                snap.unlink(missing_ok=True)
                raise TestModeError("NO_DATASET", f"No saved dataset named {dataset}", 404)
            await integrity.restore_from(src)
            if user is not None:
                await _carry_session(snap, getattr(session, "token_hash", None), user.id)
            if not (await integrity.verify_now()).ok:
                await integrity.reseal_everything(f"dataset {dataset} loaded")
        integrity.write_state(test_mode={"on": True, "since": istnow().isoformat(), "by": user.username if user else "root",
                                         "forced": user is None,
                                         "snapshot": snap.name, "sha256": sha, "dataset": dataset,
                                         "password": secrets.token_urlsafe(9)})
        await _refresh_backups()
    events.status({"test_mode": True})
    events.alert("Debug mode is on: imPress is running on test data. Changes are not kept in the real database.",
                 "warning", "all")
    return state()


FORCED_MESSAGE = ("Test mode was enabled by root and cannot be disabled. "
                  "This is intentional application design.")


async def ensure_forced() -> None:
    """Start-up with --test-mode: test mode is on, whatever it was, and stays on."""
    if not state()["on"]:
        await enable(None, None, None)


async def disable(user, session) -> dict:
    if gpc.get("test_mode.forced"):
        raise TestModeError("TEST_MODE_FORCED", FORCED_MESSAGE, 403)
    tm = integrity.read_state().get("test_mode") or {}
    if not tm.get("on"):
        raise TestModeError("ALREADY_OFF", "Debug mode is not on")
    snap = _root() / "snapshots" / tm["snapshot"]
    if not snap.exists() or integrity.file_sha256(snap) != tm.get("sha256"):
        events.alert("The saved copy of the real database is missing or was changed; debug mode stays on. "
                     "Restore it from a backup before turning debug mode off.", "error")
        raise TestModeError("SNAPSHOT_CHANGED", "The saved copy of the real database is missing or was changed "
                            "outside imPress; debug mode stays on.", 500)
    async with integrity._lock:
        pending = _root() / "pending" / f"test-{istnow():%Y%m%d-%H%M%S}.db"
        await integrity.copy_live_to(pending)
        await integrity.restore_from(snap)
        await _carry_session(pending, getattr(session, "token_hash", None), user.id)
        if not (await integrity.verify_now()).ok:
            raise TestModeError("RESTORE_FAILED", "The real database was restored but does not verify; "
                                "it is Degraded. See the integrity panel.", 500)
        integrity.write_state(test_mode={"on": False})
        await _refresh_backups()
        snap.unlink(missing_ok=True)
    events.status({"test_mode": False})
    events.alert("Debug mode is off: imPress is back on the real data.", "info", "all")
    return {**state(), "pending_id": pending.stem}


def _pending_path(pid: str) -> Path:
    p = _root() / "pending" / f"{pid}.db"
    if not re.fullmatch(r"test-\d{8}-\d{6}", pid) or not p.exists():
        raise TestModeError("NO_PENDING", "No such test data waiting for a decision", 404)
    return p


def save_pending(pid: str, name: str, by: str) -> dict:
    src = _pending_path(pid)
    if not NAME_RE.match(name or ""):
        raise TestModeError("BAD_NAME", "Name: 1-48 letters, digits, spaces, . _ -", 422)
    dst = _root() / "datasets" / f"{name}.db"
    if dst.exists():
        raise TestModeError("NAME_TAKEN", f"A dataset named {name} exists already")
    src.replace(dst)
    counts = counts_in(dst)
    meta = dst.with_suffix(".json")
    meta.write_text(json.dumps({"saved_at": istnow().isoformat(), "by": by, "counts": counts}))
    _private(meta)
    _private(dst)
    return {"name": name, "counts": counts}


def sweep_expired(now=None) -> list[str]:
    """Delete test data older than the policy allows (pending: hours, saved datasets: days; 0 = keep).
    Returns what was deleted, for the audit trail."""
    import time
    now = now or time.time()
    gone = []
    for sub, ttl_s in (("pending", gpc.get("test_mode.pending_ttl_hours") * 3600),
                       ("datasets", gpc.get("test_mode.dataset_ttl_days") * 86400)):
        if not ttl_s:
            continue
        for p in sorted((_root() / sub).glob("*.db")):
            if now - p.stat().st_mtime > ttl_s:
                p.unlink(missing_ok=True)
                p.with_suffix(".json").unlink(missing_ok=True)
                gone.append(f"{sub}/{p.stem}")
    return gone


def delete_pending(pid: str) -> None:
    _pending_path(pid).unlink()


def delete_dataset(name: str) -> None:
    p = _root() / "datasets" / f"{name}.db"
    if not NAME_RE.match(name) or not p.exists():
        raise TestModeError("NO_DATASET", f"No saved dataset named {name}", 404)
    p.unlink()
    p.with_suffix(".json").unlink(missing_ok=True)


def file_for(kind: str, ident: str) -> Path:
    if kind == "pending":
        return _pending_path(ident)
    p = _root() / "datasets" / f"{ident}.db"
    if not NAME_RE.match(ident) or not p.exists():
        raise TestModeError("NO_DATASET", f"No saved dataset named {ident}", 404)
    return p


def counts_in(path: Path) -> dict:
    with closing(sqlite3.connect(str(path))) as c:
        q = lambda sql: c.execute(sql).fetchone()[0]  # noqa: E731
        return {"teachers": q("SELECT COUNT(*) FROM users WHERE role = 'teacher'"), "courses": q("SELECT COUNT(*) FROM courses"),
                "students": q("SELECT COUNT(*) FROM students"), "classes": q("SELECT COUNT(*) FROM class_sessions"),
                "enrollments": q("SELECT COUNT(*) FROM student_enrollments"), "quizzes": q("SELECT COUNT(*) FROM quizzes"),
                "polls": q("SELECT COUNT(*) FROM polls")}


def export_zip(path: Path) -> bytes:
    """The data as CSV files in the Test data sheets' format (importable again)."""
    from .sandbox import SHEETS
    cols = {s["name"]: [c["name"] for c in s["columns"]] for s in SHEETS}
    out = io.BytesIO()
    with closing(sqlite3.connect(str(path))) as c, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        c.row_factory = sqlite3.Row
        users = {r["id"]: r["username"] for r in c.execute("SELECT id, username FROM users")}
        courses = {r["id"]: r["code"] for r in c.execute("SELECT id, code FROM courses")}
        classes = {r["id"]: r["code"] for r in c.execute("SELECT id, code FROM class_sessions")}
        faculty = {}
        for r in c.execute("SELECT class_session_id, user_id FROM class_faculty"):
            faculty.setdefault(r[0], []).append(users.get(r[1], ""))
        data = {
            "teachers": [dict(username=r["username"], full_name=r["full_name"], email=r["email"], department="")
                         for r in c.execute("SELECT * FROM users WHERE role = 'teacher'")],
            "courses": [dict(code=r["code"], name=r["name"], credits=r["credits"], department=r["department"],
                             description=r["description"]) for r in c.execute("SELECT * FROM courses")],
            "students": [dict(roll_number=r["roll_number"], student_name=r["student_name"], email=r["email"],
                              program=r["program"], enrollment_year=r["enrollment_year"] or "",
                              graduation_year=r["graduation_year"] or "") for r in c.execute("SELECT * FROM students")],
            "classes": [], "enrollments": [], "quizzes": [], "polls": []}
        for r in c.execute("SELECT * FROM class_sessions"):
            sched = json.loads(r["meeting_schedule"] or "[]")
            data["classes"].append(dict(
                code=r["code"], name=r["name"], course_code=courses.get(r["course_id"], ""), section=r["course_section"],
                term=r["term"], year=r["year"] or "", teacher_username=users.get(r["teacher_id"], ""),
                co_faculty=",".join(u for u in faculty.get(r["id"], []) if u != users.get(r["teacher_id"])),
                classroom_code=r["classroom_code"] or "", location=r["location"], capacity=r["capacity"],
                days=",".join(s["day"][:3] for s in sched), start=sched[0]["start"] if sched else "",
                end=sched[0]["end"] if sched else "", start_date=r["start_date"] or "", end_date=r["end_date"] or ""))
        for r in c.execute("SELECT s.roll_number, e.class_session_id FROM student_enrollments e "
                           "JOIN students s ON s.id = e.student_id"):
            data["enrollments"].append(dict(roll_number=r[0], class_code=classes.get(r[1], "")))
        for r in c.execute("SELECT q.class_session_id, q.title, q.status, x.question_text, x.options, x.correct_option "
                           "FROM quiz_questions x JOIN quizzes q ON q.id = x.quiz_id ORDER BY q.id, x.order_num"):
            opts = json.loads(r[4] or "[]") + ["", "", "", ""]
            data["quizzes"].append(dict(class_code=classes.get(r[0], ""), title=r[1],
                                        status="completed" if r[2] == "completed" else "draft", question_text=r[3],
                                        option_a=opts[0], option_b=opts[1], option_c=opts[2], option_d=opts[3],
                                        correct="ABCD"[r[5]] if 0 <= r[5] < 4 else "A"))
        for r in c.execute("SELECT class_session_id, title, options, status FROM polls"):
            data["polls"].append(dict(class_code=classes.get(r[0], ""), title=r[1],
                                      options=" | ".join(json.loads(r[2] or "[]")),
                                      status="closed" if r[3] == "closed" else "draft"))
        files = {}
        for name, rows in data.items():
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=cols[name], extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({k: ("'" + v if isinstance(v, str) and v[:1] in "=+-@" else v) for k, v in row.items()})
            files[f"{name}.csv"] = buf.getvalue().encode()
        for name, content in files.items():
            z.writestr(name, content)
        z.writestr("SIGNATURE.json", signing.sign_files(files))      # who produced it, and that it is unchanged
    return out.getvalue()
