"""#186: a class with a roster counts only its enrolled students; the
teacher is told about answers that were not counted. A class without any
enrolment keeps counting everyone (sites that never set up rosters)."""

import pytest

from conftest import DEVICE, auth, login, make_class, make_student

IN, OUT = "INCLASS001", "VISITOR001"


@pytest.fixture
def room(client, monkeypatch):
    h = auth(login(client))
    cid = make_class(client, h)
    make_student(client, h, roll=IN, name="In Class")
    make_student(client, h, roll=OUT, name="Visiting Student")
    quiz = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
    assert client.post(f"/api/quizzes/{quiz}/start", headers=h).status_code == 200
    poll = client.post("/api/polls/", headers=h, json={"class_session_id": cid, "title": "P",
                                                       "options": ["1", "2"], "poll_mode": "live"}).json()["id"]
    sent = []

    async def capture(class_id, event, role="everyone"):
        sent.append((class_id, dict(event), role))
    from app.ws.manager import manager
    monkeypatch.setattr(manager, "broadcast_to_class", capture)
    monkeypatch.setattr(manager, "broadcast_to_role", capture)
    return {"h": h, "cid": cid, "quiz": quiz, "poll": poll, "sent": sent}


def _enrol(client, room, roll):
    sid = next(s["id"] for s in client.get("/api/students/", headers=room["h"]).json() if s["roll_number"] == roll)
    r = client.post(f"/api/admin/classes/{room['cid']}/enroll", headers=room["h"], json={"student_id": sid})
    assert r.status_code in (200, 201), r.text


def _batch(client, *msgs):
    r = client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": list(msgs)})
    assert r.status_code == 200, r.text
    return r.json()


def _answer(room, roll):
    return {"type": "quiz_answer", "quiz_id": room["quiz"], "question_order": 0, "enrollment_number": roll,
            "selected_option": 1, "response_time_ms": 500}


def _vote(room, roll):
    return {"type": "poll_vote", "poll_id": room["poll"], "enrollment_number": roll, "selected_option": 0}


def _notices(room):
    return [e for _, e, _ in room["sent"] if e["type"] == "answer_not_counted"]


def test_with_a_roster_only_enrolled_students_count(client, room):
    _enrol(client, room, IN)
    assert _batch(client, _answer(room, IN), _answer(room, OUT)) == {"status": "ok", "processed": 1, "skipped": 1}
    assert _batch(client, _vote(room, IN), _vote(room, OUT)) == {"status": "ok", "processed": 1, "skipped": 1}


def test_the_teacher_is_told_once_per_student(client, room):
    _enrol(client, room, IN)
    _batch(client, _answer(room, OUT), _answer(room, OUT), _vote(room, OUT))
    n = _notices(room)
    assert len(n) == 1 and n[0]["enrollment_number"] == OUT and n[0]["student_name"] == "Visiting Student"
    # sent to this class's teachers only: it names a student, the gateway doesn't need it
    assert [(cid, role) for cid, e, role in room["sent"] if e["type"] == "answer_not_counted"] == [(room["cid"], "teacher")]


def test_enrolling_the_student_makes_the_next_answer_count(client, room):
    _enrol(client, room, IN)
    assert _batch(client, _answer(room, OUT))["skipped"] == 1
    _enrol(client, room, OUT)
    assert _batch(client, _answer(room, OUT))["processed"] == 1


def test_a_class_without_a_roster_counts_everyone(client, room):
    assert _batch(client, _answer(room, IN), _answer(room, OUT))["processed"] == 2
    assert _notices(room) == []
