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
    with sqlite3.connect(str(src)) as s, sqlite3.connect(str(tmp)) as d:
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
                with sqlite3.connect(str(src)) as s, sqlite3.connect(str(db), timeout=5) as d:
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
    from ..database import Base, engine
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
    await restore_from(source)
    after = await verify_now()
    await _flag(f"The database changed outside imPress ({detail}). It was restored from the "
                f"{'start-up' if source.name == 'startup.db' else 'last good'} backup"
                f"{' at start-up' if at_startup else ''}{'' if after.ok else '; it still does not verify'}.",
                restored=source.name)


async def _flag(message: str, restored: str | None) -> None:
    from ..activity import log_activity
    from ..database import async_session
    from . import events
    write_state(degraded={"since": istnow().isoformat(), "message": message, "restored_from": restored})
    async with async_session() as db:
        await log_activity(db, "system.db_degraded", None, "system", None, {"flag": True, "message": message})
        await db.commit()
    events.alert(message, "error")
    events.status({"db": "degraded"})
    logger.error(message)


async def acknowledge() -> None:
    from . import events
    write_state(degraded=None)
    events.status({"db": "ok"})


async def check_and_backup() -> None:
    async with _lock:
        rep = await verify_now()
        if rep.ok:
            await copy_live_to(backup_dir() / "rolling.db")
        else:
            await repair(rep)


async def integrity_loop() -> None:
    while True:
        await asyncio.sleep(settings.INTEGRITY_INTERVAL_S)
        try:
            await check_and_backup()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Integrity check failed to run")


def backups_info() -> list[dict]:
    out = []
    for name in ("startup.db", "rolling.db"):
        p = backup_dir() / name
        if p.exists():
            st = p.stat()
            out.append({"name": name, "size": st.st_size,
                        "modified": istnow().fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
    return out
