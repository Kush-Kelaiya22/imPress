"""#32: import courses and their sections (class sessions) from CSV."""

import csv
import io

import pytest
from sqlalchemy import func, select

from conftest import auth, login, make_user

HEADER = "course_code,course_name,section,class_code,teacher_username\n"


def _csv(*rows, header=HEADER):
    return (header + "".join(r + "\n" for r in rows)).encode()


def _post(client, h, raw, mode="create", dry_run=True):
    return client.post(f"/api/admin/classes/import?mode={mode}&dry_run={str(dry_run).lower()}",
                       headers=h, files={"file": ("c.csv", raw, "text/csv")})


def _count(db, model, *where):
    async def q(s):
        return await s.scalar(select(func.count()).select_from(model).where(*where))
    return db(q)


@pytest.fixture
def admin(client):
    h = auth(login(client))
    make_user(client, h, "teacher1")
    make_user(client, h, "teacher2")
    return h


# ── Planning ────────────────────────────────────────────────────────────────

def test_template_is_valid_and_previews_two_courses(client, admin):
    t = client.get("/api/admin/classes/import-template.csv")
    assert t.status_code == 200 and t.headers["content-type"].startswith("text/csv")
    rep = _post(client, admin, t.content).json()
    assert (rep["create"], rep["invalid"], rep["new_courses"]) == (3, 0, 2)
    assert rep["rows"][0]["classroom_code"] == "RM-201" and rep["rows"][0]["term"] == "Monsoon"


def test_dry_run_is_the_default_and_stores_nothing(client, db, admin):
    from app.models import ClassSession, Course
    r = client.post("/api/admin/classes/import", headers=admin,
                    files={"file": ("c.csv", _csv("CS101,Intro,A,CS101-A,teacher1"), "text/csv")})
    assert r.status_code == 200 and r.json()["committed"] is False and r.json()["create"] == 1
    assert _count(db, Course) == 0 and _count(db, ClassSession) == 0


def test_create_courses_and_sections(client, db, admin):
    from app.models import ClassSession, Course, User
    raw = _csv("cs101,Intro to CS,A,CS101-A,teacher1", "CS101,Intro to CS,B,CS101-B,teacher2",
               "MA201,Linear Algebra,A,MA201-A,teacher1")
    rep = _post(client, admin, raw, dry_run=False).json()
    assert rep["committed"] and (rep["imported"], rep["new_courses"]) == (3, 2)
    assert _count(db, Course) == 2 and _count(db, ClassSession) == 3

    async def check(s):
        cls = (await s.execute(select(ClassSession).where(ClassSession.code == "CS101-B"))).scalar_one()
        course = await s.get(Course, cls.course_id)
        teacher = await s.get(User, cls.teacher_id)
        return course.code, cls.course_section, cls.name, teacher.username, cls.is_active
    assert db(check) == ("CS101", "B", "CS101 B", "teacher2", False)   # code upper-cased, created inactive
    listed = {c["code"]: c for c in client.get("/api/admin/classes", headers=admin).json()}
    assert [f["full_name"] for f in listed["CS101-B"]["faculty_names"]] == ["Teacher2"]   # shown as faculty


def test_brief_column_names_are_accepted(client, admin):
    raw = _csv("CS101,Introduction to CS,A,Section A,CS101-A,teacher1",
               header="classroom_code,classroom_name,section_code,section_name,class_code,teacher_username\n")
    rep = _post(client, admin, raw).json()
    row = rep["rows"][0]
    assert rep["invalid"] == 0
    assert (row["course_code"], row["course_name"], row["section"], row["class_name"]) == (
        "CS101", "Introduction to CS", "A", "Section A")
    assert row["classroom_code"] is None


def test_room_label_column_in_our_layout(client, admin):
    raw = _csv("CS101,Intro,A,CS101-A,teacher1,RM-201", header=HEADER.strip() + ",classroom_code\n")
    assert _post(client, admin, raw).json()["rows"][0]["classroom_code"] == "RM-201"


@pytest.mark.parametrize("row,needle", [
    (",Intro,A,C1,teacher1", "course_code is empty"),
    ("CS101,Intro,A,C1,nobody", "no active teacher"),
    ("CS101,Intro,A,C1,admin", "no active teacher"),                  # admins aren't teachers
    ("CS101,Intro,A," + "x" * 33 + ",teacher1", "class_code is longer than 32"),
    ("CS101," + "n" * 129 + ",A,C1,teacher1", "course_name is longer than 128"),
    ("CS101,Intro,ABCDEFGHIJKLMNOPQ,C1,teacher1", "section is longer than 16"),
])
def test_invalid_rows_are_explained(client, admin, row, needle):
    rep = _post(client, admin, _csv(row)).json()
    assert rep["invalid"] == 1 and any(needle in e for e in rep["rows"][0]["errors"]), rep["rows"][0]


@pytest.mark.parametrize("extra,needle", [
    ("Spring,,", "term 'Spring' must be one of"),
    (",1999,", "year '1999' must be a whole number from 2000"),
    (",,lots", "capacity 'lots' must be a whole number"),
])
def test_optional_field_validation(client, admin, extra, needle):
    raw = _csv("CS101,Intro,A,C1,teacher1," + extra, header=HEADER.strip() + ",term,year,capacity\n")
    rep = _post(client, admin, raw).json()
    assert any(needle in e for e in rep["rows"][0]["errors"]), rep["rows"][0]


def test_conflicts_within_the_file(client, admin):
    rep = _post(client, admin, _csv(
        "CS101,Intro,A,C1,teacher1",
        "CS101,Introduction,B,C2,teacher1",      # same course, different name
        "CS101,Intro,A,C3,teacher1",             # same section again
        "MA201,Maths,A,C1,teacher1",             # same class_code again
    )).json()
    errs = [" ".join(r["errors"]) for r in rep["rows"]]
    assert rep["invalid"] == 3
    assert "is called 'Intro' on line 2" in errs[1]
    assert "section A of CS101 is also on line 2" in errs[2]
    assert "class_code C1 is also on line 2" in errs[3]


def test_existing_records_are_never_silently_overwritten(client, db, admin):
    _post(client, admin, _csv("CS101,Intro,A,CS101-A,teacher1"), dry_run=False)
    rep = _post(client, admin, _csv(
        "CS101,Another name,B,CS101-B,teacher1",   # course exists with a different name
        "CS101,Intro,A,OTHER-CODE,teacher1",        # section exists under another code
        "MA201,Maths,A,CS101-A,teacher1",           # code belongs to another class
    )).json()
    errs = [" ".join(r["errors"]) for r in rep["rows"]]
    assert "already exists as 'Intro'" in errs[0]
    assert "section A of CS101 already exists with class_code CS101-A" in errs[1]
    assert "class_code CS101-A is already used by another class" in errs[2]


def test_create_mode_skips_existing_and_reimport_is_idempotent(client, db, admin):
    from app.models import ClassSession
    raw = _csv("CS101,Intro,A,CS101-A,teacher1", "CS101,Intro,B,CS101-B,teacher1")
    assert _post(client, admin, raw, dry_run=False).json()["imported"] == 2
    again = _post(client, admin, raw, dry_run=False).json()
    assert (again["imported"], again["duplicate"], again["committed"]) == (0, 2, True)
    assert _count(db, ClassSession) == 2


def test_update_mode_changes_only_listed_optional_fields(client, db, admin):
    from app.models import ClassSession, User
    hdr = HEADER.strip() + ",class_name,classroom_code,capacity\n"
    _post(client, admin, _csv("CS101,Intro,A,CS101-A,teacher1,Section A,RM-1,40", header=hdr), dry_run=False)
    plan = _post(client, admin, _csv("CS101,Intro,A,CS101-A,teacher2,,RM-2,", header=hdr), mode="update").json()
    row = plan["rows"][0]
    assert row["status"] == "update" and row["changes"] == ["classroom_code", "teacher_username"]
    assert _post(client, admin, _csv("CS101,Intro,A,CS101-A,teacher2,,RM-2,", header=hdr),
                 mode="update", dry_run=False).json()["imported"] == 1

    async def check(s):
        c = (await s.execute(select(ClassSession).where(ClassSession.code == "CS101-A"))).scalar_one()
        return c.name, c.classroom_code, c.capacity, (await s.get(User, c.teacher_id)).username
    assert db(check) == ("Section A", "RM-2", 40, "teacher2")   # blanks left the old values
    listed = {c["code"]: c for c in client.get("/api/admin/classes", headers=admin).json()}
    assert [f["full_name"] for f in listed["CS101-A"]["faculty_names"]] == ["Teacher2"]   # old primary replaced
    same = _post(client, admin, _csv("CS101,Intro,A,CS101-A,teacher2,,RM-2,", header=hdr), mode="update").json()
    assert same["rows"][0]["status"] == "unchanged" and same["update"] == 0


def test_any_invalid_row_means_nothing_is_imported(client, db, admin):
    from app.models import ClassSession, Course
    r = _post(client, admin, _csv("CS101,Intro,A,C1,teacher1", "MA201,Maths,A,C2,ghost"), dry_run=False)
    assert r.status_code == 422 and r.json()["detail"]["report"]["invalid"] == 1
    assert _count(db, Course) == 0 and _count(db, ClassSession) == 0


def test_database_failure_leaves_nothing_behind(client, db, admin, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app.models import ClassSession, Course
    from app.routers import admin as admin_router

    async def broken(session, detail, status=409):
        raise OperationalError("COMMIT", {}, Exception("disk I/O error"))
    monkeypatch.setattr(admin_router, "commit_or_conflict", broken)
    r = _post(client, admin, _csv("CS101,Intro,A,C1,teacher1"), dry_run=False)
    assert r.status_code == 503
    assert _count(db, Course) == 0 and _count(db, ClassSession) == 0


def test_room_label_must_stay_unique(client, admin):
    hdr = HEADER.strip() + ",classroom_code\n"
    _post(client, admin, _csv("CS101,Intro,A,C1,teacher1,RM-1", header=hdr), dry_run=False)
    rep = _post(client, admin, _csv("CS101,Intro,B,C2,teacher1,RM-1", "MA1,M,A,C3,teacher1,RM-9",
                                    "MA1,M,B,C4,teacher1,RM-9", header=hdr)).json()
    errs = [" ".join(r["errors"]) for r in rep["rows"]]
    assert "room RM-1 is already assigned to class C1" in errs[0] and "room RM-9 is also on line 3" in errs[2]


# ── Export ──────────────────────────────────────────────────────────────────

def test_export_round_trips_and_escapes_formulas(client, db, admin):
    hdr = HEADER.strip() + ",class_name,location\n"
    _post(client, admin, _csv('CS101,Intro,A,CS101-A,teacher1,"=HYPERLINK(""x"")",@risky', header=hdr), dry_run=False)
    h = admin
    client.post("/api/admin/classes", headers=h, json={"name": "No course", "code": "FREE1"})
    r = client.get("/api/admin/classes/export.csv", headers=h)
    assert r.status_code == 200 and r.headers["x-omitted-classes"] == "1"
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert [x["class_code"] for x in rows] == ["CS101-A"]
    assert rows[0]["class_name"].startswith("'=") and rows[0]["location"] == "'@risky"
    # the export is itself a valid import: re-importing changes nothing
    again = _post(client, h, r.content).json()
    assert again["invalid"] == 0 and again["duplicate"] == 1


# ── Access control ──────────────────────────────────────────────────────────

def test_admin_only(client, admin):
    raw = _csv("CS101,Intro,A,C1,teacher1")
    assert client.post("/api/admin/classes/import", files={"file": ("c.csv", raw, "text/csv")}).status_code == 401
    _, teacher = make_user(client, admin, "teach9")
    assert _post(client, teacher, raw).status_code == 403
    assert client.get("/api/admin/classes/export.csv", headers=teacher).status_code == 403
    assert client.get("/api/admin/classes/export.csv").status_code == 401
