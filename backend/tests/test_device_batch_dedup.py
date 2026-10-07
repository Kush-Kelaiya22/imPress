"""#6: /api/device/batch validates and de-duplicates mesh answers/votes."""

import pytest
from sqlalchemy import func, select

from conftest import DEVICE, DEVICE_KEY, auth, login

ROLL = "ABCDE12345"


@pytest.fixture
def setup(client, db):
    from app.models import Student
    h = auth(login(client))
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Chem", "code": "CHEM1"}).json()["id"]
    quiz = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q1", "options": ["a", "b", "c", "d"], "correct_option": 0},
        {"question_text": "q2", "options": ["x", "y"], "correct_option": 0}]}).json()["id"]
    assert client.post(f"/api/quizzes/{quiz}/start", headers=h).status_code == 200
    poll = client.post("/api/polls/", headers=h, json={
        "class_session_id": cid, "title": "P", "options": ["1", "2", "3"], "poll_mode": "live"}).json()["id"]

    async def add_students(s):
        s.add_all([Student(roll_number=ROLL, student_name="A"), Student(roll_number="ZZZZZ99999", student_name="B")])
    db(add_students)
    return {"h": h, "class": cid, "quiz": quiz, "poll": poll}


def answer(quiz, roll=ROLL, order=0, option=1):
    return {"type": "quiz_answer", "quiz_id": quiz, "question_order": order,
            "enrollment_number": roll, "selected_option": option, "response_time_ms": 0}


def vote(poll, roll=ROLL, option=2):
    return {"type": "poll_vote", "poll_id": poll, "enrollment_number": roll, "selected_option": option}


def batch(client, *msgs):
    r = client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": list(msgs)})
    assert r.status_code == 200, r.text
    return r.json()


def count(db, model):
    async def q(s):
        return await s.scalar(select(func.count()).select_from(model))
    return db(q)


def test_relay_copies_in_one_batch_and_across_batches_stored_once(client, db, setup):
    from app.models import PollVote, QuizAnswer
    a, v = answer(setup["quiz"]), vote(setup["poll"])
    assert batch(client, a, a, a, v, v) == {"status": "ok", "processed": 2, "skipped": 3}
    assert batch(client, a, v)["skipped"] == 2
    assert count(db, QuizAnswer) == 1 and count(db, PollVote) == 1


def test_distinct_students_and_questions_all_count(client, db, setup):
    from app.models import QuizAnswer
    q = setup["quiz"]
    assert batch(client, answer(q), answer(q, roll="ZZZZZ99999"), answer(q, order=1, option=0))["processed"] == 3
    assert count(db, QuizAnswer) == 3


@pytest.mark.parametrize("bad", [
    {"quiz_id": 999},                      # unknown quiz
    {"enrollment_number": "NOPE000000"},   # unknown student
    {"question_order": 7},                 # unknown question
    {"selected_option": 4},                # q1 has 4 options (0-3)
    {"question_order": 1, "selected_option": 2},   # q2 has 2 options
    {"selected_option": "1"},              # wrong type
])
def test_invalid_answers_skipped(client, db, setup, bad):
    from app.models import QuizAnswer
    assert batch(client, {**answer(setup["quiz"]), **bad}) == {"status": "ok", "processed": 0, "skipped": 1}
    assert count(db, QuizAnswer) == 0


def test_inactive_quiz_and_closed_poll_skipped(client, db, setup):
    assert client.post(f"/api/quizzes/{setup['quiz']}/stop", headers=setup["h"]).status_code == 200
    assert client.post(f"/api/polls/{setup['poll']}/end", headers=setup["h"]).status_code == 200
    assert batch(client, answer(setup["quiz"]), vote(setup["poll"]))["skipped"] == 2


def test_vote_out_of_range_skipped(client, setup):
    assert batch(client, vote(setup["poll"], option=3))["skipped"] == 1


def test_stored_answers_broadcast_live_counts(client, setup):
    with client.websocket_connect(f"/ws/class/{setup['class']}?role=device&api_key={DEVICE_KEY}") as ws:
        ws.receive_json()                                  # "connected"
        batch(client, answer(setup["quiz"]), answer(setup["quiz"]), vote(setup["poll"]))
        # Marker after the batch: a missing broadcast fails instead of blocking.
        from app.ws.manager import manager
        client.portal.call(manager.broadcast_to_class, setup["class"], {"event": "marker"})
        frames = []
        while not frames or frames[-1] != {"event": "marker"}:
            frames.append(ws.receive_json())
    assert frames == [   # exactly 2 broadcasts: the duplicate answer wasn't broadcast
        {"type": "quiz_answer", "quiz_id": setup["quiz"], "question_order": 0, "total_answers": 1},
        {"type": "poll_vote", "poll_id": setup["poll"], "selected_option": 2, "total_votes": 1},
        {"event": "marker"},
    ]
