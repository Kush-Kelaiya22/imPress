"""#73: timed quizzes advance (per_question) and end (total) by themselves,
the teacher can still advance or stop early, and late answers are refused.

Time is shifted by moving the quiz's stored start times into the past and
calling the scheduler's `tick` directly; one test waits for the real loop.
`tick` reads only the database, so a quiz whose time ran out while the server
was down is advanced on the first tick after a restart.
"""

import time
from datetime import timedelta

import pytest

from conftest import DEVICE, DEVICE_KEY, auth, login, make_class, make_user

QUESTIONS = [
    {"question_text": "2+2?", "options": ["3", "4", "5"], "correct_option": 1},
    {"question_text": "Capital of India?", "options": ["Mumbai", "Delhi"], "correct_option": 1},
]
ROLL = "ABCDE12345"


@pytest.fixture(autouse=True)
def pause_scheduler(request, monkeypatch):
    """Stop the app's own 1 s loop from racing the explicit ticks below
    (it looks `tick` up on every pass). The real-loop test keeps it."""
    from app.services import quiz_timer
    global _real_tick
    _real_tick = quiz_timer.tick
    if "real_scheduler" not in request.node.name:
        async def idle(db, now=None):
            return []
        monkeypatch.setattr(quiz_timer, "tick", idle)


@pytest.fixture
def env(client, db):
    from app.models import Student
    su = auth(login(client))
    tid, teacher = make_user(client, su, "tch1")
    cid = make_class(client, su, "Bio", "BIO1", teacher_id=tid)

    async def add_student(s):
        s.add_all([Student(roll_number=ROLL, student_name="A"), Student(roll_number="ZZZZZ99999", student_name="B")])
    db(add_student)
    return {"teacher": teacher, "class": cid}


def _start(client, env, **timing):
    r = client.post("/api/quizzes/", headers=env["teacher"], json={
        "class_session_id": env["class"], "title": "Q", "questions": QUESTIONS, "quiz_mode": "impromptu", **timing})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _per_question(client, env, seconds=10):
    return _start(client, env, timing_mode="per_question", question_time_limit=seconds)


def _total(client, env, seconds=60):
    return _start(client, env, timing_mode="total", total_time_limit=seconds)


def _shift(db, qid, seconds, *, question=True, quiz=True):
    """Pretend the current question / the quiz started `seconds` earlier."""
    from app.models import Quiz

    async def go(s):
        q = await s.get(Quiz, qid)
        if question and q.question_started_at:
            q.question_started_at -= timedelta(seconds=seconds)
        if quiz:
            q.started_at -= timedelta(seconds=seconds)
    db(go)


def _tick(db):
    async def go(s):
        return [q.id for q in await _real_tick(s)]
    return db(go)


def _get(client, env, qid):
    return client.get(f"/api/quizzes/{qid}", headers=env["teacher"]).json()


def _mesh_answer(client, qid, order=0, roll=ROLL):
    r = client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "quiz_answer", "quiz_id": qid, "question_order": order, "enrollment_number": roll,
         "selected_option": 1, "response_time_ms": 0}]})
    assert r.status_code == 200, r.text
    return r.json()["processed"] == 1


# ── Scheduler ───────────────────────────────────────────────────────────────

def test_per_question_quiz_advances_then_ends_on_schedule(client, db, env):
    qid = _per_question(client, env, 10)
    _shift(db, qid, 9)
    assert _tick(db) == [] and _get(client, env, qid)["current_question"] == 0      # 1 s left
    _shift(db, qid, 2)
    assert _tick(db) == [qid]
    q = _get(client, env, qid)
    assert (q["status"], q["current_question"]) == ("active", 1)
    assert _tick(db) == []                       # question 2 has its own fresh 10 s
    _shift(db, qid, 11)
    assert _tick(db) == [qid]
    assert _get(client, env, qid)["status"] == "completed"


def test_total_quiz_ends_when_its_time_is_up_on_any_question(client, db, env):
    qid = _total(client, env, 60)
    _shift(db, qid, 59)
    assert _tick(db) == []
    _shift(db, qid, 2)
    assert _tick(db) == [qid]
    q = _get(client, env, qid)
    assert (q["status"], q["is_live"], q["current_question"]) == ("completed", False, 0)


@pytest.mark.parametrize("timing", [{"timing_mode": "manual"},
                                    {"timing_mode": "per_question", "question_time_limit": 0},
                                    {"timing_mode": "total", "total_time_limit": 0}])
def test_manual_and_unlimited_quizzes_are_never_advanced(client, db, env, timing):
    qid = _start(client, env, **timing)
    _shift(db, qid, 3600)
    assert _tick(db) == []
    assert (_get(client, env, qid)["current_question"], _get(client, env, qid)["status"]) == (0, "active")


def test_quiz_running_before_the_upgrade_starts_counting_on_the_first_tick(client, db, env):
    from app.models import Quiz
    qid = _per_question(client, env, 10)

    async def legacy(s):
        (await s.get(Quiz, qid)).question_started_at = None
    db(legacy)
    assert _tick(db) == []

    async def started(s):
        return (await s.get(Quiz, qid)).question_started_at
    assert db(started) is not None
    _shift(db, qid, 11)
    assert _tick(db) == [qid]


def test_teacher_and_timer_cannot_both_advance_one_question(client, db, env):
    from app.models import Quiz
    from app.services.quiz_timer import advance
    qid = _per_question(client, env, 10)

    async def race(s):
        quiz = await s.get(Quiz, qid)            # both read question 0
        return await advance(s, quiz), await advance(s, quiz)
    assert db(race) == (True, False)
    assert _get(client, env, qid)["current_question"] == 1


def test_real_scheduler_advances_without_the_teacher(client, env):
    qid = _per_question(client, env, 1)
    deadline = time.monotonic() + 6
    while _get(client, env, qid)["current_question"] == 0 and time.monotonic() < deadline:
        time.sleep(0.2)
    assert _get(client, env, qid)["current_question"] == 1


# ── Teacher control ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("timing", [{"timing_mode": "per_question", "question_time_limit": 30},
                                    {"timing_mode": "total", "total_time_limit": 300}])
def test_teacher_can_advance_and_stop_a_timed_quiz_early(client, env, timing):
    qid = _start(client, env, **timing)
    n = client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"]).json()
    assert (n["status"], n["current_question"]) == ("active", 1)
    assert client.post(f"/api/quizzes/{qid}/stop", headers=env["teacher"]).json()["status"] == "completed"


def test_next_restarts_the_question_timer(client, db, env):
    qid = _per_question(client, env, 10)
    _shift(db, qid, 8)
    client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"])
    _shift(db, qid, 8, quiz=False)                # 8 s into question 2: still open
    assert _tick(db) == []


def test_total_quiz_sends_modules_the_time_remaining(client, db, env):
    qid = _total(client, env, 60)
    _shift(db, qid, 20)
    with client.websocket_connect(f"/ws/class/{env['class']}?role=device&api_key={DEVICE_KEY}") as ws:
        assert ws.receive_json()["event"] == "connected"
        client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"])
        frame = ws.receive_json()
    assert frame["event"] == "quiz_question" and 39 <= frame["time_limit_s"] <= 40


# ── Late answers are refused server-side ────────────────────────────────────

def test_mesh_answer_within_grace_is_kept_and_after_it_dropped(client, db, env):
    from app.services.quiz_timer import GRACE_S
    qid = _total(client, env, 60)
    _shift(db, qid, 60 + GRACE_S - 1)            # the deadline passed a moment ago
    assert _mesh_answer(client, qid)
    _shift(db, qid, 2)
    assert not _mesh_answer(client, qid, order=1)


def test_mesh_answer_to_a_closed_question_is_dropped(client, db, env):
    from app.services.quiz_timer import GRACE_S
    qid = _per_question(client, env, 10)
    _shift(db, qid, 11)
    _tick(db)                                    # now on question 2
    assert _mesh_answer(client, qid, order=0)    # in flight when the question closed
    _shift(db, qid, GRACE_S + 1, quiz=False)
    assert not _mesh_answer(client, qid, order=0, roll="ZZZZZ99999")


def test_http_answer_after_the_deadline_is_refused(client, db, env):
    qid = _per_question(client, env, 10)
    dev = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "AA:BB:CC:00:00:01", "device_type": "student", "device_name": "s1"}).json()["device_id"]
    _shift(db, qid, 20)                          # timer hasn't ticked yet
    r = client.post(f"/api/quizzes/{qid}/answer", headers=DEVICE, json={"device_id": dev, "selected_option": 1})
    assert r.status_code == 409 and "Time is up" in r.json()["detail"]


def test_manual_quiz_still_accepts_answers_to_earlier_questions(client, env):
    qid = _start(client, env, timing_mode="manual")
    client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"])
    assert _mesh_answer(client, qid, order=0)
