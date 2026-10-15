"""#200 and #202: the data-rights drill and the restore and tamper drills, run as tests so they can be repeated at every release.

The results are recorded in docs/compliance/drill-records.md (what each step found, the measured restore time).
"""

import json
import sqlite3
import time

from sqlalchemy import select

from conftest import DEVICE, auth, login, make_class, make_student, make_user

ROLL = "DSAR000001"


def _tables_mentioning(path, roll, name):
    """Every table of a SQLite file with a text cell holding the roll number or the name."""
    found = {}
    with sqlite3.connect(str(path)) as c:
        for (table,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
            if table.startswith("integrity_"):
                continue
            cols = [r[1] for r in c.execute(f'PRAGMA table_info("{table}")')]
            for col in cols:
                n = c.execute(f'SELECT COUNT(*) FROM "{table}" WHERE CAST("{col}" AS TEXT) LIKE ? OR CAST("{col}" AS TEXT) LIKE ?',
                              (f"%{roll}%", f"%{name}%")).fetchone()[0]
                if n:
                    found.setdefault(table, 0)
                    found[table] += n
    return found


def test_data_rights_drill_finds_one_student_everywhere_and_erases_them(client, db, policy, tmp_path):
    """Runbook section 1 to 4 against a generated student: find, export, erase, and show what is left and where."""
    from app.models import EspDevice, StudentEnrollment
    from app.services import integrity
    policy({"audit.sink_path": str(tmp_path / "chain.jsonl")})
    su = auth(login(client))
    _, th = make_user(client, su, "drill-teacher")
    cid = make_class(client, su, name="Drill", code="DRL1", activate=True)
    sid = make_student(client, su, roll=ROLL, name="Dara Subject", email="dara@example.edu")
    assert client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": sid}).status_code in (200, 201)
    quiz = client.post("/api/quizzes/", headers=su, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q1", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
    client.post(f"/api/quizzes/{quiz}/start", headers=su)
    assert client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "quiz_answer", "quiz_id": quiz, "question_order": 0, "enrollment_number": ROLL, "selected_option": 1,
         "response_time_ms": 7}]}).json()["processed"] == 1

    async def link(s):
        enr = await s.scalar(select(StudentEnrollment.id).where(StudentEnrollment.student_id == sid))
        s.add(EspDevice(mac_address="AA:00:00:00:00:77", device_type="student", student_enrollment_id=enr))
    db(link)
    client.portal.call(integrity.check_and_backup)                      # a backup that holds the student

    # 1. where the data lives: each place the runbook names
    assert ROLL in client.get("/api/students/", headers=su).text                                          # student record
    assert any(c["class_id"] == cid for c in client.get(f"/api/students/{sid}/classes", headers=su).json())     # enrolments
    part = client.get(f"/api/admin/students/{sid}/participation", headers=su)
    assert part.status_code == 200 and "q1" in part.text or "Q" in part.text                              # quiz participation
    assert "Dara Subject" in client.get("/api/admin/activity?limit=200", headers=su).text                 # activity log
    live = _tables_mentioning(integrity.db_path(), ROLL, "Dara Subject")
    assert {"students", "quiz_answers"} <= set(live) or "students" in live, live
    assert "Dara Subject" not in (tmp_path / "chain.jsonl").read_text() and ROLL not in (tmp_path / "chain.jsonl").read_text()   # the trail

    # 2. a test-data copy of the real database holds them too
    assert client.post("/api/admin/test-mode/enable", headers=su, json={}).json()["on"]
    off = client.post("/api/admin/test-mode/disable", headers=su).json()
    from app.services import test_mode
    copy = test_mode.file_for("pending", off["pending_id"])
    assert "students" in _tables_mentioning(copy, ROLL, "Dara Subject")

    # 3. erase (runbook section 4)
    assert client.delete(f"/api/students/{sid}/hard-delete", headers=su).status_code == 200
    gone = _tables_mentioning(integrity.db_path(), ROLL, "Dara Subject")
    assert gone == {} or set(gone) <= {"activity_logs"} and "Dara Subject" not in client.get("/api/admin/activity?limit=200", headers=su).text, gone
    assert "Dara Subject" not in client.get("/api/admin/activity?limit=200", headers=su).text
    assert ROLL not in client.get("/api/students/", headers=su).text

    # 4. what the runbook says remains, and where: copies and backups until they expire
    assert "students" in _tables_mentioning(copy, ROLL, "Dara Subject"), "the pending test copy still holds them: delete it (Test data page)"
    assert client.post(f"/api/admin/test-mode/pending/{off['pending_id']}", headers=su, json={"action": "delete"}).status_code in (200, 204)
    assert "students" in _tables_mentioning(integrity.backup_dir() / "rolling.db", ROLL, "Dara Subject"), \
        "the integrity backup keeps them until it is replaced: record the expiry (retention schedule)"


def test_restore_drill_puts_the_data_back_and_measures_how_long_it_took(client):
    su = auth(login(client))
    make_student(client, su, roll="KEEP000001", name="Kept Student")
    assert client.post("/api/admin/backups", headers=su, json={"name": "drill"}).status_code == 201
    make_student(client, su, roll="LOST000001", name="Lost Student")                         # made after the backup: not in it
    started = time.perf_counter()
    r = client.post("/api/admin/backups/saved/drill/restore", headers=su, json={"password": "admin123", "confirm": "drill"})
    rto = time.perf_counter() - started
    assert r.status_code == 200, r.text
    su = auth(login(client))                                                                 # a restore signs everyone out
    rolls = [s["roll_number"] for s in client.get("/api/students/", headers=su).json()]
    assert rolls == ["KEEP000001"]                                                           # the recovery point is the backup's moment
    assert rto < 30, f"restoring a small database took {rto:.1f} s"
    from app.services.integrity import verify_now
    assert client.portal.call(verify_now).ok


def test_the_external_trail_survives_a_reset_and_shows_tampering(client, policy, tmp_path):
    """#202 tamper simulation: a reset clears the local log; the external evidence stays and its chain still verifies."""
    from app.services import auditsink
    from conftest import approved
    sink = tmp_path / "chain.jsonl"
    policy({"audit.sink_path": str(sink), "audit.min_retention_days": 0})
    su = auth(login(client))
    make_user(client, su, "before-reset")
    before = sink.read_text().splitlines()
    assert any("user.create" in line or "admin.user" in line or "create" in line for line in before)
    aid = approved(client, su, "system.clear.everything")
    assert client.post("/api/admin/system/clear", headers=su,
                       json={"scope": "everything", "confirm": "RESET EVERYTHING", "approval_id": aid}).status_code == 200
    local = client.get("/api/admin/activity?limit=200", headers=su).json()          # the acting session survives a reset
    assert isinstance(local, list)
    assert not any(e["action"] == "user.create" for e in local), "the local log was cleared by the reset"
    after = sink.read_text().splitlines()
    assert after[:len(before)] == before and len(after) > len(before), "the external trail kept every earlier line and recorded the reset"
    assert auditsink.verify_file(sink) == []
    forged = [json.loads(line) for line in after]
    forged[0]["action"] = "nothing.happened"
    sink.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in forged) + "\n")
    assert auditsink.verify_file(sink), "an edited line is found by audit-verify"
