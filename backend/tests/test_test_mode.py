"""v2.2 debug (test) mode: the real data is set aside, test data is generated
or imported on a copy, and the real data comes back untouched."""

import io
import zipfile

from conftest import auth, login, make_student, make_user


def _super(client):
    return auth(login(client))


def test_test_data_routes_need_debug_mode(client):
    h = _super(client)
    r = client.post("/api/admin/test-data/generate", headers=h, json={"seed": 1})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "TEST_MODE_OFF"


def test_only_a_super_admin_turns_it_on(client):
    h = _super(client)
    _, th = make_user(client, h, "tch5")
    assert client.post("/api/admin/test-mode/enable", headers=th, json={}).status_code == 403


def test_round_trip_keeps_the_real_data_and_offers_the_test_data(client):
    h = _super(client)
    make_student(client, h, roll="REAL000001", name="Real Student")
    st = client.post("/api/admin/test-mode/enable", headers=h, json={}).json()
    assert st["on"] is True
    assert client.get("/api/system/status").json()["test_mode"] is True

    gen = client.post("/api/admin/test-data/generate", headers=h,
                      json={"seed": 42, "counts": {"teachers": 4, "courses": 4, "students": 30, "classes": 4}}).json()
    sheets = gen["sheets"]
    assert len(sheets["students"]) == 30 and sheets["enrollments"]
    v = client.post("/api/admin/test-data/validate", headers=h, json={"sheets": sheets}).json()
    assert v["ok"], v["errors"][:3]
    rep = client.post("/api/admin/test-data/import", headers=h, json={"sheets": sheets, "seed": 42}).json()
    assert rep["imported"]["students"] == 30 and rep["activity"]["answers"] > 0
    assert len(client.get("/api/students/", headers=h).json()) == 31

    off = client.post("/api/admin/test-mode/disable", headers=h).json()       # the super admin stays signed in
    assert off["on"] is False and off["pending_id"]
    rolls = [s["roll_number"] for s in client.get("/api/students/", headers=h).json()]
    assert rolls == ["REAL000001"]                                               # test data gone from the real DB
    from app.services.integrity import verify_now
    assert client.portal.call(verify_now).ok

    z = client.get(f"/api/admin/test-mode/pending/{off['pending_id']}/export.zip", headers=h)
    names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert "students.csv" in names and "classes.csv" in names
    saved = client.post(f"/api/admin/test-mode/pending/{off['pending_id']}", headers=h,
                        json={"action": "save", "name": "Term demo"}).json()
    assert saved["counts"]["students"] == 31

    back = client.post("/api/admin/test-mode/enable", headers=h, json={"dataset": "Term demo"}).json()
    assert back["on"] is True
    assert len(client.get("/api/students/", headers=h).json()) == 31                 # the saved test data again
    client.post("/api/admin/test-mode/disable", headers=h)
    assert len(client.get("/api/students/", headers=h).json()) == 1


def test_invalid_rows_are_reported_and_nothing_is_imported(client):
    h = _super(client)
    client.post("/api/admin/test-mode/enable", headers=h, json={})
    sheets = {"students": [{"roll_number": "SHORT", "student_name": ""}],
              "enrollments": [{"roll_number": "NOPE000001", "class_code": "NOCLASS"}]}
    r = client.post("/api/admin/test-data/import", headers=h, json={"sheets": sheets})
    assert r.status_code == 422
    errs = {(e["sheet"], e["column"]) for e in r.json()["detail"]["errors"]}
    assert {("students", "roll_number"), ("students", "student_name"), ("enrollments", "class_code")} <= errs
    assert client.get("/api/students/", headers=h).json() == []
    client.post("/api/admin/test-mode/disable", headers=h)


def test_generated_data_is_unique_consistent_and_repeatable():
    from app.services.dummy_data import generate
    a, b, c = generate(5), generate(5), generate(6)
    assert a == b and a != c
    rolls = [s["roll_number"] for s in a["students"]]
    assert len(rolls) == len(set(rolls))
    codes = {cl["code"] for cl in a["classes"]}
    assert all(e["class_code"] in codes for e in a["enrollments"])
    rooms = [cl["classroom_code"] for cl in a["classes"]]
    assert len(rooms) == len(set(rooms))
    slots = {}
    for cl in a["classes"]:                                   # no teacher teaches two classes at once
        for d in cl["days"].split(","):
            key = (cl["teacher_username"], d, cl["start"])
            assert key not in slots, key
            slots[key] = cl["code"]


def test_generated_teachers_get_a_password_that_is_random_per_session(client):
    h = _super(client)
    client.post("/api/admin/test-mode/enable", headers=h, json={})
    pw1 = client.get("/api/admin/test-mode", headers=h).json()["test_password"]
    assert pw1 and pw1 != "TestMode-Pass-2026" and len(pw1) >= 10
    sheets = client.post("/api/admin/test-data/generate", headers=h, json={"seed": 3, "counts": {"teachers": 1, "students": 4, "classes": 1, "courses": 1}}).json()["sheets"]
    assert client.post("/api/admin/test-data/import", headers=h, json={"sheets": sheets, "simulate_activity": False}).status_code == 200
    teacher = sheets["teachers"][0]["username"]
    assert client.post("/api/auth/login", json={"username": teacher, "password": pw1}).status_code == 200
    client.post("/api/admin/test-mode/disable", headers=h)
    assert client.get("/api/admin/test-mode", headers=h).json()["test_password"] is None
    client.post("/api/admin/test-mode/enable", headers=h, json={})
    assert client.get("/api/admin/test-mode", headers=h).json()["test_password"] != pw1
