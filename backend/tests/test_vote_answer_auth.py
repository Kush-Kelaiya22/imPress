"""#9: poll vote / quiz answer endpoints require the device key, a registered
device and an in-range option; ballot stuffing by incrementing device_id fails."""

import pytest

from conftest import DEVICE, auth, login


@pytest.fixture
def live(client):
    h = auth(login(client))
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Bio", "code": "BIO1"}).json()["id"]
    poll = client.post("/api/polls/", headers=h, json={
        "class_session_id": cid, "title": "T?", "options": ["a", "b", "c"], "poll_mode": "live"})
    assert poll.status_code == 201 and poll.json()["status"] == "active", poll.text
    quiz = client.post("/api/quizzes/", headers=h, json={
        "class_session_id": cid, "title": "Q", "questions": [
            {"question_text": "q1", "options": ["1", "2", "3", "4"], "correct_option": 0},
            {"question_text": "q2", "options": ["x", "y"], "correct_option": 1}]})
    qid = quiz.json()["id"]
    assert client.post(f"/api/quizzes/{qid}/start", headers=h).status_code == 200
    dev = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "AA:BB:CC:DD:EE:01", "device_type": "c6", "device_name": "gw"})
    assert dev.status_code == 200, dev.text
    return {"h": h, "poll": poll.json()["id"], "quiz": qid, "dev": dev.json()["device_id"]}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_vote_and_answer_require_device_key(client, live, headers):
    body = {"device_id": live["dev"], "selected_option": 0}
    assert client.post(f"/api/polls/{live['poll']}/vote", headers=headers, json=body).status_code in (401, 403, 422)
    assert client.post(f"/api/quizzes/{live['quiz']}/answer", headers=headers, json=body).status_code in (401, 403, 422)


def test_ballot_stuffing_by_incrementing_device_id_blocked(client, live):
    codes = [client.post(f"/api/polls/{live['poll']}/vote", headers=DEVICE,
                         json={"device_id": i, "selected_option": 1}).status_code for i in range(1, 51)]
    assert codes.count(200) == 1          # only the one registered device
    assert set(codes) == {200, 404}


def test_duplicate_vote_and_answer_rejected(client, live):
    body = {"device_id": live["dev"], "selected_option": 1}
    assert client.post(f"/api/polls/{live['poll']}/vote", headers=DEVICE, json=body).status_code == 200
    assert client.post(f"/api/polls/{live['poll']}/vote", headers=DEVICE, json=body).status_code == 400
    assert client.post(f"/api/quizzes/{live['quiz']}/answer", headers=DEVICE, json=body).status_code == 200
    assert client.post(f"/api/quizzes/{live['quiz']}/answer", headers=DEVICE, json=body).status_code == 400


def test_option_out_of_range_rejected(client, live):
    bad_poll = client.post(f"/api/polls/{live['poll']}/vote", headers=DEVICE,
                           json={"device_id": live["dev"], "selected_option": 3})   # 3 options
    assert bad_poll.status_code == 422
    # Question 2 has only 2 options: option 2 is valid on q1 but not on q2.
    assert client.post(f"/api/quizzes/{live['quiz']}/next", headers=live["h"]).status_code == 200
    bad_ans = client.post(f"/api/quizzes/{live['quiz']}/answer", headers=DEVICE,
                          json={"device_id": live["dev"], "selected_option": 2})
    assert bad_ans.status_code == 422
    ok = client.post(f"/api/quizzes/{live['quiz']}/answer", headers=DEVICE,
                     json={"device_id": live["dev"], "selected_option": 1})
    assert ok.status_code == 200
