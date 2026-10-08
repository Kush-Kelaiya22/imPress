"""#41: versioned migrations adopt old databases safely and atomically."""

import asyncio
import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine


def _migrate(path, steps=None, monkeypatch=None):
    from app import migrations
    from app.database import Base
    from app import models  # noqa: F401
    if steps is not None:
        monkeypatch.setattr(migrations, "MIGRATIONS", steps)

    async def go():
        engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
        try:
            return await migrations.migrate(engine, Base.metadata.create_all)
        finally:
            await engine.dispose()
    return asyncio.run(go())


def _q(path, sql, *args):
    with sqlite3.connect(path) as c:
        return c.execute(sql, args).fetchall()


def _indexes(path):
    return {r[0] for r in _q(path, "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'uq_%'")}


def _all_versions():
    from app.migrations import MIGRATIONS
    return [v for v, *_ in MIGRATIONS]


def _model_unique_indexes():
    """What a fresh database gets from the models: migrated ones must match."""
    from app.database import Base
    from app import models  # noqa: F401
    return {i.name for t in Base.metadata.tables.values() for i in t.indexes if i.unique and i.name.startswith("uq_")}


def _backups(path):
    return sorted(p.name for p in path.parent.glob(path.name + ".bak-*"))


def _legacy_db(path):
    """A v2-era database: today's tables minus the unique indexes and the
    schema_migrations table, one column missing, plus the data problems old
    code could create (duplicates, dangling references)."""
    from app.database import Base
    from app import models  # noqa: F401
    eng = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(eng)
    eng.dispose()
    with sqlite3.connect(path) as c:
        c.execute("DROP TABLE firmware_artifacts")         # new in v2.1
        for name in [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE name LIKE 'uq_%'")]:
            c.execute(f"DROP INDEX {name}")
        c.execute("ALTER TABLE esp_devices DROP COLUMN total_flash")
        c.executescript("""
            INSERT INTO users (id, username, email, hashed_password, role) VALUES (1, 'admin', 'a@x', 'h', 'super_admin');
            INSERT INTO courses (id, code, name) VALUES (1, 'CS101', 'Intro');
            INSERT INTO class_sessions (id, name, code, teacher_id, course_id, course_section) VALUES (1, 'A', 'C1', 1, 1, 'A');
            INSERT INTO students (id, roll_number, student_name) VALUES (1, 'ABCDE12345', 'Asha');
            INSERT INTO quizzes (id, class_session_id, title) VALUES (1, 1, 'Q');
            INSERT INTO polls (id, class_session_id, title, options) VALUES (1, 1, 'P', '["a","b"]');
            -- the same press relayed three times (pre-dedup firmware): keep id 10
            INSERT INTO quiz_answers (id, quiz_id, question_order, student_id, selected_option) VALUES
                (10, 1, 0, 1, 2), (11, 1, 0, 1, 2), (12, 1, 0, 1, 3);
            INSERT INTO poll_votes (id, poll_id, student_id, selected_option) VALUES (20, 1, 1, 0), (21, 1, 1, 1);
            INSERT INTO student_enrollments (id, class_session_id, student_id) VALUES (30, 1, 1), (31, 1, 1);
            -- a hard-deleted student (999) left a dangling nullable reference
            INSERT INTO quiz_answers (id, quiz_id, question_order, student_id, selected_option) VALUES (13, 1, 1, 999, 0);
            -- attendance of a deleted class: required parent gone, unreachable row
            INSERT INTO attendance (id, class_session_id) VALUES (40, 999);
            INSERT INTO esp_devices (id, mac_address, gateway_id) VALUES (50, 'AA:00:00:00:00:01', 999);
        """)


def test_fresh_database_gets_every_migration_and_no_backup(tmp_path):
    db = tmp_path / "fresh.db"
    assert _migrate(db) == _all_versions()
    assert [r[0] for r in _q(db, "SELECT version FROM schema_migrations ORDER BY version")] == _all_versions()
    assert _indexes(db) == _model_unique_indexes()
    assert _backups(db) == []
    assert _migrate(db) == []                         # idempotent: nothing pending


def test_legacy_database_is_backed_up_repaired_and_constrained(tmp_path):
    db = tmp_path / "impress.db"
    _legacy_db(db)
    assert _q(db, "PRAGMA foreign_key_check")         # the dirt is really there

    assert _migrate(db) == _all_versions()

    from app.migrations import LATEST
    backups = _backups(db)
    assert len(backups) == 1 and backups[0].startswith(f"impress.db.bak-0-to-{LATEST}-")
    assert _q(tmp_path / backups[0], "SELECT COUNT(*) FROM quiz_answers") == [(4,)]   # untouched copy

    assert "total_flash" in {r[1] for r in _q(db, "PRAGMA table_info(esp_devices)")}  # baseline column
    assert _q(db, "PRAGMA foreign_key_check") == []
    assert _q(db, "SELECT student_id FROM quiz_answers WHERE id = 13") == [(None,)]   # nullable → NULL
    assert _q(db, "SELECT COUNT(*) FROM attendance WHERE id = 40") == [(0,)]          # orphan removed
    assert _q(db, "SELECT gateway_id FROM esp_devices WHERE id = 50") == [(None,)]
    # first answer / vote / enrollment wins, as the application always intended
    assert _q(db, "SELECT id, selected_option FROM quiz_answers WHERE question_order = 0") == [(10, 2)]
    assert _q(db, "SELECT id FROM poll_votes") == [(20,)]
    assert _q(db, "SELECT id FROM student_enrollments") == [(30,)]
    assert _indexes(db) == _model_unique_indexes()          # same as a fresh install

    assert _migrate(db) == [] and len(_backups(db)) == 1   # second start: no-op, no new backup


def test_duplicate_sections_stop_the_upgrade_with_instructions(tmp_path):
    from app.migrations import MigrationError
    db = tmp_path / "impress.db"
    _legacy_db(db)
    with sqlite3.connect(db) as c:
        c.execute("INSERT INTO class_sessions (id, name, code, teacher_id, course_id, course_section) "
                  "VALUES (2, 'A again', 'C2', 1, 1, 'A')")
    with pytest.raises(MigrationError) as e:
        _migrate(db)
    assert "class_sessions" in str(e.value) and "section" in str(e.value)
    # steps 1-2 committed, step 3 left no trace: no index, no record, both classes kept
    assert [r[0] for r in _q(db, "SELECT version FROM schema_migrations ORDER BY version")] == [1, 2]
    from app.migrations import UNIQUE_INDEXES
    assert not _indexes(db) & {name for name, *_ in UNIQUE_INDEXES}      # step 3 created none of its indexes
    assert _q(db, "SELECT COUNT(*) FROM class_sessions") == [(2,)]
    # once resolved, the next start completes
    with sqlite3.connect(db) as c:
        c.execute("UPDATE class_sessions SET course_section = 'B' WHERE id = 2")
    assert _migrate(db) == [v for v in _all_versions() if v >= 3]


def test_a_failing_step_rolls_back_its_ddl(tmp_path, monkeypatch):
    db = tmp_path / "impress.db"
    _migrate(db)                                      # fresh, at the latest version

    async def bad_step(conn):
        from sqlalchemy import text
        await conn.execute(text("ALTER TABLE students ADD COLUMN half_done INTEGER"))
        await conn.execute(text("CREATE UNIQUE INDEX uq_half_done ON students (half_done)"))
        raise RuntimeError("power cut mid-migration")

    from app.migrations import MIGRATIONS
    with pytest.raises(RuntimeError):
        _migrate(db, steps=MIGRATIONS + [(999, "bad", bad_step)], monkeypatch=monkeypatch)
    assert "half_done" not in {r[1] for r in _q(db, "PRAGMA table_info(students)")}
    assert _q(db, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'uq_half_done'") == [(0,)]
    from app.migrations import LATEST                 # the real list; MIGRATIONS is patched
    assert [r[0] for r in _q(db, "SELECT MAX(version) FROM schema_migrations")] == [LATEST]


def test_duplicate_question_positions_are_renumbered(tmp_path):
    db = tmp_path / "impress.db"
    _legacy_db(db)
    with sqlite3.connect(db) as c:
        c.execute("INSERT INTO quiz_questions (id, quiz_id, order_num, question_text, options, correct_option) "
                  "VALUES (60, 1, 0, 'first', '[\"a\",\"b\"]', 0), (61, 1, 0, 'second', '[\"a\",\"b\"]', 0), "
                  "(62, 1, 1, 'third', '[\"a\",\"b\"]', 0)")
    _migrate(db)
    assert _q(db, "SELECT question_text, order_num FROM quiz_questions ORDER BY order_num") == [
        ("first", 0), ("second", 1), ("third", 2)]
    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(db) as c:
            c.execute("INSERT INTO quiz_questions (quiz_id, order_num, question_text, options, correct_option) "
                      "VALUES (1, 2, 'clash', '[]', 0)")


def test_app_reports_its_schema_version(client):
    from app.migrations import LATEST
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["schema_version"] == LATEST
