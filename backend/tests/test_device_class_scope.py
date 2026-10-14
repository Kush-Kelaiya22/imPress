"""v2.2: a gateway with its own key reports for its own class only.

Its key already restricted the class WebSocket to the linked class (#121);
the batch and attendance routes accepted answers, votes, attendance and room
links for any class. Now another class's quiz, poll or room is skipped (batch)
or refused (attendance). The shared site key keeps the old behaviour."""

import pytest

from conftest import DEVICE, auth, login, make_class

ROLL = "ABCDE12345"


@pytest.fixture
def rooms(client, db):
    from app.models import Student
    h = auth(login(client))
    a = make_class(client, h, name="A", code="CLSA", classroom_code="RM-A", activate=True)
    b = make_class(client, h, name="B", code="CLSB", classroom_code="RM-B", activate=True)

    def quiz(cid):
        q = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
            {"question_text": "q", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
        assert client.post(f"/api/quizzes/{q}/start", headers=h).status_code == 200
        return q

    def poll(cid):
        return client.post("/api/polls/", headers=h, json={"class_session_id": cid, "title": "P",
                                                           "options": ["1", "2"], "poll_mode": "live"}).json()["id"]

    async def student(s):
        s.add(Student(roll_number=ROLL, student_name="S"))
    db(student)
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:0A", "device_type": "c6", "classroom_code": "RM-A"})
    assert r.status_code == 200 and r.json()["class_id"] == a, r.text
    return {"a": a, "b": b, "qa": quiz(a), "qb": quiz(b), "pa": poll(a), "pb": poll(b),
            "key": {"X-API-Key": r.json()["device_key"]}}


def _batch(client, headers, *msgs):
    r = client.post("/api/device/batch", headers=headers, json={"device_type": "c6", "messages": list(msgs)})
    assert r.status_code == 200, r.text
    return r.json()


def _answer(quiz):
    return {"type": "quiz_answer", "quiz_id": quiz, "question_order": 0, "enrollment_number": ROLL,
            "selected_option": 1, "response_time_ms": 900}


def _vote(poll):
    return {"type": "poll_vote", "poll_id": poll, "enrollment_number": ROLL, "selected_option": 0}


def test_own_class_answers_and_votes_are_recorded(client, rooms):
    assert _batch(client, rooms["key"], _answer(rooms["qa"]), _vote(rooms["pa"]))["processed"] == 2


def test_another_class_answers_and_votes_are_skipped(client, rooms):
    r = _batch(client, rooms["key"], _answer(rooms["qb"]), _vote(rooms["pb"]))
    assert r == {"status": "ok", "processed": 0, "skipped": 2}


def test_a_join_cannot_link_a_student_to_another_room(client, db, rooms):
    from sqlalchemy import select
    from app.models import StudentEnrollment
    _batch(client, rooms["key"], {"type": "student_join", "enrollment_number": ROLL,
                                  "device_mac": "48:F6:EE:00:00:0A", "class_code": "RM-B", "device_id": 1})

    async def enrolled(s):
        return (await s.execute(select(StudentEnrollment.class_session_id))).scalars().all()
    assert rooms["b"] not in db(enrolled)


def test_attendance_for_another_class_is_refused(client, rooms):
    r = client.post("/api/device/attendance", headers=rooms["key"], json={
        "class_code": "CLSB", "enrollment_number": ROLL, "mac_address": "48:F6:EE:00:00:0A"})
    assert r.status_code == 403


def test_an_unlinked_gateway_reports_nothing(client, rooms):
    r = client.post("/api/device/register", headers=DEVICE, json={"mac_address": "48:F6:EE:00:00:0B", "device_type": "c6"})
    key = {"X-API-Key": r.json()["device_key"]}
    assert _batch(client, key, _answer(rooms["qa"]))["skipped"] == 1


def test_the_shared_key_is_not_bound_to_a_room(client, rooms):
    assert _batch(client, DEVICE, _answer(rooms["qb"]))["processed"] == 1
