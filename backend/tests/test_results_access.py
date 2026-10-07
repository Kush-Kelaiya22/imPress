"""#20: quiz/poll details and results follow the class access rule."""

import pytest

from conftest import auth, login

PW = "Passw0rd!x"


def _teacher(client, su, name):
    r = client.post("/api/admin/users", headers=su, json={
        "username": name, "email": f"{name}@x.io", "password": PW, "full_name": name, "role": "teacher"})
    return r.json()["id"], auth(login(client, name, PW))


@pytest.fixture
def env(client):
    su = auth(login(client))
    owner, ho = _teacher(client, su, "owner")
    _, hx = _teacher(client, su, "outsider")
    cid = client.post("/api/admin/classes", headers=su, json={"name": "Bio", "code": "BIO1", "teacher_id": owner}).json()["id"]
    qid = client.post("/api/quizzes/", headers=ho, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q", "options": ["a", "b"], "correct_option": 1}]}).json()["id"]
    pid = client.post("/api/polls/", headers=ho, json={
        "class_session_id": cid, "title": "P", "options": ["a", "b"]}).json()["id"]
    paths = [f"/api/quizzes/{qid}", f"/api/quizzes/{qid}/results", f"/api/polls/{pid}", f"/api/polls/{pid}/results"]
    return {"su": su, "owner": ho, "out": hx, "paths": paths}


def test_outsider_cannot_read_details_or_results(client, env):
    for path in env["paths"]:
        assert client.get(path, headers=env["out"]).status_code == 403, path


def test_owner_and_admin_can_read(client, env):
    for who in ("owner", "su"):
        for path in env["paths"]:
            assert client.get(path, headers=env[who]).status_code == 200, (who, path)


def test_unknown_ids_still_404_and_anonymous_401(client, env):
    assert client.get("/api/quizzes/999/results", headers=env["owner"]).status_code == 404
    assert client.get("/api/polls/999", headers=env["owner"]).status_code == 404
    assert client.get(env["paths"][1]).status_code == 401
