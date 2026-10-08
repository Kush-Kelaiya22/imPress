"""#41: the database enforces its own integrity (foreign keys, uniqueness), and
every delete path leaves no dangling reference behind."""

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from conftest import DEVICE, auth, login, make_class, make_student, make_user

ROLL = "ABCDE12345"


def _fk_violations(db):
    async def q(s):
        return (await s.execute(text("PRAGMA foreign_key_check"))).all()
    return db(q)


def _count(db, model, *where):
    async def q(s):
        return await s.scalar(select(func.count()).select_from(model).where(*where))
    return db(q)


@pytest.fixture
def world(client, db):
    """A class with a quiz, a poll, an enrolled student who answered and voted
    over the mesh, attendance, and a student module linked to the enrollment."""
    from app.models import EspDevice, StudentEnrollment
    h = auth(login(client))
    tid, th = make_user(client, h, "teach1")
    cid = make_class(client, h, name="Chem", code="CHEM1", activate=True)
    assert client.post(f"/api/admin/classes/{cid}/assign-teacher", headers=h,
                       json={"teacher_id": tid}).status_code == 200
    sid = make_student(client, h, roll=ROLL)
    assert client.post(f"/api/admin/classes/{cid}/enroll", headers=h, json={"student_id": sid}).status_code == 200
    quiz = client.post("/api/quizzes/", headers=th, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q1", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
    assert client.post(f"/api/quizzes/{quiz}/start", headers=th).status_code == 200
    poll = client.post("/api/polls/", headers=th, json={
        "class_session_id": cid, "title": "P", "options": ["1", "2"], "poll_mode": "live"}).json()["id"]
    r = client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "quiz_answer", "quiz_id": quiz, "question_order": 0, "enrollment_number": ROLL,
         "selected_option": 1, "response_time_ms": 5},
        {"type": "poll_vote", "poll_id": poll, "enrollment_number": ROLL, "selected_option": 0}]})
    assert r.status_code == 200 and r.json()["processed"] == 2, r.text

    async def link_module(s):
        enr = await s.scalar(select(StudentEnrollment.id).where(StudentEnrollment.student_id == sid))
        s.add(EspDevice(mac_address="AA:00:00:00:00:99", device_type="student", student_enrollment_id=enr))
    db(link_module)
    return {"h": h, "th": th, "class": cid, "student": sid, "quiz": quiz, "poll": poll}


# ── Foreign keys are enforced ───────────────────────────────────────────────

def test_foreign_keys_are_enforced(client, db):
    from app.models import QuizAnswer

    async def orphan(s):
        s.add(QuizAnswer(quiz_id=999, question_order=0, selected_option=0))
        await s.flush()
    with pytest.raises(IntegrityError):
        db(orphan)


# ── Delete paths leave nothing dangling ─────────────────────────────────────

def test_teacher_can_delete_a_class_that_has_quizzes_and_polls(client, db, world):
    from app.models import ClassSession, Poll, PollVote, Quiz, QuizAnswer, StudentEnrollment
    r = client.delete(f"/api/classes/{world['class']}", headers=world["th"])
    assert r.status_code == 200, r.text
    assert _count(db, ClassSession, ClassSession.id == world["class"]) == 0
    for model in (Quiz, Poll, QuizAnswer, PollVote, StudentEnrollment):
        assert _count(db, model) == 0, model.__name__
    assert _fk_violations(db) == []


def test_admin_class_delete_detaches_modules_linked_to_its_enrollments(client, db, world):
    from app.models import EspDevice
    assert client.delete(f"/api/admin/classes/{world['class']}", headers=world["h"]).status_code == 200
    assert _count(db, EspDevice, EspDevice.mac_address == "AA:00:00:00:00:99") == 1   # module kept
    assert _fk_violations(db) == []


def test_hard_deleted_student_leaves_anonymous_results(client, db, world):
    from app.models import PollVote, QuizAnswer
    r = client.delete(f"/api/students/{world['student']}/hard-delete", headers=world["h"])
    assert r.status_code == 200, r.text
    # class statistics stay intact; the identity link is gone
    assert _count(db, QuizAnswer) == 1 and _count(db, QuizAnswer, QuizAnswer.student_id.is_not(None)) == 0
    assert _count(db, PollVote) == 1 and _count(db, PollVote, PollVote.student_id.is_not(None)) == 0
    assert _fk_violations(db) == []
    results = client.get(f"/api/quizzes/{world['quiz']}/results", headers=world["th"])
    assert results.status_code == 200, results.text


# ── Uniqueness lives in the database, not only in application checks ───────

def _insert_twice(db, factory):
    async def go(s):
        s.add(factory())
        await s.flush()
        s.add(factory())
        await s.flush()
    with pytest.raises(IntegrityError):
        db(go)


def test_one_answer_per_student_and_question(client, db, world):
    from app.models import QuizAnswer
    _insert_twice(db, lambda: QuizAnswer(quiz_id=world["quiz"], question_order=5,
                                         student_id=world["student"], selected_option=0))


def test_one_answer_per_device_and_question(client, db, world):
    from app.models import EspDevice, QuizAnswer

    async def dev(s):
        return await s.scalar(select(EspDevice.id).where(EspDevice.mac_address == "AA:00:00:00:00:99"))
    did = db(dev)
    _insert_twice(db, lambda: QuizAnswer(quiz_id=world["quiz"], question_order=5, device_id=did,
                                         selected_option=0))


def test_answers_without_identity_are_not_constrained(client, db, world):
    from app.models import QuizAnswer

    async def go(s):   # NULL student and device: unknown origin, no uniqueness to enforce
        s.add_all([QuizAnswer(quiz_id=world["quiz"], question_order=7, selected_option=0) for _ in range(3)])
    db(go)
    assert _count(db, QuizAnswer, QuizAnswer.question_order == 7) == 3


def test_one_vote_per_student_and_per_device(client, db, world):
    from app.models import PollVote
    _insert_twice(db, lambda: PollVote(poll_id=world["poll"], student_id=world["student"], selected_option=1))


def test_one_enrollment_per_student_and_class(client, db, world):
    from app.models import StudentEnrollment
    _insert_twice(db, lambda: StudentEnrollment(class_session_id=world["class"], student_id=world["student"]))


def test_section_is_unique_within_a_course(client):
    h = auth(login(client))
    course = client.post("/api/courses/", headers=h, json={"code": "CS101", "name": "Intro"}).json()["id"]
    first = client.post("/api/admin/classes", headers=h, json={
        "name": "CS101 A", "code": "CS101-A", "course_id": course, "course_section": "A"})
    assert first.status_code == 201, first.text
    dup = client.post("/api/admin/classes", headers=h, json={
        "name": "CS101 A again", "code": "CS101-A2", "course_id": course, "course_section": "A"})
    assert dup.status_code == 409 and "section" in dup.json()["detail"].lower()
    other = client.post("/api/admin/classes", headers=h, json={
        "name": "CS101 B", "code": "CS101-B", "course_id": course, "course_section": "B"})
    assert other.status_code == 201
    # classes without a course, or without a section label, aren't constrained
    for i in range(2):
        assert client.post("/api/admin/classes", headers=h, json={
            "name": f"Free {i}", "code": f"FREE{i}", "course_id": course, "course_section": ""}).status_code == 201


def test_section_rename_into_a_taken_section_is_rejected(client):
    h = auth(login(client))
    course = client.post("/api/courses/", headers=h, json={"code": "MA1", "name": "Maths"}).json()["id"]
    client.post("/api/admin/classes", headers=h, json={"name": "A", "code": "MA1-A", "course_id": course, "course_section": "A"})
    b = client.post("/api/admin/classes", headers=h, json={
        "name": "B", "code": "MA1-B", "course_id": course, "course_section": "B"}).json()["id"]
    r = client.put(f"/api/admin/classes/{b}", headers=h, json={"course_section": "A"})
    assert r.status_code == 409, r.text


# ── Races surface as clean errors, never 500 ────────────────────────────────

def test_commit_or_conflict_turns_a_unique_violation_into_409(client, db, world):
    from fastapi import HTTPException

    from app.database import commit_or_conflict
    from app.models import StudentEnrollment

    async def race(s):
        s.add(StudentEnrollment(class_session_id=world["class"], student_id=world["student"]))
        await commit_or_conflict(s, "Student is already enrolled")
    with pytest.raises(HTTPException) as e:
        db(race)
    assert e.value.status_code == 409 and e.value.detail == "Student is already enrolled"

