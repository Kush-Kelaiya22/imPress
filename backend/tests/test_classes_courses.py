"""Classes (routers/classes.py, admin class routes) and courses (routers/courses.py)."""

import pytest

from conftest import auth, login, make_class, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


# ── Courses ─────────────────────────────────────────────────────────────────

def test_course_crud_and_unique_code(client, su):
    r = client.post("/api/courses/", headers=su, json={"code": "CS101", "name": "Intro to CS", "credits": 4})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert client.post("/api/courses/", headers=su, json={"code": "CS101", "name": "Dup"}).status_code == 400
    assert client.get(f"/api/courses/{cid}", headers=su).json()["name"] == "Intro to CS"
    upd = client.put(f"/api/courses/{cid}", headers=su, json={"name": "Introduction to CS"})
    assert upd.status_code == 200 and upd.json()["name"] == "Introduction to CS"
    assert [c["code"] for c in client.get("/api/courses/", headers=su).json()] == ["CS101"]
    assert client.delete(f"/api/courses/{cid}", headers=su).status_code == 200
    assert client.get(f"/api/courses/{cid}", headers=su).status_code == 404


def test_course_update_cannot_steal_another_code(client, su):
    client.post("/api/courses/", headers=su, json={"code": "MA1", "name": "Maths"})
    other = client.post("/api/courses/", headers=su, json={"code": "PH1", "name": "Physics"}).json()["id"]
    assert client.put(f"/api/courses/{other}", headers=su, json={"code": "MA1"}).status_code == 400


def test_teachers_read_courses_but_only_admins_write(client, su):
    _, teacher = make_user(client, su, "tch1")
    client.post("/api/courses/", headers=su, json={"code": "CS1", "name": "CS"})
    assert client.get("/api/courses/", headers=teacher).status_code == 200
    assert client.post("/api/courses/", headers=teacher, json={"code": "X1", "name": "X"}).status_code == 403


# ── Classes: visibility and access ──────────────────────────────────────────

def test_teacher_sees_only_their_classes(client, su):
    t1, h1 = make_user(client, su, "tch1")
    t2, h2 = make_user(client, su, "tch2")
    make_class(client, su, "Bio", "BIO1", teacher_id=t1)
    make_class(client, su, "Chem", "CHEM1", teacher_id=t2)
    assert [c["code"] for c in client.get("/api/classes/", headers=h1).json()] == ["BIO1"]
    assert [c["code"] for c in client.get("/api/classes/", headers=h2).json()] == ["CHEM1"]
    assert len(client.get("/api/classes/", headers=su).json()) == 2


def test_other_teachers_class_is_forbidden(client, su):
    t1, _ = make_user(client, su, "tch1")
    _, h2 = make_user(client, su, "tch2")
    cid = make_class(client, su, "Bio", "BIO1", teacher_id=t1)
    for method, path in (("get", f"/api/classes/{cid}"), ("post", f"/api/classes/{cid}/activate"),
                         ("post", f"/api/classes/{cid}/deactivate"), ("get", f"/api/classes/{cid}/presence")):
        assert getattr(client, method)(path, headers=h2).status_code == 403, path
    assert client.delete(f"/api/classes/{cid}", headers=h2).status_code == 403


def test_activate_deactivate_toggle(client, su):
    cid = make_class(client, su)
    assert client.get(f"/api/classes/{cid}", headers=su).json()["is_active"] is False
    assert client.post(f"/api/classes/{cid}/activate", headers=su).json()["is_active"] is True
    assert client.post(f"/api/classes/{cid}/deactivate", headers=su).json()["is_active"] is False
    assert client.post("/api/classes/999/activate", headers=su).status_code == 404


def test_join_requires_known_active_code(client, su):
    _, teacher = make_user(client, su, "tch1")
    make_class(client, su, "Bio", "BIO1")
    assert client.post("/api/classes/join", headers=teacher, json={"code": "NOPE"}).status_code == 404
    assert client.post("/api/classes/join", headers=teacher, json={"code": "BIO1"}).status_code == 400


def test_class_codes_are_unique(client, su):
    make_class(client, su, "Bio", "BIO1")
    r = client.post("/api/admin/classes", headers=su, json={"name": "Bio again", "code": "BIO1"})
    assert r.status_code in (400, 409)


def test_primary_teacher_can_delete_own_class(client, su):
    t1, h1 = make_user(client, su, "tch1")
    cid = make_class(client, su, "Bio", "BIO1", teacher_id=t1)
    assert client.delete(f"/api/classes/{cid}", headers=h1).status_code == 200
    assert client.get(f"/api/classes/{cid}", headers=su).status_code == 404


def test_presence_snapshot_empty_without_gateway(client, su):
    cid = make_class(client, su)
    snap = client.get(f"/api/classes/{cid}/presence", headers=su).json()
    assert snap["class_id"] == cid and snap["devices"] == [] and snap["total_count"] == 0


# ── Schedule conflict warnings (non-blocking) ───────────────────────────────

def test_overlapping_schedule_for_same_teacher_warns_but_creates(client, su):
    t1, _ = make_user(client, su, "tch1")
    slot = [{"day": "Mon", "start": "09:00", "end": "10:00"}]
    make_class(client, su, "Bio", "BIO1", teacher_id=t1, meeting_schedule=slot, location="RM-1")
    r = client.post("/api/admin/classes", headers=su, json={
        "name": "Chem", "code": "CHEM1", "teacher_id": t1, "location": "RM-1",
        "meeting_schedule": [{"day": "Mon", "start": "09:30", "end": "10:30"}]})
    assert r.status_code == 201
    kinds = {w["type"] for w in r.json()["warnings"]}
    assert kinds == {"teacher", "room"}


def test_back_to_back_slots_do_not_warn(client, su):
    t1, _ = make_user(client, su, "tch1")
    make_class(client, su, "Bio", "BIO1", teacher_id=t1, meeting_schedule=[{"day": "Mon", "start": "09:00", "end": "10:00"}])
    r = client.post("/api/admin/classes", headers=su, json={
        "name": "Chem", "code": "CHEM1", "teacher_id": t1,
        "meeting_schedule": [{"day": "Mon", "start": "10:00", "end": "11:00"}]})
    assert r.json()["warnings"] == []
