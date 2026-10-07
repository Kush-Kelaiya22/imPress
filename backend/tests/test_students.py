"""Student registry (routers/students.py) and class enrollment (admin enroll routes).

The enrollment number (roll_number) is the student's identity everywhere —
the student firmware sends it over the mesh — so its format rules are core.
"""

import pytest

from conftest import auth, login, make_class, make_student, make_user


@pytest.fixture
def su(client):
    return auth(login(client))


@pytest.mark.parametrize("roll", ["ABC", "ABCDE123456", "ABCDE-1234", "ABCDE 1234", ""])
def test_enrollment_number_must_be_10_alphanumerics(client, su, roll):
    r = client.post("/api/students/", headers=su, json={"roll_number": roll, "student_name": "X"})
    assert r.status_code == 422


def test_enrollment_number_is_normalised_to_upper_case(client, su):
    sid = make_student(client, su, roll="  abcde12345 ")
    assert client.get(f"/api/students/{sid}", headers=su).json()["roll_number"] == "ABCDE12345"


def test_duplicate_enrollment_number_rejected(client, su):
    make_student(client, su, roll="ABCDE12345")
    r = client.post("/api/students/", headers=su, json={"roll_number": "abcde12345", "student_name": "Y"})
    assert r.status_code == 400


def test_list_search_and_update(client, su):
    make_student(client, su, roll="AAAAA00001", name="Asha Rao")
    sid = make_student(client, su, roll="BBBBB00002", name="Bilal Khan")
    hits = client.get("/api/students/", headers=su, params={"search": "bilal"}).json()
    assert [s["roll_number"] for s in hits] == ["BBBBB00002"]
    upd = client.put(f"/api/students/{sid}", headers=su, json={"program": "B.Tech CS", "phone": "98765 43210"})
    assert upd.status_code == 200 and upd.json()["program"] == "B.Tech CS"
    assert client.put("/api/students/999", headers=su, json={"program": "x"}).status_code == 404


def test_soft_delete_keeps_record(client, su):
    sid = make_student(client, su)
    assert client.delete(f"/api/students/{sid}", headers=su).status_code == 200
    assert client.get(f"/api/students/{sid}", headers=su).json()["is_active"] is False


def test_hard_delete_is_admin_only(client, su):
    _, teacher = make_user(client, su, "tch1")
    sid = make_student(client, su)
    assert client.delete(f"/api/students/{sid}/hard-delete", headers=teacher).status_code == 403
    assert client.delete(f"/api/students/{sid}/hard-delete", headers=su).status_code == 200
    assert client.get(f"/api/students/{sid}", headers=su).status_code == 404


def test_enroll_into_class_and_list_classes(client, su):
    cid = make_class(client, su, "Bio", "BIO1")
    sid = make_student(client, su)
    assert client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": sid}).status_code == 200
    classes = client.get(f"/api/students/{sid}/classes", headers=su).json()
    assert [c["class_id"] for c in classes] == [cid]
    assert client.get(f"/api/classes/{cid}", headers=su).json()["student_count"] == 1
    roster = client.get(f"/api/admin/students/class/{cid}", headers=su).json()
    assert [s["id"] for s in roster] == [sid]


def test_unenroll_removes_from_roster(client, su):
    cid = make_class(client, su, "Bio", "BIO1")
    sid = make_student(client, su)
    client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": sid})
    assert client.delete(f"/api/admin/classes/{cid}/unenroll/{sid}", headers=su).status_code == 200
    assert client.get(f"/api/classes/{cid}", headers=su).json()["student_count"] == 0


# ── CSV import ──────────────────────────────────────────────────────────────

CSV_HEADER = "roll_number,student_name,email,phone,program,enrollment_year,graduation_year\n"


def _csv(client, h, rows, name="students.csv"):
    return client.post("/api/students/import", headers=h,
                       files={"file": (name, (CSV_HEADER + rows).encode(), "text/csv")})


def test_csv_import_mixed_rows(client, su):
    make_student(client, su, roll="EXIST00001")
    r = _csv(client, su,
             "GOODA00001,Good One,good1@x.io,+91 98765-43210,BTech,2024,2028\n"
             "bad,Too Short,b@x.io,9876543210,BTech,2024,2028\n"            # roll format
             "GOODA00001,Dup In File,d@x.io,9876543210,BTech,2024,2028\n"   # duplicate in CSV
             "EXIST00001,Already,e@x.io,9876543210,BTech,2024,2028\n"       # duplicate in DB
             "GOODA00002,Bad Mail,not-an-email,9876543210,BTech,2024,2028\n"
             "GOODA00003,Bad Years,y@x.io,9876543210,BTech,2028,2024\n"      # grad < enrol
             "GOODA00004,Old Year,o@x.io,9876543210,BTech,1999,2003\n")     # out of range
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["inserted"] == 1 and res["total_rows"] == 7
    errors = {e["row"]: e["error"] for e in res["skipped"]}
    assert len(errors) == 6
    assert any("10 alphanumeric" in e for e in errors.values())
    assert any("duplicate roll_number within CSV" in e for e in errors.values())
    assert any("already exists in database" in e for e in errors.values())
    assert any("email" in e for e in errors.values())
    assert any("graduation_year must be >= enrollment_year" in e for e in errors.values())
    assert any("between 2000 and 2099" in e for e in errors.values())


def test_csv_import_rejects_wrong_columns_and_non_csv(client, su):
    bad_cols = client.post("/api/students/import", headers=su,
                           files={"file": ("s.csv", b"roll_number,student_name\nA,B\n", "text/csv")})
    assert bad_cols.status_code == 400 and "missing" in bad_cols.json()["detail"]
    not_csv = client.post("/api/students/import", headers=su,
                          files={"file": ("s.xlsx", b"PK\x03\x04", "application/octet-stream")})
    assert not_csv.status_code == 400
