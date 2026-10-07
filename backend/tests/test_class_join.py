"""#19: joining a class by code must never take over the primary-teacher role."""

from conftest import auth, login

PW = "Passw0rd!x"


def _teacher(client, su, name):
    r = client.post("/api/admin/users", headers=su, json={
        "username": name, "email": f"{name}@x.io", "password": PW, "full_name": name, "role": "teacher"})
    assert r.status_code == 201, r.text
    return r.json()["id"], auth(login(client, name, PW))


def _class(client, su, owner_id):
    r = client.post("/api/admin/classes", headers=su, json={"name": "Bio", "code": "BIO1", "teacher_id": owner_id})
    cid = r.json()["id"]
    assert client.post(f"/api/classes/{cid}/activate", headers=su).status_code == 200
    return cid


def test_join_adds_co_faculty_and_keeps_owner(client):
    su = auth(login(client))
    owner, _ = _teacher(client, su, "owner")
    joiner, hj = _teacher(client, su, "joiner")
    cid = _class(client, su, owner)
    r = client.post("/api/classes/join", headers=hj, json={"code": "BIO1"})
    assert r.status_code == 200
    body = client.get(f"/api/classes/{cid}", headers=su).json()
    assert body["teacher_id"] == owner                       # ownership unchanged
    assert set(body["teacher_ids"]) == {owner, joiner}       # joiner is co-faculty
    assert client.get(f"/api/classes/{cid}", headers=hj).status_code == 200


def test_join_is_idempotent_and_owner_join_is_noop(client):
    su = auth(login(client))
    owner, ho = _teacher(client, su, "owner")
    joiner, hj = _teacher(client, su, "joiner")
    cid = _class(client, su, owner)
    for _ in range(2):
        client.post("/api/classes/join", headers=hj, json={"code": "BIO1"})
    client.post("/api/classes/join", headers=ho, json={"code": "BIO1"})
    body = client.get(f"/api/classes/{cid}", headers=su).json()
    assert body["teacher_id"] == owner and sorted(body["teacher_ids"]) == sorted([owner, joiner])
    assert len(body["faculty_names"]) == len(set(f["id"] for f in body["faculty_names"]))


def test_co_faculty_cannot_delete_class(client):
    su = auth(login(client))
    owner, _ = _teacher(client, su, "owner")
    _, hj = _teacher(client, su, "joiner")
    cid = _class(client, su, owner)
    client.post("/api/classes/join", headers=hj, json={"code": "BIO1"})
    assert client.delete(f"/api/classes/{cid}", headers=hj).status_code == 403   # primary-only action


def test_join_errors(client):
    su = auth(login(client))
    _, hj = _teacher(client, su, "joiner")
    assert client.post("/api/classes/join", headers=hj, json={"code": "NOPE"}).status_code == 404
    client.post("/api/admin/classes", headers=su, json={"name": "X", "code": "OFF1"})
    assert client.post("/api/classes/join", headers=hj, json={"code": "OFF1"}).status_code == 400
