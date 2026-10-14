"""Database gateway (v2.2): every write goes through one checkpoint.

1. **Who may write what.** Every SQL statement the application sends passes
   `before_cursor_execute`. A write (INSERT, UPDATE, DELETE) names its table;
   the acting principal (a signed-in user with their permissions, a device,
   the anonymous sign-in path, or the system itself) must be allowed to write
   that table, or the statement is refused before it runs (403, flagged in
   the activity log, administrators alerted). Schema changes are for the
   system only. Row-level rules come on top for accounts: without
   `users.manage` a user may change only their own name and password.

2. **Seals.** Every row of every application table carries a seal: the
   HMAC-SHA256 of its column values under a key only this server holds
   (derived from IMPRESS_JWT_SECRET), kept in `integrity_seals`, plus a
   per-table aggregate (XOR of the row seals and the row count, itself
   sealed) in `integrity_tables`. Each of the application's own database
   connections carries TEMP triggers (they exist on that connection only)
   that record every row a statement changes, whatever its kind (ORM, bulk,
   raw SQL, cascades); at commit the gateway reseals exactly those rows,
   inside the same transaction: one HMAC per changed row, so it stays cheap
   for tables that grow all day (logs, answers).

   A change made **outside** the application (an `sqlite3` command, a hex
   editor, a restored file) cannot produce valid seals, so `verify()` finds
   it: a row whose seal doesn't match, a row without a seal, a deleted row,
   or an aggregate that doesn't add up. services/integrity.py runs it every
   5 minutes and restores the last good backup if it fails.

Clearing or resetting the database is done through the administrators' API
(routers/system.py), never by commands.
"""

from __future__ import annotations

import base64
import contextvars
import datetime as dt
import decimal
import hashlib
import hmac
import json
import logging
import re
from dataclasses import dataclass, field

from sqlalchemy import event, exc, select, text

logger = logging.getLogger(__name__)

SEAL_TABLES = ("integrity_seals", "integrity_tables", "integrity_meta")
BULK_RESEAL = 300          # more changed rows than this in one commit: reseal the whole table
NOT_SEALED = frozenset(SEAL_TABLES) | {"schema_migrations", "sqlite_sequence"}


# ── Who is acting ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Principal:
    kind: str                       # system | user | device | anonymous
    user: object | None = None      # the User, for permission checks
    device_id: int | None = None
    label: str = ""


SYSTEM = Principal("system", label="system")
ANONYMOUS = Principal("anonymous", label="anonymous")
_current: contextvars.ContextVar[Principal] = contextvars.ContextVar("db_principal", default=SYSTEM)
_sealing: contextvars.ContextVar[bool] = contextvars.ContextVar("db_sealing", default=False)


def act_as(principal: Principal) -> None:
    """Set the principal for the rest of this request (or task)."""
    _current.set(principal)


@dataclass(frozen=True)
class UserSnapshot:
    """What the rules need, copied: a rollback must not expire it mid-request."""
    id: int | None
    username: str
    role: str
    is_active: bool


def as_user(user) -> Principal:
    snap = UserSnapshot(user.id, user.username, user.role, bool(user.is_active))
    return Principal("user", user=snap, label=f"user:{snap.username}")


def as_device(device_id: int | None) -> Principal:
    return Principal("device", device_id=device_id, label=f"device:{device_id or 'shared-key'}")


def current() -> Principal:
    return _current.get()


class as_system:
    """`with as_system():` the server's own housekeeping inside a request
    (reading the schema version creates its bookkeeping table if missing)."""

    def __enter__(self):
        self._token = _current.set(SYSTEM)

    def __exit__(self, *exc):
        _current.reset(self._token)


class DatabaseWriteRefused(Exception):
    def __init__(self, table: str, principal: Principal, why: str = ""):
        self.table, self.principal, self.why = table, principal, why
        super().__init__(f"{principal.label} may not write {table}{': ' + why if why else ''}")


# ── The write rules ─────────────────────────────────────────────────────

ANONYMOUS_TABLES = frozenset({"login_throttle", "activity_logs"})
DEVICE_TABLES = frozenset({
    "esp_devices", "student_modules", "quiz_answers", "poll_votes", "attendance", "activity_logs",
    "deployment_targets", "firmware_deployments", "student_enrollments", "class_sessions",
})
# Tables a signed-in user writes only with this permission; any other table:
# any active member of staff (the routes' own policy checks still apply).
USER_TABLE_PERMISSION = {
    "firmware_artifacts": "firmware.manage",
    "firmware_deployments": "firmware.deploy",
    "deployment_targets": "firmware.deploy",
    "schedule_sources": "classes.manage_all",
}
SYSTEM_ONLY = frozenset(SEAL_TABLES) | {"schema_migrations"}


def may_write(p: Principal, table: str) -> tuple[bool, str]:
    if p.kind == "system":
        return True, ""
    if table in SYSTEM_ONLY:
        return False, "system tables are written by the server only"
    if p.kind == "anonymous":
        return table in ANONYMOUS_TABLES, "not signed in"
    if p.kind == "device":
        return table in DEVICE_TABLES, "devices write only their own records"
    from .policy import allowed, is_staff
    if not is_staff(p.user):
        return False, "not an active member of staff"
    perm = USER_TABLE_PERMISSION.get(table)
    if perm and not allowed(p.user, perm):
        return False, f"needs {perm}"
    return True, ""


_WRITE = re.compile(r'^\s*(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|REPLACE\s+INTO|UPDATE(?:\s+OR\s+\w+)?|DELETE\s+FROM)'
                    r'\s+(?:main\.)?["`\[]?(\w+)', re.I)
_DDL = re.compile(r'^\s*(?:CREATE|DROP|ALTER)\b', re.I)


# ── Seals ───────────────────────────────────────────────────────────────

def _key() -> bytes:
    from .config import settings
    return hashlib.sha256(b"impress.db-gateway.seal\0" + settings.JWT_SECRET.encode()).digest()


def key_fingerprint() -> str:
    return hashlib.sha256(b"fingerprint\0" + _key()).hexdigest()[:16]


def _plain(v):
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(v)).decode()
    if isinstance(v, decimal.Decimal):
        return str(v)
    if isinstance(v, bool):
        return int(v)
    return v


def row_seal(table: str, values: tuple) -> str:
    body = json.dumps([table, [_plain(v) for v in values]], sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()


def _pk_text(values) -> str:
    """Same text as SQLite's json_array() over the key columns (the triggers' form)."""
    return json.dumps([_plain(v) for v in values], separators=(",", ":"), ensure_ascii=False)


def _aggregate_mac(table: str, xor: str, count: int) -> str:
    return hmac.new(_key(), f"agg\0{table}\0{xor}\0{count}".encode(), hashlib.sha256).hexdigest()


def _xor(a: str, b: str) -> str:
    return f"{int(a, 16) ^ int(b, 16):064x}"


ZERO = "0" * 64


def sealed_tables(metadata) -> list:
    return [t for _, t in sorted(metadata.tables.items()) if t.name not in NOT_SEALED and list(t.primary_key.columns)]


def _table(metadata, name):
    return metadata.tables.get(name)


def _read_rows(conn, table, where=None):
    q = select(table)
    if where is not None:
        q = q.where(where)
    pk = list(table.primary_key.columns)
    cols = list(table.columns)
    idx = [cols.index(c) for c in pk]
    for row in conn.execute(q):
        yield _pk_text([row[i] for i in idx]), row_seal(table.name, tuple(row))


def _set_aggregate(conn, table_name: str, xor: str, count: int) -> None:
    conn.execute(text("INSERT INTO integrity_tables (tbl, xor, count, mac) VALUES (:t, :x, :c, :m) "
                      "ON CONFLICT(tbl) DO UPDATE SET xor = :x, count = :c, mac = :m"),
                 {"t": table_name, "x": xor, "c": count, "m": _aggregate_mac(table_name, xor, count)})


def _get_aggregate(conn, table_name: str) -> tuple[str, int]:
    row = conn.execute(text("SELECT xor, count FROM integrity_tables WHERE tbl = :t"), {"t": table_name}).first()
    return (row[0], row[1]) if row else (ZERO, 0)


def reseal_table(conn, table) -> int:
    """Seal every row of one table afresh (the server's own bulk writes, or a
    new baseline). Returns the number of rows."""
    token = _sealing.set(True)
    try:
        conn.execute(text("DELETE FROM integrity_seals WHERE tbl = :t"), {"t": table.name})
        xor, n, batch = ZERO, 0, []
        for pk, mac in _read_rows(conn, table):
            xor, n = _xor(xor, mac), n + 1
            batch.append({"t": table.name, "p": pk, "m": mac})
            if len(batch) >= 500:
                conn.execute(text("INSERT INTO integrity_seals (tbl, pk, mac) VALUES (:t, :p, :m)"), batch)
                batch = []
        if batch:
            conn.execute(text("INSERT INTO integrity_seals (tbl, pk, mac) VALUES (:t, :p, :m)"), batch)
        _set_aggregate(conn, table.name, xor, n)
        return n
    finally:
        _sealing.reset(token)


def reseal_all(conn, metadata) -> int:
    token = _sealing.set(True)
    try:
        total = sum(reseal_table(conn, t) for t in sealed_tables(metadata))
        conn.execute(text("INSERT INTO integrity_meta (k, v) VALUES ('key', :v) "
                          "ON CONFLICT(k) DO UPDATE SET v = :v"), {"v": key_fingerprint()})
        return total
    finally:
        _sealing.reset(token)


def _seal_rows(conn, table, pk_texts) -> None:
    """Reseal these rows (by key text) and update the table aggregate."""
    token = _sealing.set(True)
    try:
        xor, count = _get_aggregate(conn, table.name)
        cols = list(table.primary_key.columns)
        for pk in pk_texts:
            old = conn.execute(text("SELECT mac FROM integrity_seals WHERE tbl = :t AND pk = :p"),
                               {"t": table.name, "p": pk}).first()
            if old:
                xor, count = _xor(xor, old[0]), count - 1
            values = json.loads(pk)
            cond = None
            for c, v in zip(cols, values):
                cond = (c == v) if cond is None else (cond & (c == v))
            fresh = next(_read_rows(conn, table, cond), None)
            if fresh is None:                                   # the row is gone
                conn.execute(text("DELETE FROM integrity_seals WHERE tbl = :t AND pk = :p"), {"t": table.name, "p": pk})
                continue
            conn.execute(text("INSERT INTO integrity_seals (tbl, pk, mac) VALUES (:t, :p, :m) "
                              "ON CONFLICT(tbl, pk) DO UPDATE SET mac = :m"), {"t": table.name, "p": fresh[0], "m": fresh[1]})
            xor, count = _xor(xor, fresh[1]), count + 1
        _set_aggregate(conn, table.name, xor, count)
    finally:
        _sealing.reset(token)


# ── Verification ────────────────────────────────────────────────────────

@dataclass
class Report:
    ok: bool = True
    rows: int = 0
    problems: dict = field(default_factory=dict)       # table -> {"changed": n, "added": n, "removed": n, "aggregate": bool}
    key_changed: bool = False

    def summary(self) -> str:
        if self.ok:
            return f"{self.rows} rows verified"
        parts = []
        for t, p in self.problems.items():
            bits = [f"{k} {v}" for k, v in p.items() if k != "aggregate" and v]
            if p.get("aggregate"):
                bits.append("aggregate mismatch")
            parts.append(f"{t}: {', '.join(bits)}")
        return "; ".join(parts)


def verify(conn, metadata) -> Report:
    """Recompute every row's seal and compare (one HMAC per row)."""
    rep = Report()
    meta = conn.execute(text("SELECT v FROM integrity_meta WHERE k = 'key'")).first()
    if meta and meta[0] != key_fingerprint():
        rep.ok, rep.key_changed = False, True
        rep.problems["*"] = {"key": "the sealing key changed (IMPRESS_JWT_SECRET rotated?)"}
        return rep
    for table in sealed_tables(metadata):
        seals = dict(conn.execute(text("SELECT pk, mac FROM integrity_seals WHERE tbl = :t"), {"t": table.name}).all())
        changed = added = 0
        xor, n = ZERO, 0
        for pk, mac in _read_rows(conn, table):
            n += 1
            rep.rows += 1
            want = seals.pop(pk, None)
            if want is None:
                added += 1
            elif not hmac.compare_digest(want, mac):
                changed += 1
            xor = _xor(xor, mac)
        removed = len(seals)
        agg = conn.execute(text("SELECT xor, count, mac FROM integrity_tables WHERE tbl = :t"),
                           {"t": table.name}).first()
        agg_bad = (agg is None and n > 0) or (agg is not None and (
            not hmac.compare_digest(agg[2], _aggregate_mac(table.name, agg[0], agg[1]))
            or agg[0] != xor or agg[1] != n))
        if changed or added or removed or agg_bad:
            rep.ok = False
            rep.problems[table.name] = {"changed": changed, "added": added, "removed": removed, "aggregate": agg_bad}
    return rep


def ensure_tables(conn) -> None:
    conn.execute(text("CREATE TABLE IF NOT EXISTS integrity_seals (tbl TEXT NOT NULL, pk TEXT NOT NULL, "
                      "mac TEXT NOT NULL, PRIMARY KEY (tbl, pk))"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS integrity_tables (tbl TEXT PRIMARY KEY, xor TEXT NOT NULL, "
                      "count INTEGER NOT NULL, mac TEXT NOT NULL)"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS integrity_meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)"))


# ── Hooks ───────────────────────────────────────────────────────────────

_refused_log: list[dict] = []          # refusals waiting to be written to the activity log


def _trigger_sql(table) -> list[str]:
    """TEMP triggers (this connection only) recording every changed row."""
    cols = [c.name for c in table.primary_key.columns]
    def key(alias):
        return "json_array(" + ", ".join(f'{alias}."{c}"' for c in cols) + ")"
    t = table.name
    # unqualified: older SQLite refuses schema names in trigger bodies; a TEMP
    # trigger resolves gw_changes in the temp schema first
    rec = "INSERT OR IGNORE INTO gw_changes (tbl, pk) VALUES ('{t}', {k});"
    return [
        f'CREATE TEMP TRIGGER IF NOT EXISTS gw_{t}_i AFTER INSERT ON main."{t}" BEGIN '
        + rec.format(t=t, k=key("NEW")) + " END",
        f'CREATE TEMP TRIGGER IF NOT EXISTS gw_{t}_u AFTER UPDATE ON main."{t}" BEGIN '
        + rec.format(t=t, k=key("OLD")) + " " + rec.format(t=t, k=key("NEW")) + " END",
        f'CREATE TEMP TRIGGER IF NOT EXISTS gw_{t}_d AFTER DELETE ON main."{t}" BEGIN '
        + rec.format(t=t, k=key("OLD")) + " END",
    ]


def install(engine, metadata, session_class) -> None:
    """Attach the gateway to the engine and the ORM session class."""
    sync_engine = engine.sync_engine

    @event.listens_for(sync_engine, "connect")
    def _triggers(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            cur.execute("CREATE TEMP TABLE IF NOT EXISTS gw_changes (tbl TEXT NOT NULL, pk TEXT NOT NULL, "
                        "PRIMARY KEY (tbl, pk))")
            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            existing = {r[0] for r in cur.fetchall()}
            for table in sealed_tables(metadata):
                if table.name in existing:
                    for sql in _trigger_sql(table):
                        cur.execute(sql)
        finally:
            cur.close()

    @event.listens_for(sync_engine, "before_cursor_execute", retval=False)
    def _check(conn, cursor, statement, parameters, context, executemany):
        if _sealing.get():
            return
        p = _current.get()
        if _DDL.match(statement) and "TEMP" not in statement[:30].upper():
            if p.kind != "system":
                _refuse("schema", p, "schema changes are for the server only")
            return
        m = _WRITE.match(statement)
        if not m:
            return
        table = m.group(1)
        ok, why = may_write(p, table)
        if not ok:
            _refuse(table, p, why)
        conn.info.setdefault("gw_touched", set()).add(table)

    @event.listens_for(sync_engine, "commit")
    def _on_commit(conn):
        touched = conn.info.pop("gw_touched", set())
        if not touched:
            return
        token = _sealing.set(True)
        try:
            changes = conn.execute(text("SELECT tbl, pk FROM temp.gw_changes")).all()
            if changes:
                conn.execute(text("DELETE FROM temp.gw_changes"))
        finally:
            _sealing.reset(token)
        by_table: dict[str, list[str]] = {}
        for tbl, pk in changes:
            by_table.setdefault(tbl, []).append(pk)
        for name, pks in by_table.items():
            t = _table(metadata, name)
            if t is None or name in NOT_SEALED:
                continue
            if len(pks) > BULK_RESEAL:          # a bulk change: one pass over the table is cheaper
                reseal_table(conn, t)
            else:
                _seal_rows(conn, t, pks)
        from .services import events
        events.changed(touched - set(NOT_SEALED))

    @event.listens_for(sync_engine, "rollback")
    def _on_rollback(conn):
        # A task cancelled mid-query leaves an invalidated connection: reading
        # its info raises, and that error would replace the CancelledError
        # being handled (a background loop then never stops). Nothing to
        # clear then: temp.gw_changes rolled back with the transaction.
        try:
            conn.info.pop("gw_touched", None)
        except exc.SQLAlchemyError:
            pass

    @event.listens_for(session_class, "before_flush")
    def _before_flush(session, flush_context, instances):
        p = _current.get()
        if p.kind == "user":
            _check_user_rows(session, p)


ACCOUNT_SELF_FIELDS = frozenset({"full_name", "display_name", "hashed_password", "must_change_password", "preferences",
                                 "onboarded_at", "updated_at"})


def _check_user_rows(session, p: Principal) -> None:
    """Without users.manage, a user changes only their own name and password."""
    from sqlalchemy import inspect
    from .models import User
    from .policy import allowed
    if allowed(p.user, "users.manage"):
        return
    for obj in list(session.new) + list(session.dirty) + list(session.deleted):
        if not isinstance(obj, User):
            continue
        if obj in session.new or obj in session.deleted or obj.id != p.user.id:
            _refuse("users", p, "only an administrator manages accounts")
        changed = {a.key for a in inspect(obj).attrs if a.history.has_changes()}
        if not changed <= ACCOUNT_SELF_FIELDS:
            _refuse("users", p, f"may change only their own {', '.join(sorted(ACCOUNT_SELF_FIELDS))}")


def _refuse(table: str, p: Principal, why: str):
    entry = {"table": table, "principal": p.label, "why": why}
    _refused_log.append(entry)
    logger.warning("DB gateway refused a write: %s", entry)
    try:
        from .services import events
        events.alert(f"Database gateway refused a write to {table} by {p.label}: {why}", "error")
    except Exception:            # pragma: no cover - alerts are best effort
        pass
    raise DatabaseWriteRefused(table, p, why)


def take_refusals() -> list[dict]:
    out = list(_refused_log)
    _refused_log.clear()
    return out
