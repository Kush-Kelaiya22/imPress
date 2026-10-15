"""v2.2 data for the redesigned pages: users' last activity and live
session, per-student attendance and participation, the quizzes-and-polls
overview."""

from conftest import DEVICE, auth, login, make_class, make_student, make_user


def test_users_list_shows_activity_classes_and_sign_in(client):
    h = auth(login(client))
    uid, _ = make_user(client, h, "prof9")
    make_class(client, h, teacher_ids=[uid])
    rows = {u["username"]: u for u in client.get("/api/admin/users", headers=h).json()}
    assert rows["impress.default.superAdmin"]["signed_in"] is True and rows["impress.default.superAdmin"]["last_active_at"]
    assert rows["prof9"]["class_count"] == 1


def test_students_summary_counts_attendance_and_participation(client):
    h = auth(login(client))
    cid = make_class(client, h, activate=True)
    sid = make_student(client, h, roll="ROLL000001")
    client.post(f"/api/admin/classes/{cid}/enroll", headers=h, json={"student_id": sid})
    quiz = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "a", "options": ["x", "y"], "correct_option": 0},
        {"question_text": "b", "options": ["x", "y"], "correct_option": 0}]}).json()["id"]
    client.post(f"/api/quizzes/{quiz}/start", headers=h)
    client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "quiz_answer", "quiz_id": quiz, "question_order": 0, "enrollment_number": "ROLL000001", "selected_option": 0}]})
    client.post(f"/api/quizzes/{quiz}/stop", headers=h)
    row = next(r for r in client.get("/api/admin/students/summary", headers=h).json() if r["id"] == sid)
    assert row["classes"] and row["participation_pct"] == 50 and row["attendance_pct"] is None


def test_overview_lists_quizzes_and_polls_of_accessible_classes(client):
    h = auth(login(client))
    _, th = make_user(client, h, "prof8")
    mine = make_class(client, h, name="Mine", code="MINE1", teacher_ids=[_uid(client, h, "prof8")])
    other = make_class(client, h, name="Other", code="OTH1")
    for cid in (mine, other):
        client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": f"Q{cid}", "questions": [
            {"question_text": "a", "options": ["x", "y"], "correct_option": 0}]})
        client.post("/api/polls/", headers=h, json={"class_session_id": cid, "title": f"P{cid}", "options": ["1", "2"],
                                                    "poll_mode": "planned"})
    teacher = client.get("/api/quizzes/overview", headers=th).json()
    assert [q["class_code"] for q in teacher["quizzes"]] == ["MINE1"] and [p["class_code"] for p in teacher["polls"]] == ["MINE1"]
    assert len(client.get("/api/quizzes/overview", headers=h).json()["quizzes"]) == 2


def _uid(client, h, name):
    return next(u["id"] for u in client.get("/api/admin/users", headers=h).json() if u["username"] == name)
