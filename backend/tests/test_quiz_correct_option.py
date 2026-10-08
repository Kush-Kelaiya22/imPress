"""#22: correct_option must index one of the question's options."""

import pytest

from conftest import auth, login


@pytest.fixture
def ctx(client):
    h = auth(login(client))
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Bio", "code": "BIO1"}).json()["id"]
    return h, cid


def _create(client, ctx, options, correct):
    h, cid = ctx
    return client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q",
                       "questions": [{"question_text": "q", "options": options, "correct_option": correct}]})


@pytest.mark.parametrize("options,correct", [(["a", "b"], 2), (["a", "b"], 9), (["a", "b", "c", "d"], 4)])   # 4 = the most a module shows (#49)
def test_out_of_range_rejected(client, ctx, options, correct):
    r = _create(client, ctx, options, correct)
    assert r.status_code == 422 and "correct_option" in r.text


@pytest.mark.parametrize("options,correct", [(["a", "b"], 0), (["a", "b"], 1), (["a", "b", "c", "d"], 3)])
def test_boundaries_accepted(client, ctx, options, correct):
    assert _create(client, ctx, options, correct).status_code == 201


def test_negative_still_rejected(client, ctx):
    assert _create(client, ctx, ["a", "b"], -1).status_code == 422


def test_one_bad_question_rejects_whole_quiz(client, ctx):
    h, cid = ctx
    r = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "ok", "options": ["a", "b"], "correct_option": 1},
        {"question_text": "bad", "options": ["a", "b"], "correct_option": 3}]})
    assert r.status_code == 422
    assert client.get(f"/api/quizzes/class/{cid}", headers=h).json() == []      # nothing half-created
