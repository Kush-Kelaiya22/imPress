"""#49: the API only accepts what a student module can show and answer.

Student modules have four answer buttons, and questions travel in fixed-size
frame fields (firmware/protocol/protocol.h). Options beyond the fourth were
silently dropped on the device, which made such questions unanswerable.
"""

import re
from pathlib import Path

import pytest

from conftest import DEVICE, auth, login

PROTOCOL_H = Path(__file__).resolve().parents[2] / "firmware/protocol/protocol.h"


def _quiz(client, h, cid, options, text="2+2?", correct=0):
    return client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": text, "options": options, "correct_option": correct}]})


@pytest.fixture
def cls(client):
    h = auth(login(client))
    return h, client.post("/api/admin/classes", headers=h, json={"name": "Phys", "code": "PHY1"}).json()["id"]


def test_backend_limits_match_the_firmware_frame():
    from app.schemas import DEVICE_MAX_OPTIONS, DEVICE_TEXT_BYTES
    h = PROTOCOL_H.read_text()
    q = h[h.index("} payload_quiz_question_t") - 400:h.index("} payload_quiz_question_t")]
    assert int(re.search(r"question_text\[(\d+)\]", q).group(1)) - 1 == DEVICE_TEXT_BYTES["question"]
    n, size = map(int, re.search(r"options\[(\d+)\]\[(\d+)\]", q).groups())
    assert n == DEVICE_MAX_OPTIONS and size - 1 == DEVICE_TEXT_BYTES["option"]
    p = h[h.index("} payload_poll_start_t") - 300:h.index("} payload_poll_start_t")]
    assert int(re.search(r"title\[(\d+)\]", p).group(1)) - 1 == DEVICE_TEXT_BYTES["poll_title"]


@pytest.mark.parametrize("n,status", [(2, 201), (4, 201), (5, 422), (6, 422)])
def test_quiz_options_limited_to_the_four_buttons(client, cls, n, status):
    h, cid = cls
    r = _quiz(client, h, cid, [f"o{i}" for i in range(n)], correct=n - 1)
    assert r.status_code == status, r.text


@pytest.mark.parametrize("n,status", [(4, 201), (5, 422)])
def test_poll_options_limited_to_the_four_buttons(client, cls, n, status):
    h, cid = cls
    r = client.post("/api/polls/", headers=h, json={
        "class_session_id": cid, "title": "T", "options": [f"o{i}" for i in range(n)], "poll_mode": "planned"})
    assert r.status_code == status, r.text


def test_long_text_is_accepted_with_truncation_warnings(client, cls):
    h, cid = cls
    r = _quiz(client, h, cid, ["fits", "this option is far too long for the display"], text="Q" * 150)
    assert r.status_code == 201
    w = r.json()["warnings"]
    assert any("Question 1 is 150 bytes" in x for x in w) and any("option B" in x for x in w)
    assert len(w) == 2

    # bytes, not characters: 12 Devanagari letters = 36 bytes > 14
    r = _quiz(client, h, cid, ["क" * 12, "ok"])
    assert any("option A is 36 bytes" in x for x in r.json()["warnings"])

    poll = client.post("/api/polls/", headers=h, json={
        "class_session_id": cid, "title": "T" * 70, "options": ["a", "b"], "poll_mode": "planned"})
    assert poll.status_code == 201 and poll.json()["warnings"] == ["Poll title is 70 bytes; student modules show the first 63"]
    assert _quiz(client, h, cid, ["a", "b"]).json()["warnings"] == []


def test_answer_and_vote_options_beyond_d_rejected(client, cls):
    h, cid = cls
    for path, oid in (("polls", "poll"), ("quizzes", "quiz")):
        r = client.post(f"/api/{path}/1/{'vote' if oid == 'poll' else 'answer'}", headers=DEVICE,
                        json={"device_id": 1, "selected_option": 4})
        assert r.status_code == 422
