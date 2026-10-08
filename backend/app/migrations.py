"""Versioned, transactional schema migrations for the SQLite database.

Why not Alembic: the deployment is one SQLite file on one server, migrations
are few, and every one must also adopt databases created by older releases
(which have no migration history). A numbered list of idempotent steps covers
that with no extra tooling.

Rules
- `MIGRATIONS` is append-only. Never edit or renumber a released step.
- Every step is idempotent (safe on a fresh schema built by `create_all`, and
  on a database that already has the change).
- Each step runs in its own transaction together with its `schema_migrations`
  row: a step either fully applies or leaves no trace.
- Before the first pending step on an existing database file, a copy is
  written next to it (`<db>.bak-<from>-to-<to>-<timestamp>`).
- A step that can't apply safely raises `MigrationError` with instructions;
  startup stops instead of running on a half-migrated schema.

See docs/engineering/DATABASE_MIGRATIONS.md.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from .timeutil import istnow

log = logging.getLogger(__name__)

Step = Callable[[AsyncConnection], Awaitable[None]]


class MigrationError(RuntimeError):
    """A migration cannot be applied safely; the message says what to do."""


# ── Steps ────────────────────────────────────────────────────────────────

# Columns added to pre-v2 tables (formerly database._ADD_COLUMNS).
_V2_COLUMNS = {
    "class_sessions": {"start_date": "DATE", "end_date": "DATE", "exam_start_date": "DATE",
                       "exam_end_date": "DATE", "classroom_code": "VARCHAR(32)"},
    "esp_devices": {"is_connected": "BOOLEAN DEFAULT 0", "gateway_id": "INTEGER",
                    "is_active": "BOOLEAN DEFAULT 1", "firmware_version": "VARCHAR(32) DEFAULT '0.0.0'",
                    "pending_version": "VARCHAR(32) DEFAULT ''", "ota_status": "VARCHAR(16) DEFAULT 'idle'",
                    "ota_requested_at": "DATETIME", "verified_at": "DATETIME",
                    "student_count": "INTEGER DEFAULT 0", "free_heap": "INTEGER", "total_flash": "INTEGER",
                    "student_enrollment_id": "INTEGER", "device_id": "INTEGER"},
    "courses": {"exam_date": "DATE", "exam_start_time": "VARCHAR(8)", "exam_end_time": "VARCHAR(8)"},
    "quiz_answers": {"student_id": "INTEGER"},
    "poll_votes": {"student_id": "INTEGER"},
    "attendance": {"student_enrollment_id": "INTEGER", "device_id": "INTEGER"},
}


async def _columns(conn: AsyncConnection, table: str) -> dict[str, dict]:
    rows = (await conn.execute(text(f"PRAGMA table_info({table})"))).all()
    return {r[1]: {"notnull": bool(r[3]), "pk": bool(r[5])} for r in rows}


async def _add_columns(conn: AsyncConnection, columns: dict[str, dict[str, str]]) -> None:
    for table, cols in columns.items():
        existing = await _columns(conn, table)
        for name, ddl in cols.items():
            if existing and name not in existing:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


async def add_v2_columns(conn: AsyncConnection) -> None:
    """Columns older databases lack (the pre-migration-framework ALTERs)."""
    await _add_columns(conn, _V2_COLUMNS)


# Latest gateway diagnostics from the heartbeat (#39). All nullable: older
# firmware doesn't send them.
_DIAGNOSTICS_COLUMNS = {
    "esp_devices": {"uptime_s": "INTEGER", "reset_reason": "VARCHAR(16)", "boot_count": "INTEGER",
                    "min_free_heap": "INTEGER", "s3_link_ok": "BOOLEAN", "s3_uptime_s": "INTEGER",
                    "diag_at": "DATETIME"},
}


async def add_diagnostics_columns(conn: AsyncConnection) -> None:
    await _add_columns(conn, _DIAGNOSTICS_COLUMNS)


async def add_device_keys(conn: AsyncConnection) -> None:
    """Per-device keys (#66): the hash of each device's own key."""
    await _add_columns(conn, {"esp_devices": {"api_key_hash": "VARCHAR(64)", "key_issued_at": "DATETIME",
                                              "key_confirmed_at": "DATETIME"}})
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_esp_devices_api_key_hash ON esp_devices (api_key_hash)"))


async def repair_dangling_references(conn: AsyncConnection) -> None:
    """Older code could delete a parent and leave children pointing at it.

    Foreign keys are enforced from now on, so such rows must be repaired
    first: a nullable reference is set to NULL; a row whose required parent
    is gone (unreachable in the app) is deleted. Counts are logged.
    """
    repaired = deleted = 0
    for _ in range(10):                      # deleting a row can orphan its own children
        violations = (await conn.execute(text("PRAGMA foreign_key_check"))).all()
        if not violations:
            break
        for table, rowid, _parent, fkid in violations:
            fks = (await conn.execute(text(f"PRAGMA foreign_key_list({table})"))).all()
            cols = [fk[3] for fk in fks if fk[0] == fkid]           # (id, seq, table, from, ...)
            meta = await _columns(conn, table)
            if all(not meta[c]["notnull"] for c in cols):
                sets = ", ".join(f"{c} = NULL" for c in cols)
                await conn.execute(text(f"UPDATE {table} SET {sets} WHERE rowid = :r"), {"r": rowid})
                repaired += 1
            else:
                await conn.execute(text(f"DELETE FROM {table} WHERE rowid = :r"), {"r": rowid})
                deleted += 1
    else:
        raise MigrationError("dangling references remain after 10 repair passes")
    if repaired or deleted:
        log.warning("Repaired %d dangling reference(s); removed %d orphaned row(s)", repaired, deleted)


# (index, table, key columns, WHERE for partial index or None)
UNIQUE_INDEXES = [
    ("uq_student_enrollments_class_student", "student_enrollments", ("class_session_id", "student_id"), None),
    ("uq_quiz_answers_quiz_question_student", "quiz_answers", ("quiz_id", "question_order", "student_id"), None),
    ("uq_quiz_answers_quiz_question_device", "quiz_answers", ("quiz_id", "question_order", "device_id"), None),
    ("uq_poll_votes_poll_student", "poll_votes", ("poll_id", "student_id"), None),
    ("uq_poll_votes_poll_device", "poll_votes", ("poll_id", "device_id"), None),
    ("uq_class_sessions_course_section", "class_sessions", ("course_id", "course_section"),
     "course_id IS NOT NULL AND course_section <> ''"),
]

# Duplicates the application already treated as "first one wins" are removed
# keeping the earliest row. Any other duplicate needs a human decision.
_KEEP_FIRST = {"student_enrollments", "quiz_answers", "poll_votes"}


async def add_unique_constraints(conn: AsyncConnection) -> None:
    for name, table, cols, where in UNIQUE_INDEXES:
        key = ", ".join(cols)
        cond = " AND ".join([f"{c} IS NOT NULL" for c in cols] + ([where] if where else []))
        dups = (await conn.execute(text(
            f"SELECT {key}, COUNT(*), MIN(id) FROM {table} WHERE {cond} GROUP BY {key} HAVING COUNT(*) > 1"
        ))).all()
        if dups and table in _KEEP_FIRST:
            removed = 0
            for row in dups:
                match = " AND ".join(f"{c} = :{c}" for c in cols)
                params = {c: row[i] for i, c in enumerate(cols)} | {"keep": row[-1]}
                res = await conn.execute(text(f"DELETE FROM {table} WHERE {match} AND id <> :keep"), params)
                removed += res.rowcount or 0
            log.warning("%s: removed %d duplicate row(s), kept the earliest of each (%s)", table, removed, key)
        elif dups:
            sample = "; ".join(f"({', '.join(map(str, r[:len(cols)]))}) x{r[len(cols)]}" for r in dups[:5])
            raise MigrationError(
                f"{table} has duplicate ({key}) values that must be resolved by hand before "
                f"upgrading: {sample}. Give each class its own section label (or remove the "
                f"course link) in the current version, then restart.")
        partial = f" WHERE {where}" if where else ""
        await conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS {name} ON {table} ({key}){partial}"))


async def unique_question_order(conn: AsyncConnection) -> None:
    """One question per position in a quiz (#31: concurrent CSV imports into
    one quiz must not interleave). Quiz creation always numbered 0..n-1, but
    any duplicate positions are renumbered in (order_num, id) order first."""
    quizzes = (await conn.execute(text(
        "SELECT quiz_id FROM quiz_questions GROUP BY quiz_id, order_num HAVING COUNT(*) > 1"))).all()
    for (quiz_id,) in set(quizzes):
        ids = [r[0] for r in (await conn.execute(text(
            "SELECT id FROM quiz_questions WHERE quiz_id = :q ORDER BY order_num, id"), {"q": quiz_id})).all()]
        for pos, qid in enumerate(ids):
            await conn.execute(text("UPDATE quiz_questions SET order_num = :p WHERE id = :i"), {"p": pos, "i": qid})
        log.warning("quiz %s: renumbered %d questions to remove duplicate positions", quiz_id, len(ids))
    await conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_quiz_questions_quiz_order ON quiz_questions (quiz_id, order_num)"))


# Append-only. (version, name, step)
MIGRATIONS: list[tuple[int, str, Step]] = [
    (1, "add_v2_columns", add_v2_columns),
    (2, "repair_dangling_references", repair_dangling_references),
    (3, "add_unique_constraints", add_unique_constraints),
    (4, "unique_question_order", unique_question_order),
    (5, "add_diagnostics_columns", add_diagnostics_columns),
    (6, "add_device_keys", add_device_keys),
]

LATEST = MIGRATIONS[-1][0]


# ── Runner ───────────────────────────────────────────────────────────────

async def _applied(conn: AsyncConnection) -> set[int]:
    await conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version INTEGER PRIMARY KEY, name VARCHAR(64) NOT NULL, applied_at DATETIME NOT NULL)"))
    return {r[0] for r in (await conn.execute(text("SELECT version FROM schema_migrations"))).all()}


async def _has_app_tables(conn: AsyncConnection) -> bool:
    n = await conn.scalar(text(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "AND name <> 'schema_migrations'"))
    return bool(n)


def _db_file(engine: AsyncEngine) -> Path | None:
    url = make_url(str(engine.url))
    db = url.database
    if not url.drivername.startswith("sqlite") or not db or db == ":memory:":
        return None
    return Path(db)


def backup(engine: AsyncEngine, from_version: int, to_version: int) -> Path | None:
    """Copy the SQLite file before migrating it. Returns the backup path."""
    src = _db_file(engine)
    if src is None or not src.exists():
        return None
    dest = src.with_name(f"{src.name}.bak-{from_version}-to-{to_version}-{istnow():%Y%m%d%H%M%S}")
    shutil.copy2(src, dest)
    log.warning("Database backup before migrating: %s", dest)
    return dest


async def schema_version(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        applied = await _applied(conn)
        await conn.commit()
    return max(applied, default=0)


async def migrate(engine: AsyncEngine, create_all: Callable | None = None) -> list[int]:
    """Bring the database to LATEST. Returns the versions applied now.

    `create_all` (sync, run on the connection) first creates missing tables:
    on a fresh database that is the whole schema, and every step is a no-op.
    """
    async with engine.begin() as conn:
        existing = await _has_app_tables(conn)
        applied = await _applied(conn)
    pending = [m for m in MIGRATIONS if m[0] not in applied]

    if existing and pending:
        await engine.dispose()               # release the file before copying it
        backup(engine, max(applied, default=0), LATEST)
    if create_all is not None:
        async with engine.begin() as conn:
            await conn.run_sync(create_all)

    done = []
    for version, name, step in pending:
        # pysqlite only opens a transaction before DML, so DDL (ALTER, CREATE
        # INDEX) would autocommit; an explicit BEGIN makes the whole step and
        # its record atomic, and IMMEDIATE keeps a second process out.
        async with engine.connect() as conn:
            await conn.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                await step(conn)
                await conn.execute(text(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (:v, :n, :t)"),
                    {"v": version, "n": name, "t": istnow().isoformat(sep=" ")})   # str: sqlite3's datetime adapter is deprecated
                await conn.commit()
            except BaseException:
                await conn.rollback()
                raise
        done.append(version)
        log.info("Applied migration %04d %s", version, name)
    return done
