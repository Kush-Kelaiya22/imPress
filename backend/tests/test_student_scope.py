"""Who may edit, deactivate and see the contact details of a student (the registry's scope)."""

from conftest import auth, login, make_class, make_student, make_user


def _setup(client):
    su = auth(login(client))
    a_id, a = make_user(client, su, "tchA")
    _, b = make_user(client, su, "tchB")
    return su, a_id, a, b


def test_a_teacher_edits_only_students_they_registered_or_teach(client):
    su, a_id, a, b = _setup(client)
    own = make_student(client, a, roll="OWNREG0001", name="Registered By A")        # registered_by = A
    admin_made = make_student(client, su, roll="ADMINMADE1", name="Made By Admin", email="admin.made@example.edu", phone="9999999999")
    cid = make_class(client, su, name="A's class", code="AC101", teacher_id=a_id)
    client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": admin_made})

    assert client.put(f"/api/students/{own}", headers=a, json={"program": "Physics"}).status_code == 200
    assert client.put(f"/api/students/{admin_made}", headers=a, json={"program": "Maths"}).status_code == 200   # enrolled in A's class
    for sid in (own, admin_made):
        r = client.put(f"/api/students/{sid}", headers=b, json={"program": "Hijack"})
        assert r.status_code == 403 and r.json()["detail"]["code"] == "STUDENT_OUT_OF_SCOPE", sid
        assert client.delete(f"/api/students/{sid}", headers=b).status_code == 403
    assert client.get(f"/api/students/{admin_made}", headers=su).json()["program"] == "Maths"      # B changed nothing
    assert client.put(f"/api/students/{admin_made}", headers=su, json={"program": "Chem"}).status_code == 200  # admin: anyone
    assert client.delete(f"/api/students/{own}", headers=a).status_code == 200                       # A may deactivate their own


def test_contact_details_are_for_the_students_own_faculty_and_admins(client):
    su, a_id, a, b = _setup(client)
    sid = make_student(client, su, roll="CONTACT001", name="Reachable", email="reach@example.edu", phone="8888888888")
    cid = make_class(client, su, name="A's class", code="AC102", teacher_id=a_id)
    client.post(f"/api/admin/classes/{cid}/enroll", headers=su, json={"student_id": sid})

    def seen(h, path):
        r = client.get(path, headers=h)
        assert r.status_code == 200
        body = r.json()
        return next(x for x in body if x["id"] == sid) if isinstance(body, list) else body
    for h in (su, a):
        for path in ("/api/students/", f"/api/students/{sid}"):
            assert seen(h, path)["email"] == "reach@example.edu" and seen(h, path)["phone"] == "8888888888"
    for path in ("/api/students/", f"/api/students/{sid}"):
        row = seen(b, path)
        assert row["student_name"] == "Reachable" and row["roll_number"] == "CONTACT001"       # B can still find them to enrol
        assert row["email"] == "" and row["phone"] == "" and row["device_mac"] is None
