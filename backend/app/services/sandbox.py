"""Test-mode data sheets (v2.2): validate and import rows, simulate activity.

The super admin's *Test data* page shows one spreadsheet tab per sheet below.
Rows come from typing, pasting (from Google Sheets or Excel), a CSV file, or
the generator (services/dummy_data.py). Import is all-or-nothing and runs
through the database gateway as the signed-in super admin.

Order matters and is enforced: teachers and courses before classes,
students and classes before enrollments, classes before quizzes and polls.
A row may refer to something in the same import or already in the database.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (Attendance, ClassSession, Course, Poll, PollVote, Quiz, QuizAnswer, QuizQuestion, Student,
                      StudentEnrollment, User)
from ..schedule import WEEKDAYS
from ..schemas import SEMESTERS
from .dummy_data import TEST_PASSWORD, Taken

_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_ROLL = re.compile(r"^[A-Za-z0-9]{10}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USER = re.compile(r"^[a-z0-9._-]{3,32}$")
_CODE = re.compile(r"^[A-Za-z0-9._-]{2,32}$")
_DAY = {d[:3].lower(): d for d in WEEKDAYS}


def _col(name, label, required=False, kind="text", help=""):
    return {"name": name, "label": label, "required": required, "kind": kind, "help": help}


SHEETS = [
    {"name": "teachers", "label": "Teachers", "columns": [
        _col("username", "Username", True, help="3-32: a-z 0-9 . _ -"),
        _col("full_name", "Full name", True), _col("email", "E-mail", True, "email"),
        _col("department", "Department")]},
    {"name": "courses", "label": "Courses", "columns": [
        _col("code", "Code", True, help="e.g. CSE201"), _col("name", "Name", True),
        _col("credits", "Credits", kind="int"), _col("department", "Department"), _col("description", "Description")]},
    {"name": "students", "label": "Students", "columns": [
        _col("roll_number", "Enrollment no.", True, help="exactly 10 letters or digits"),
        _col("student_name", "Name", True), _col("email", "E-mail", kind="email"), _col("program", "Programme"),
        _col("enrollment_year", "Intake year", kind="int"), _col("graduation_year", "Graduation year", kind="int")]},
    {"name": "classes", "label": "Classes", "columns": [
        _col("code", "Class code", True), _col("name", "Name", True), _col("course_code", "Course code", kind="ref"),
        _col("section", "Section"), _col("term", "Term", help="Monsoon, Winter or Summer"),
        _col("year", "Year", kind="int"), _col("teacher_username", "Teacher", True, "ref"),
        _col("co_faculty", "Co-faculty", help="usernames, comma-separated"),
        _col("classroom_code", "Room code", help="unique per class"), _col("location", "Location"),
        _col("capacity", "Capacity", kind="int"), _col("days", "Days", help="e.g. Mon,Wed,Fri"),
        _col("start", "Start", kind="time"), _col("end", "End", kind="time"),
        _col("start_date", "From", kind="date"), _col("end_date", "To", kind="date")]},
    {"name": "enrollments", "label": "Enrolments", "columns": [
        _col("roll_number", "Enrollment no.", True, "ref"), _col("class_code", "Class code", True, "ref")]},
    {"name": "quizzes", "label": "Quiz questions", "columns": [
        _col("class_code", "Class code", True, "ref"), _col("title", "Quiz title", True),
        _col("status", "Status", help="draft or completed"), _col("question_text", "Question", True),
        _col("option_a", "A", True), _col("option_b", "B", True), _col("option_c", "C"), _col("option_d", "D"),
        _col("correct", "Correct", True, help="A, B, C or D")]},
    {"name": "polls", "label": "Polls", "columns": [
        _col("class_code", "Class code", True, "ref"), _col("title", "Question", True),
        _col("options", "Options", True, help="2-4, separated by |"), _col("status", "Status", help="draft or closed")]},
]
SHEET_NAMES = [s["name"] for s in SHEETS]
MAX_ROWS = 20000


def _s(v) -> str:
    return "" if v is None else str(v).strip()


async def taken_values(db: AsyncSession) -> Taken:
    users = (await db.execute(select(User.username, User.email, User.role))).all()
    stu = (await db.execute(select(Student.roll_number, Student.email))).all()
    classes = (await db.execute(select(ClassSession.code, ClassSession.classroom_code))).all()
    return Taken(
        usernames={u.lower() for u, _, _ in users}, emails={(e or "").lower() for _, e, _ in users} | {(e or "").lower() for _, e in stu},
        course_codes={c.lower() for (c,) in (await db.execute(select(Course.code))).all()},
        class_codes={c.lower() for c, _ in classes}, rooms={(r or "").lower() for _, r in classes if r},
        rolls={r.lower() for r, _ in stu}, teachers=[u for u, _, r in users if r == "teacher"])


def _days(text_: str) -> list[str] | None:
    out = []
    for part in re.split(r"[,\s/]+", text_.strip()):
        if not part:
            continue
        d = _DAY.get(part[:3].lower())
        if d is None:
            return None
        out.append(d)
    return out


async def validate(db: AsyncSession, sheets: dict) -> dict:
    """Every problem, as {sheet, row (1-based), column, message}."""
    errors: list[dict] = []
    t = await taken_values(db)
    existing_users = {u.lower() for u in t.usernames}
    new_users, new_courses, new_students, new_classes = set(), set(), set(), set()
    emails, rooms = set(t.emails), set(t.rooms)
    total = 0

    def err(sheet, row, col, msg):
        if len(errors) < 500:
            errors.append({"sheet": sheet, "row": row, "column": col, "message": msg})

    def rows(name):
        return [r for r in (sheets.get(name) or []) if any(_s(v) for v in (r or {}).values())]

    for name in SHEET_NAMES:
        total += len(rows(name))
    if total > MAX_ROWS:
        err("*", 0, "", f"too many rows ({total}); at most {MAX_ROWS} per import")
        return {"ok": False, "errors": errors}

    for spec in SHEETS:
        for i, r in enumerate(rows(spec["name"]), 1):
            for col in spec["columns"]:
                v = _s(r.get(col["name"]))
                if col["required"] and not v:
                    err(spec["name"], i, col["name"], f"{col['label']} is required")
                elif v and col["kind"] == "int" and not re.fullmatch(r"-?\d{1,6}", v):
                    err(spec["name"], i, col["name"], "must be a whole number")
                elif v and col["kind"] == "email" and not _EMAIL.match(v):
                    err(spec["name"], i, col["name"], "not an e-mail address")
                elif v and col["kind"] == "time" and not _HHMM.match(v):
                    err(spec["name"], i, col["name"], "use HH:MM, 24-hour")
                elif v and col["kind"] == "date":
                    try:
                        date.fromisoformat(v)
                    except ValueError:
                        err(spec["name"], i, col["name"], "use YYYY-MM-DD")

    for i, r in enumerate(rows("teachers"), 1):
        u, e = _s(r.get("username")).lower(), _s(r.get("email")).lower()
        if u and not _USER.match(u):
            err("teachers", i, "username", "3-32 characters: a-z, 0-9, . _ -")
        elif u in existing_users or u in new_users:
            err("teachers", i, "username", "already taken")
        new_users.add(u)
        if e and e in emails:
            err("teachers", i, "email", "already used")
        emails.add(e)
    for i, r in enumerate(rows("courses"), 1):
        c = _s(r.get("code")).lower()
        if c and not _CODE.match(c):
            err("courses", i, "code", "2-32 letters, digits, . _ -")
        elif c in t.course_codes or c in new_courses:
            err("courses", i, "code", "already exists")
        new_courses.add(c)
    for i, r in enumerate(rows("students"), 1):
        roll, e = _s(r.get("roll_number")).lower(), _s(r.get("email")).lower()
        if roll and not _ROLL.match(roll):
            err("students", i, "roll_number", "exactly 10 letters or digits")
        elif roll in t.rolls or roll in new_students:
            err("students", i, "roll_number", "already exists")
        new_students.add(roll)
        if e and e in emails:
            err("students", i, "email", "already used")
        if e:
            emails.add(e)
    staff = existing_users | new_users
    for i, r in enumerate(rows("classes"), 1):
        c = _s(r.get("code")).lower()
        if c in t.class_codes or c in new_classes:
            err("classes", i, "code", "already exists")
        new_classes.add(c)
        cc = _s(r.get("course_code")).lower()
        if cc and cc not in t.course_codes and cc not in new_courses:
            err("classes", i, "course_code", "no such course (add it on the Courses tab)")
        if _s(r.get("teacher_username")).lower() not in staff:
            err("classes", i, "teacher_username", "no such teacher (add them on the Teachers tab)")
        for co in filter(None, (x.strip().lower() for x in _s(r.get("co_faculty")).split(","))):
            if co not in staff:
                err("classes", i, "co_faculty", f"no such teacher: {co}")
        room = _s(r.get("classroom_code")).lower()
        if room:
            if room in rooms:
                err("classes", i, "classroom_code", "this room code belongs to another class")
            rooms.add(room)
        term = _s(r.get("term"))
        if term and term not in SEMESTERS:
            err("classes", i, "term", "Monsoon, Winter or Summer")
        days = _s(r.get("days"))
        if days and _days(days) is None:
            err("classes", i, "days", "day names, e.g. Mon,Wed,Fri")
        if bool(days) != bool(_s(r.get("start")) and _s(r.get("end"))):
            err("classes", i, "days", "days, start and end go together")
        elif days and _s(r.get("start")) >= _s(r.get("end")):
            err("classes", i, "end", "must be after the start")
    all_students = t.rolls | new_students
    all_classes = t.class_codes | new_classes
    pairs = set()
    for i, r in enumerate(rows("enrollments"), 1):
        roll, c = _s(r.get("roll_number")).lower(), _s(r.get("class_code")).lower()
        if roll and roll not in all_students:
            err("enrollments", i, "roll_number", "no such student (add them on the Students tab)")
        if c and c not in all_classes:
            err("enrollments", i, "class_code", "no such class (add it on the Classes tab)")
        if (roll, c) in pairs:
            err("enrollments", i, "roll_number", "enrolled twice in this class")
        pairs.add((roll, c))
    for i, r in enumerate(rows("quizzes"), 1):
        if _s(r.get("class_code")).lower() not in all_classes:
            err("quizzes", i, "class_code", "no such class")
        st = _s(r.get("status")).lower()
        if st and st not in ("draft", "completed"):
            err("quizzes", i, "status", "draft or completed")
        correct = _s(r.get("correct")).upper()
        if correct and (correct not in "ABCD" or len(correct) != 1 or not _s(r.get(f"option_{correct.lower()}"))):
            err("quizzes", i, "correct", "A, B, C or D, and that option must be filled in")
        if _s(r.get("option_d")) and not _s(r.get("option_c")):
            err("quizzes", i, "option_c", "fill C before D")
    for i, r in enumerate(rows("polls"), 1):
        if _s(r.get("class_code")).lower() not in all_classes:
            err("polls", i, "class_code", "no such class")
        opts = [o.strip() for o in _s(r.get("options")).split("|") if o.strip()]
        if not 2 <= len(opts) <= 4:
            err("polls", i, "options", "2 to 4 options, separated by |")
        st = _s(r.get("status")).lower()
        if st and st not in ("draft", "closed"):
            err("polls", i, "status", "draft or closed")
    return {"ok": not errors, "errors": errors, "counts": {n: len(rows(n)) for n in SHEET_NAMES}}


async def import_sheets(db: AsyncSession, sheets: dict, actor: User, simulate: bool, seed: int = 1) -> dict:
    """Validate, then insert everything in one transaction (caller commits)."""
    report = await validate(db, sheets)
    if not report["ok"]:
        return report
    from ..auth import hash_password

    def rows(name):
        return [{k: _s(v) for k, v in (r or {}).items()} for r in (sheets.get(name) or [])
                if any(_s(v) for v in (r or {}).values())]

    pw = hash_password(TEST_PASSWORD) if rows("teachers") else None     # one hash: same test password for all
    users = {u.username.lower(): u for u in (await db.execute(select(User))).scalars()}
    for r in rows("teachers"):
        u = User(username=r["username"].lower(), email=r["email"], full_name=r["full_name"], role="teacher",
                 hashed_password=pw)
        db.add(u)
        users[u.username] = u
    courses = {c.code.lower(): c for c in (await db.execute(select(Course))).scalars()}
    for r in rows("courses"):
        c = Course(code=r["code"], name=r["name"], credits=int(r.get("credits") or 0),
                   department=r.get("department", ""), description=r.get("description", ""))
        db.add(c)
        courses[c.code.lower()] = c
    students = {s.roll_number.lower(): s for s in (await db.execute(select(Student))).scalars()}
    for r in rows("students"):
        s = Student(roll_number=r["roll_number"].upper(), student_name=r["student_name"], email=r.get("email", ""),
                    program=r.get("program", ""), registered_by=actor.id,
                    enrollment_year=int(r["enrollment_year"]) if r.get("enrollment_year") else None,
                    graduation_year=int(r["graduation_year"]) if r.get("graduation_year") else None)
        db.add(s)
        students[s.roll_number.lower()] = s
    await db.flush()
    classes = {c.code.lower(): c for c in (await db.execute(select(ClassSession))).scalars()}
    for r in rows("classes"):
        days = _days(r.get("days", "")) or []
        teacher = users[r["teacher_username"].lower()]
        co = [users[x.strip().lower()] for x in r.get("co_faculty", "").split(",") if x.strip()]
        cl = ClassSession(
            name=r["name"], code=r["code"], teacher_id=teacher.id, created_by=actor.id,
            course_id=courses[r["course_code"].lower()].id if r.get("course_code") else None,
            course_section=r.get("section", ""), term=r.get("term", ""),
            year=int(r["year"]) if r.get("year") else None,
            start_date=date.fromisoformat(r["start_date"]) if r.get("start_date") else None,
            end_date=date.fromisoformat(r["end_date"]) if r.get("end_date") else None,
            meeting_schedule=[{"day": d, "start": r["start"], "end": r["end"]} for d in days],
            location=r.get("location", ""), capacity=int(r.get("capacity") or 0),
            classroom_code=r.get("classroom_code") or None)
        cl.faculty = [teacher] + [u for u in co if u is not teacher]
        db.add(cl)
        classes[cl.code.lower()] = cl
    await db.flush()
    enrol = {}
    for r in rows("enrollments"):
        e = StudentEnrollment(class_session_id=classes[r["class_code"].lower()].id,
                              student_id=students[r["roll_number"].lower()].id, enrolled_by=actor.id)
        db.add(e)
        enrol.setdefault(e.class_session_id, []).append(e)
    quizzes = defaultdict(list)
    for r in rows("quizzes"):
        quizzes[(r["class_code"].lower(), r["title"])].append(r)
    new_quizzes = []
    for (code, title), qrows in quizzes.items():
        status = "completed" if any(q.get("status", "").lower() == "completed" for q in qrows) else "draft"
        quiz = Quiz(class_session_id=classes[code].id, title=title, status=status)
        db.add(quiz)
        await db.flush()
        for n, q in enumerate(qrows):
            opts = [q[f"option_{k}"] for k in "abcd" if q.get(f"option_{k}")]
            db.add(QuizQuestion(quiz_id=quiz.id, order_num=n, question_text=q["question_text"], options=opts,
                                correct_option="ABCD".index(q["correct"].upper())))
        new_quizzes.append((quiz, qrows))
    new_polls = []
    for r in rows("polls"):
        p = Poll(class_session_id=classes[r["class_code"].lower()].id, title=r["title"],
                 options=[o.strip() for o in r["options"].split("|") if o.strip()],
                 status="closed" if r.get("status", "").lower() == "closed" else "draft")
        db.add(p)
        new_polls.append(p)
    await db.flush()
    activity = {"answers": 0, "votes": 0, "attendance": 0}
    if simulate:
        activity = await _simulate(db, new_quizzes, new_polls, classes, seed)
    report["imported"] = report.pop("counts")
    report["activity"] = activity
    return report


async def _simulate(db: AsyncSession, quizzes, polls, classes, seed: int) -> dict:
    """Past participation that looks like a real term: each student has an
    ability and a habit of turning up; completed quizzes get answers with
    plausible response times, closed polls get votes, and past class days
    get attendance."""
    rng = random.Random(seed * 7919 + 17)
    by_class = defaultdict(list)
    for e in (await db.execute(select(StudentEnrollment))).scalars():
        by_class[e.class_session_id].append(e)
    ability, habit = {}, {}
    out = {"answers": 0, "votes": 0, "attendance": 0}
    today = date.today()

    def past_day(cls):
        start = cls.start_date or (today - timedelta(days=30))
        span = max(1, (today - start).days)
        return start + timedelta(days=rng.randrange(span))

    for quiz, qrows in quizzes:
        if quiz.status != "completed":
            continue
        cls = next(c for c in classes.values() if c.id == quiz.class_session_id)
        day = past_day(cls)
        t0 = datetime.combine(day, time(9, 0)) + timedelta(minutes=rng.randrange(0, 420))
        quiz.started_at, quiz.ended_at = t0, t0 + timedelta(minutes=4 * len(qrows))
        for e in by_class.get(cls.id, []):
            ability.setdefault(e.student_id, rng.betavariate(5, 2))
            habit.setdefault(e.student_id, rng.betavariate(8, 2))
            if rng.random() > habit[e.student_id]:
                continue                                        # absent that day
            for n, q in enumerate(qrows):
                opts = [k for k in "abcd" if q.get(f"option_{k}")]
                correct = "ABCD".index(q["correct"].upper())
                pick = correct if rng.random() < ability[e.student_id] else rng.randrange(len(opts))
                ms = int(min(60000, max(800, rng.lognormvariate(9.2, 0.5))))
                db.add(QuizAnswer(quiz_id=quiz.id, question_order=n, student_id=e.student_id, selected_option=pick,
                                  response_time_ms=ms, submitted_at=t0 + timedelta(minutes=n * 4, milliseconds=ms)))
                out["answers"] += 1
    for p in polls:
        if p.status != "closed":
            continue
        cls = next(c for c in classes.values() if c.id == p.class_session_id)
        day = past_day(cls)
        p.started_at = datetime.combine(day, time(10, 0))
        p.ended_at = p.started_at + timedelta(minutes=5)
        weights = [rng.random() + 0.2 for _ in p.options]
        for e in by_class.get(cls.id, []):
            if rng.random() < 0.85:
                db.add(PollVote(poll_id=p.id, student_id=e.student_id,
                                selected_option=rng.choices(range(len(p.options)), weights)[0], submitted_at=p.ended_at))
                out["votes"] += 1
    for cls in classes.values():
        if not cls.meeting_schedule or not by_class.get(cls.id):
            continue
        start = cls.start_date or (today - timedelta(days=21))
        day = max(start, today - timedelta(days=28))
        meeting_days = {s["day"] for s in cls.meeting_schedule}
        slot = cls.meeting_schedule[0]["start"]
        while day < today:
            if WEEKDAYS[day.weekday()] in meeting_days:
                at = datetime.combine(day, time.fromisoformat(slot))
                for e in by_class[cls.id]:
                    habit.setdefault(e.student_id, rng.betavariate(8, 2))
                    if rng.random() < habit[e.student_id]:
                        db.add(Attendance(class_session_id=cls.id, student_enrollment_id=e.id,
                                          check_in_time=at + timedelta(minutes=rng.randrange(0, 8))))
                        out["attendance"] += 1
            day += timedelta(days=1)
    await db.flush()
    return out


async def table_counts(db: AsyncSession) -> dict:
    out = {}
    for name, model in (("teachers", User), ("courses", Course), ("students", Student), ("classes", ClassSession),
                        ("enrollments", StudentEnrollment), ("quizzes", Quiz), ("polls", Poll)):
        out[name] = await db.scalar(select(func.count()).select_from(model))
    return out
