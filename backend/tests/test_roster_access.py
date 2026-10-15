"""Co-faculty manage a class roster like the primary teacher (#146)."""

import pytest

from conftest import auth, login, make_class, make_student, make_user


@pytest.fixture
def setup(client):
    su = auth(login(client))
    owner, owner_h = make_user(client, su, "owner1")
    co, co_h = make_user(client, su, "cofac1")
    _, other_h = make_user(client, su, "other1")
    cid = make_class(client, su, teacher_ids=[owner, co])
    sid = make_student(client, owner_h, roll="ROLL000001")
    return client, {"owner": owner_h, "co": co_h, "other": other_h}, cid, sid


@pytest.mark.parametrize("who,allowed", [("owner", True), ("co", True), ("other", False)])
def test_enrol_list_and_remove(setup, who, allowed):
    client, h, cid, sid = setup
    enrol = client.post(f"/api/admin/classes/{cid}/enroll", headers=h[who], json={"student_id": sid})
    listing = client.get(f"/api/admin/students/class/{cid}", headers=h[who])
    remove = client.delete(f"/api/admin/classes/{cid}/unenroll/{sid}", headers=h[who])
    if allowed:
        assert enrol.status_code == 200 and listing.status_code == 200 and remove.status_code == 200
    else:
        assert {enrol.status_code, listing.status_code, remove.status_code} == {403}


def test_co_faculty_see_participation_of_their_class(setup, db):
    from sqlalchemy import text
    client, h, cid, sid = setup
    client.post(f"/api/admin/classes/{cid}/enroll", headers=h["owner"], json={"student_id": sid})
    qid = client.post("/api/quizzes/", headers=h["owner"], json={
        "class_session_id": cid, "title": "Q", "questions": [
            {"question_text": "2+2?", "options": ["3", "4"], "correct_option": 1}]}).json()["id"]

    async def answer(s):
        await s.execute(text("INSERT INTO quiz_answers (quiz_id, question_order, student_id, selected_option, "
                             "response_time_ms, submitted_at) VALUES (:q, 0, :s, 1, 900, CURRENT_TIMESTAMP)"),
                        {"q": qid, "s": sid})
    db(answer)
    co = client.get(f"/api/admin/students/{sid}/participation", headers=h["co"]).json()
    other = client.get(f"/api/admin/students/{sid}/participation", headers=h["other"]).json()
    assert co["total_quiz_answers"] == 1 and other["total_quiz_answers"] == 0
