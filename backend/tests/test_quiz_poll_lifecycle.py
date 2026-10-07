"""Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).

Quiz:  draft ──start──▶ active ──next…──▶ (past last question) completed
                             └──stop──▶ completed
       impromptu quizzes are created active.
Poll:  planned: draft ──start──▶ active ──end──▶ closed ; live: created active.
"""

import pytest

from conftest import DEVICE, auth, login, make_class, make_user

QUESTIONS = [
    {"question_text": "2+2?", "options": ["3", "4", "5"], "correct_option": 1},
    {"question_text": "Capital of India?", "options": ["Mumbai", "Delhi"], "correct_option": 1},
]


@pytest.fixture
def env(client):
    su = auth(login(client))
    tid, teacher = make_user(client, su, "tch1")
    _, other = make_user(client, su, "tch2")
    cid = make_class(client, su, "Bio", "BIO1", teacher_id=tid)
    return {"su": su, "teacher": teacher, "other": other, "class": cid}


def _quiz(client, env, **extra):
    r = client.post("/api/quizzes/", headers=env["teacher"],
                    json={"class_session_id": env["class"], "title": "Q", "questions": QUESTIONS, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def _poll(client, env, mode="planned", options=("Yes", "No", "Maybe")):
    r = client.post("/api/polls/", headers=env["teacher"], json={
        "class_session_id": env["class"], "title": "Lab Friday?", "options": list(options), "poll_mode": mode})
    assert r.status_code == 201, r.text
    return r.json()


# ── Quiz ────────────────────────────────────────────────────────────────────

def test_planned_quiz_starts_as_draft(client, env):
    q = _quiz(client, env)
    assert (q["status"], q["is_live"], q["question_count"]) == ("draft", False, 2)


def test_impromptu_quiz_is_live_immediately(client, env):
    q = _quiz(client, env, quiz_mode="impromptu")
    assert (q["status"], q["is_live"], q["current_question"]) == ("active", True, 0)


def test_quiz_full_walkthrough(client, env):
    qid = _quiz(client, env)["id"]
    s = client.post(f"/api/quizzes/{qid}/start", headers=env["teacher"]).json()
    assert (s["status"], s["current_question"]) == ("active", 0)
    assert client.post(f"/api/quizzes/{qid}/start", headers=env["teacher"]).status_code == 400   # already active
    n = client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"]).json()
    assert n["current_question"] == 1 and n["status"] == "active"
    end = client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"]).json()   # past the last question
    assert (end["status"], end["is_live"]) == ("completed", False)
    assert client.post(f"/api/quizzes/{qid}/next", headers=env["teacher"]).status_code == 400


def test_stop_completes_quiz(client, env):
    qid = _quiz(client, env, quiz_mode="impromptu")["id"]
    assert client.post(f"/api/quizzes/{qid}/stop", headers=env["teacher"]).json()["status"] == "completed"


def test_other_teacher_cannot_run_quiz(client, env):
    qid = _quiz(client, env)["id"]
    for action in ("start", "next", "stop"):
        assert client.post(f"/api/quizzes/{qid}/{action}", headers=env["other"]).status_code == 403
    bad = client.post("/api/quizzes/", headers=env["other"],
                      json={"class_session_id": env["class"], "title": "X", "questions": QUESTIONS})
    assert bad.status_code == 403


@pytest.mark.parametrize("questions", [[], [{"question_text": "q", "options": ["only one"], "correct_option": 0}]])
def test_quiz_validation(client, env, questions):
    r = client.post("/api/quizzes/", headers=env["teacher"],
                    json={"class_session_id": env["class"], "title": "Q", "questions": questions})
    assert r.status_code == 422


def test_quiz_results_aggregate_per_question(client, env):
    qid = _quiz(client, env, quiz_mode="impromptu")["id"]
    devs = []
    for i in range(3):
        devs.append(client.post("/api/device/register", headers=DEVICE, json={
            "mac_address": f"AA:BB:CC:00:00:0{i}", "device_type": "student", "device_name": f"s{i}"}).json()["device_id"])
    for dev, opt in zip(devs, (1, 1, 2)):
        assert client.post(f"/api/quizzes/{qid}/answer", headers=DEVICE,
                           json={"device_id": dev, "selected_option": opt}).status_code == 200
    res = client.get(f"/api/quizzes/{qid}/results", headers=env["teacher"]).json()
    assert (res["quiz_id"], res["status"]) == (qid, "active")
    q1, q2 = res["results"]
    assert q1["total_answers"] == 3 and q1["option_counts"] == [0, 2, 1] and q1["correct_option"] == 1
    assert q2["total_answers"] == 0 and q2["option_counts"] == [0, 0]


def test_list_quizzes_for_class(client, env):
    _quiz(client, env)
    _quiz(client, env)
    assert len(client.get(f"/api/quizzes/class/{env['class']}", headers=env["teacher"]).json()) == 2
    assert client.get(f"/api/quizzes/class/{env['class']}", headers=env["other"]).status_code == 403


# ── Poll ────────────────────────────────────────────────────────────────────

def test_live_poll_is_active_immediately(client, env):
    p = _poll(client, env, mode="live")
    assert (p["status"], p["is_live"], p["total_votes"]) == ("active", True, 0)


def test_planned_poll_lifecycle(client, env):
    pid = _poll(client, env)["id"]
    assert client.get(f"/api/polls/{pid}", headers=env["teacher"]).json()["status"] == "draft"
    assert client.post(f"/api/polls/{pid}/start", headers=env["teacher"]).json()["status"] == "active"
    assert client.post(f"/api/polls/{pid}/start", headers=env["teacher"]).status_code == 400
    assert client.post(f"/api/polls/{pid}/end", headers=env["teacher"]).json()["status"] == "closed"


@pytest.mark.parametrize("options", [["only"], ["a", "b", "c", "d", "e", "f", "g"]])
def test_poll_option_count_limits(client, env, options):
    r = client.post("/api/polls/", headers=env["teacher"], json={
        "class_session_id": env["class"], "title": "T", "options": options})
    assert r.status_code == 422


def test_poll_results_and_ended_vote_rejected(client, env):
    pid = _poll(client, env, mode="live")["id"]
    devs = [client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": f"AA:BB:CC:00:01:0{i}", "device_type": "student", "device_name": f"s{i}"}).json()["device_id"]
        for i in range(3)]
    for dev, opt in zip(devs, (0, 2, 2)):
        client.post(f"/api/polls/{pid}/vote", headers=DEVICE, json={"device_id": dev, "selected_option": opt})
    res = client.get(f"/api/polls/{pid}/results", headers=env["teacher"]).json()
    assert res["total_votes"] == 3 and res["option_counts"] == [1, 0, 2]
    client.post(f"/api/polls/{pid}/end", headers=env["teacher"])
    late = client.post(f"/api/polls/{pid}/vote", headers=DEVICE, json={"device_id": devs[0], "selected_option": 1})
    assert late.status_code == 400


def test_other_teacher_cannot_run_poll(client, env):
    pid = _poll(client, env)["id"]
    assert client.post(f"/api/polls/{pid}/start", headers=env["other"]).status_code == 403
    assert client.post(f"/api/polls/{pid}/end", headers=env["other"]).status_code == 403
