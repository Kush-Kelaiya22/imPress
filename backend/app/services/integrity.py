"""Database integrity: verification, temporary backups, self-repair (v2.2).

- At start-up the database is verified (dbgateway.verify) and copied to the
  **start-up backup**. Every INTEGRITY_INTERVAL_S (5 minutes) it is verified
  again; while it verifies, the **rolling backup** is refreshed.
- If verification fails (something changed the database outside the
  application), the last good backup is restored automatically, the database
  is marked **Degraded**, the event is written to the activity log (flagged)
  and every signed-in administrator and super admin gets a toast. Degraded
  stays visible until an administrator acknowledges it.
- Backups live in IMPRESS_TEMP_BACKUP_DIR (default: the system temporary
  folder, `impress-backups/<database>`), readable by the server's user only.

The state (degraded, test mode) is a small JSON file next to the database, so
it survives a restart and does not travel with database swaps.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from ..config import settings
from ..timeutil import istnow

logger = logging.getLogger(__name__)

_lock = asyncio.Lock()          # one verification / backup / restore at a time
_last: dict = {"verified_at": None, "ok": None, "summary": "", "rows": 0}


# ── Paths and state ─────────────────────────────────────────────────────

def db_path() -> Path | None:
    url = settings.DATABASE_URL
    if not url.startswith("sqlite") or ":memory:" in url:
        return None
    return Path(url.split("///", 1)[1]).resolve()


def backup_dir() -> Path:
    db = db_path()
    tag = hashlib.sha256(str(db).encode()).hexdigest()[:8] if db else "memory"
    base = Path(settings.TEMP_BACKUP_DIR) if settings.TEMP_BACKUP_DIR else Path(tempfile.gettempdir()) / "impress-backups"
    d = base / f"{db.stem if db else 'db'}-{tag}"
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def state_file() -> Path:
    db = db_path()
    return (db.parent if db else Path(".")) / f"{db.stem if db else 'impress'}.state.json"


def read_state() -> dict:
    try:
        return json.loads(state_file().read_text())
    except (OSError, ValueError):
        return {}


def write_state(**changes) -> dict:
    state = {**read_state(), **changes}
    path = state_file()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, default=str))
    try:
        os.chmod(tmp, 0o600)              # it holds the test-mode password
    except OSError:
        pass
    os.replace(tmp, path)
    return state


def status() -> dict:
    s = read_state()
    deg = s.get("degraded")
    return {"db": "degraded" if deg else "ok", "degraded": deg, "last_verification": dict(_last),
            "test_mode": s.get("test_mode")}


# ── SQLite file operations (run in a thread) ────────────────────────────

def _copy_db(src: Path, dst: Path) -> None:
    """Consistent copy with SQLite's backup API (safe while the app writes)."""
    tmp = dst.with_suffix(".partial")
    # closing(): `with connect()` only commits; Windows can't rename an open file
    with closing(sqlite3.connect(str(src))) as s, closing(sqlite3.connect(str(tmp))) as d:
        s.backup(d)
    os.replace(tmp, dst)
    try:
        os.chmod(dst, 0o600)
    except OSError:
        pass


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


async def copy_live_to(dst: Path) -> Path:
    db = db_path()
    await asyncio.to_thread(_copy_db, db, dst)
    return dst


async def restore_from(src: Path) -> None:
    """Replace the live database's content with `src` (SQLite backup API),
    after closing the application's pooled connections."""
    from ..database import engine
    await engine.dispose()
    db = db_path()

    def go():
        for attempt in range(50):
            try:
                with closing(sqlite3.connect(str(src))) as s, closing(sqlite3.connect(str(db), timeout=5)) as d:
                    s.backup(d)
                return
            except sqlite3.OperationalError:
                if attempt == 49:
                    raise
                import time
                time.sleep(0.1)
    await asyncio.to_thread(go)
    await engine.dispose()           # new connections: fresh triggers, fresh data


# ── Verification ────────────────────────────────────────────────────────

async def verify_now():
    from .. import dbgateway
    from ..database import Base, engine
    async with engine.connect() as conn:
        rep = await conn.run_sync(lambda c: dbgateway.verify(c, Base.metadata))
    _last.update(verified_at=istnow().isoformat(), ok=rep.ok, summary=rep.summary(), rows=rep.rows)
    return rep


async def reseal_everything(reason: str) -> int:
    """Accept the database as it is now (a new baseline)."""
    from .. import dbgateway
    from ..database import Base, engine
    async with engine.begin() as conn:
        n = await conn.run_sync(lambda c: dbgateway.reseal_all(c, Base.metadata))
    logger.warning("Database re-sealed (%s): %d rows", reason, n)
    return n


async def startup() -> None:
    """After migrations: baseline on first use, else verify (and repair)."""
    from .. import dbgateway
    from ..database import engine
    if db_path() is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(dbgateway.ensure_tables)
        has_baseline = (await conn.exec_driver_sql("SELECT COUNT(*) FROM integrity_meta")).scalar()
    if not has_baseline:
        await reseal_everything("first start with the database gateway")
    else:
        rep = await verify_now()
        if not rep.ok:
            if rep.key_changed:
                await reseal_everything("the sealing key changed")
                await _flag("The database sealing key changed (IMPRESS_JWT_SECRET rotated): the database was "
                            "re-sealed as it is. Check that this was intended.", restored=None)
            else:
                await repair(rep, at_startup=True)
    async with _lock:
        if (await verify_now()).ok:
            await copy_live_to(backup_dir() / "startup.db")
            await copy_live_to(backup_dir() / "rolling.db")


async def repair(rep, at_startup: bool = False) -> None:
    """Restore the last good backup after a failed verification."""
    d = backup_dir()
    source = next((p for p in (d / "rolling.db", d / "startup.db") if p.exists()), None)
    detail = rep.summary()
    if source is None:
        await _flag(f"The database changed outside imPress ({detail}) and no backup was available to restore. "
                    "Review it; a super admin can accept its current state.", restored=None)
        return
    age_min = max(0, int((istnow().timestamp() - source.stat().st_mtime) // 60))
    forensic = await keep_forensic_copy()
    await restore_from(source)
    after = await verify_now()
    await _flag(f"The database changed outside imPress ({detail}). It was restored from the "
                f"{'start-up' if source.name == 'startup.db' else 'last good'} backup made {age_min} min ago"
                f"{' at start-up' if at_startup else ''}{'' if after.ok else '; it still does not verify'}. "
                f"Changes made since that backup are lost. "
                + (f"The changed database was kept as {forensic.name} for investigation." if forensic else
                   "No copy of the changed database could be kept."),
                restored=source.name)


async def keep_forensic_copy() -> Path | None:
    """Before an automatic restore replaces it, keep the failed database (what an
    investigator needs), newest N per policy integrity.forensic_copies."""
    from .. import gpc
    try:
        dst = await copy_live_to(backup_dir() / f"forensic-{istnow():%Y%m%d-%H%M%S}.db")
    except Exception:
        logger.exception("could not keep a forensic copy")
        return None
    old = sorted(backup_dir().glob("forensic-*.db"))
    for p in old[:max(0, len(old) - max(1, gpc.get("integrity.forensic_copies")))]:
        p.unlink(missing_ok=True)
    return dst


async def _flag(message: str, restored: str | None) -> None:
    from ..activity import log_activity
    from ..database import async_session
    from . import events
    write_state(degraded={"since": istnow().isoformat(), "message": message, "restored_from": restored})
    async with async_session() as db:
        await log_activity(db, "system.db_degraded", None, "system", None, {"flag": True, "message": message})
        await db.commit()
    events.alert(message, "error")
    events.status({"db": "degraded"}, "admins")
    logger.error(message)


async def acknowledge() -> None:
    from . import events
    write_state(degraded=None)
    events.status({"db": "ok"}, "admins")


async def check_and_backup_locked() -> None:
    """check_and_backup for a caller that already holds the lock."""
    rep = await verify_now()
    if rep.ok:
        await copy_live_to(backup_dir() / "rolling.db")
    else:
        await repair(rep)


async def check_and_backup() -> None:
    async with _lock:
        await check_and_backup_locked()


async def integrity_loop() -> None:
    while True:
        await asyncio.sleep(settings.INTEGRITY_INTERVAL_S)
        try:
            await check_and_backup()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Integrity check failed to run")


def sweep_old_copies(now: float | None = None) -> list[str]:
    """Delete the copies taken before a clear once they are older than policy integrity.before_clear_days."""
    import time
    from .. import gpc
    days = gpc.get("integrity.before_clear_days")
    if not days:
        return []
    now = now or time.time()
    gone = []
    for p in sorted(backup_dir().glob("before-clear-*.db")):
        if now - p.stat().st_mtime > days * 86400:
            p.unlink(missing_ok=True)
            gone.append(p.name)
    return gone


def backups_info() -> list[dict]:
    d = backup_dir()
    names = ["startup.db", "rolling.db"] + [p.name for p in sorted(d.glob("forensic-*.db"), reverse=True)] \
        + [p.name for p in sorted(d.glob("before-clear-*.db"), reverse=True)[:3]]
    out = []
    for name in names:
        p = d / name
        if p.exists():
            st = p.stat()
            kind = "forensic" if name.startswith("forensic-") else "before-clear" if name.startswith("before-clear-") else "backup"
            out.append({"name": name, "kind": kind, "size": st.st_size,
                        "modified": istnow().fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
    return out
