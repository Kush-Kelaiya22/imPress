"""#21: co-faculty can run quizzes/polls for their class; outsiders still can't."""

import pytest

from conftest import auth, login

PW = "Passw0rd!x"
Q = [{"question_text": "q", "options": ["a", "b"], "correct_option": 0}]


def _teacher(client, su, name):
    r = client.post("/api/admin/users", headers=su, json={
        "username": name, "email": f"{name}@x.io", "password": PW, "full_name": name, "role": "teacher"})
    return r.json()["id"], auth(login(client, name, PW))


@pytest.fixture
def env(client):
    su = auth(login(client))
    owner, ho = _teacher(client, su, "owner")
    co, hc = _teacher(client, su, "cofac")
    _, hx = _teacher(client, su, "outsider")
    cid = client.post("/api/admin/classes", headers=su,
                      json={"name": "Bio", "code": "BIO1", "teacher_ids": [owner, co]}).json()["id"]
    return {"cid": cid, "owner": ho, "co": hc, "out": hx, "su": su}


def test_cofaculty_runs_quiz_end_to_end(client, env):
    r = client.post("/api/quizzes/", headers=env["co"], json={"class_session_id": env["cid"], "title": "Q", "questions": Q})
    assert r.status_code == 201
    qid = r.json()["id"]
    for action in ("start", "next"):
        assert client.post(f"/api/quizzes/{qid}/{action}", headers=env["co"]).status_code == 200
    assert client.get(f"/api/quizzes/class/{env['cid']}", headers=env["co"]).status_code == 200


def test_cofaculty_runs_poll(client, env):
    r = client.post("/api/polls/", headers=env["co"], json={
        "class_session_id": env["cid"], "title": "P", "options": ["a", "b"], "poll_mode": "planned"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert client.post(f"/api/polls/{pid}/start", headers=env["co"]).status_code == 200
    assert client.post(f"/api/polls/{pid}/end", headers=env["co"]).status_code == 200
    assert client.get(f"/api/polls/class/{env['cid']}", headers=env["co"]).status_code == 200


def test_outsider_still_forbidden_and_owner_and_admin_allowed(client, env):
    body = {"class_session_id": env["cid"], "title": "Q", "questions": Q}
    assert client.post("/api/quizzes/", headers=env["out"], json=body).status_code == 403
    assert client.post("/api/polls/", headers=env["out"], json={
        "class_session_id": env["cid"], "title": "P", "options": ["a", "b"]}).status_code == 403
    assert client.post("/api/quizzes/", headers=env["owner"], json=body).status_code == 201
    assert client.post("/api/quizzes/", headers=env["su"], json=body).status_code == 201
