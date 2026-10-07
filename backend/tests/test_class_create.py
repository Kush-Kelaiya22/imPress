"""#15: POST /api/classes/ works (it 500'd on every call)."""

from datetime import date

from sqlalchemy import select

from conftest import auth, login


def _stored(db, cid):
    from app.models import ClassSession

    async def q(s):
        return (await s.execute(select(ClassSession).where(ClassSession.id == cid))).scalar_one()
    return db(q)


def test_create_class_without_exam_dates(client, db):
    r = client.post("/api/classes/", headers=auth(login(client)), json={"name": "Physics", "code": "PHY101"})
    assert r.status_code == 201, r.text
    cls = _stored(db, r.json()["id"])
    assert (cls.name, cls.code, cls.exam_start_date, cls.exam_end_date) == ("Physics", "PHY101", None, None)


def test_create_class_with_exam_dates_persists_them(client, db):
    r = client.post("/api/classes/", headers=auth(login(client)), json={
        "name": "Maths", "code": "MTH201",
        "exam_start_date": "2026-11-20", "exam_end_date": "2026-11-28"})
    assert r.status_code == 201, r.text
    cls = _stored(db, r.json()["id"])
    assert cls.exam_start_date == date(2026, 11, 20) and cls.exam_end_date == date(2026, 11, 28)


def test_invalid_exam_date_is_422_not_500(client):
    r = client.post("/api/classes/", headers=auth(login(client)), json={
        "name": "Bad", "code": "BAD1", "exam_start_date": "not-a-date"})
    assert r.status_code == 422


def test_admin_route_unaffected(client):
    r = client.post("/api/admin/classes", headers=auth(login(client)), json={"name": "Bio", "code": "BIO9"})
    assert r.status_code == 201, r.text
