"""CSV → courses and their sections (class sessions) (#32).

One row = one section of a course:
    course_code, course_name, section, class_code, teacher_username
    [, class_name, classroom_code, term, year, capacity, location]

Planning (read-only) decides, per row: create the section, update it (only
in mode=update, only the optional fields), skip it as unchanged, or reject
it with reasons. Courses are created when their code is new and matched by
code otherwise; a different name for an existing code is a conflict, never a
silent rename. Applying runs the plan in one transaction (all-or-nothing).
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ClassSession, Course, User
from ..schemas import SEMESTERS, ClassImportReport, ClassImportRow
from .csv_import import read_rows, to_csv

REQUIRED = ["course_code", "course_name", "section", "class_code", "teacher_username"]
OPTIONAL = ["class_name", "classroom_code", "term", "year", "capacity", "location"]
ALIASES = {
    # the wording used in the v2.1 brief: classroom = course, section = class session
    "classroom_code": "course_code", "classroom_name": "course_name",
    "section_code": "section", "section_name": "class_name",
    "course": "course_code", "teacher": "teacher_username", "code": "class_code",
    "join_code": "class_code", "room": "classroom_code", "room_code": "classroom_code",
}

TEMPLATE = to_csv(REQUIRED + OPTIONAL, [
    ["CS101", "Introduction to Computing", "A", "CS101-A-2026", "teacher1", "CS101 Section A", "RM-201",
     "Monsoon", 2026, 60, "Block B"],
    ["CS101", "Introduction to Computing", "B", "CS101-B-2026", "teacher2", "", "", "Monsoon", 2026, 60, ""],
    ["MA201", "Linear Algebra", "A", "MA201-A-2026", "teacher1", "", "", "", "", "", ""],
])

_LIMITS = {"course_code": 16, "course_name": 128, "section": 16, "class_code": 32, "class_name": 128,
           "classroom_code": 32, "location": 128}


def _resolve_aliases(raw: bytes) -> dict[str, str]:
    """`classroom_code` means the course in the brief's layout (it comes with
    `classroom_name`), and the physical room label in ours."""
    head = raw.decode("utf-8-sig", errors="replace").splitlines()[0].lower() if raw.strip() else ""
    names = {re.sub(r"[\s\-]+", "_", h.strip()) for h in head.split(",")}
    aliases = dict(ALIASES)
    if "classroom_name" not in names:
        aliases.pop("classroom_code")
    return aliases


def _row_fields(r: dict, errors: list[str]) -> dict:
    v = {k: r.get(k, "").strip() for k in REQUIRED + OPTIONAL}
    v["course_code"] = v["course_code"].upper()
    for k in REQUIRED:
        if not v[k]:
            errors.append(f"{k} is empty")
    for k, n in _LIMITS.items():
        if len(v[k]) > n:
            errors.append(f"{k} is longer than {n} characters")
    if v["term"] and v["term"].capitalize() not in SEMESTERS:
        errors.append(f"term '{v['term']}' must be one of {', '.join(SEMESTERS)}")
    v["term"] = v["term"].capitalize() if v["term"] else ""
    for k, lo, hi in (("year", 2000, 2100), ("capacity", 0, 5000)):
        if v[k]:
            if not v[k].isdigit() or not lo <= int(v[k]) <= hi:
                errors.append(f"{k} '{v[k]}' must be a whole number from {lo} to {hi}")
                v[k] = None                    # the error explains it; the row stays reportable
            else:
                v[k] = int(v[k])
        else:
            v[k] = None
    return v


async def plan_class_import(db: AsyncSession, raw: bytes, mode: str = "create") -> ClassImportReport:
    rows = read_rows(raw, REQUIRED, OPTIONAL, _resolve_aliases(raw))

    courses = {c.code: c for c in (await db.execute(select(Course))).scalars()}
    classes = list((await db.execute(select(ClassSession))).scalars())
    by_code = {c.code: c for c in classes}
    by_section = {(c.course_id, c.course_section): c for c in classes if c.course_id and c.course_section}
    by_room = {c.classroom_code: c for c in classes if c.classroom_code}
    teachers = {u.username: u for u in (await db.execute(
        select(User).where(User.role == "teacher", User.is_active == True))).scalars()}  # noqa: E712

    file_courses: dict[str, tuple[str, int]] = {}      # code -> (name, first line)
    file_codes: dict[str, int] = {}
    file_sections: dict[tuple[str, str], int] = {}
    file_rooms: dict[str, int] = {}
    out: list[ClassImportRow] = []

    for line, r in rows:
        errors: list[str] = []
        if "__extra__" in r:
            errors.append(r.pop("__extra__"))
        v = _row_fields(r, errors)
        cc, sec, code, room = v["course_code"], v["section"], v["class_code"], v["classroom_code"]
        action, note, changes = "create", None, []

        if not errors:
            # course: create, or match by code with the same name
            existing_course = courses.get(cc)
            if existing_course and existing_course.name != v["course_name"]:
                errors.append(f"course {cc} already exists as '{existing_course.name}', "
                              f"not '{v['course_name']}' (rename it in Courses first)")
            seen = file_courses.setdefault(cc, (v["course_name"], line))
            if seen[0] != v["course_name"]:
                errors.append(f"course {cc} is called '{seen[0]}' on line {seen[1]}")

            teacher = teachers.get(v["teacher_username"])
            if teacher is None:
                errors.append(f"no active teacher with username '{v['teacher_username']}'")

            # within the file
            if code in file_codes:
                errors.append(f"class_code {code} is also on line {file_codes[code]}")
            if (cc, sec) in file_sections:
                errors.append(f"section {sec} of {cc} is also on line {file_sections[(cc, sec)]}")
            if room and room in file_rooms:
                errors.append(f"room {room} is also on line {file_rooms[room]}")

            # against the database
            course_id = existing_course.id if existing_course else None
            current = by_code.get(code)
            if current is not None:
                if current.course_id != course_id or (current.course_section or "") != sec:
                    errors.append(f"class_code {code} is already used by another class")
                elif mode == "update":
                    changes = _changes(current, v, teacher)
                    action, note = (("update", "changes: " + ", ".join(changes)) if changes
                                    else ("unchanged", "already up to date"))
                else:
                    action, note = "duplicate", "already exists; skipped (use update mode to change it)"
            else:
                clash = by_section.get((course_id, sec)) if course_id else None
                if clash is not None:
                    errors.append(f"section {sec} of {cc} already exists with class_code {clash.code}")
            if room and room in by_room and by_room[room].code != code:
                errors.append(f"room {room} is already assigned to class {by_room[room].code}")

        file_codes.setdefault(code, line)
        file_sections.setdefault((cc, sec), line)
        if room:
            file_rooms.setdefault(room, line)
        out.append(ClassImportRow(
            line=line, status="invalid" if errors else action, errors=errors, note=note, changes=changes,
            course_code=cc, course_name=v["course_name"], section=sec, class_code=code,
            teacher_username=v["teacher_username"], class_name=v["class_name"] or f"{cc} {sec}".strip(),
            classroom_code=room or None, term=v["term"], year=v["year"], capacity=v["capacity"],
            location=v["location"], new_course=not errors and cc not in courses
            and file_courses.get(cc, ("", line))[1] == line))

    count = {s: sum(r.status == s for r in out) for s in ("create", "update", "duplicate", "unchanged", "invalid")}
    return ClassImportReport(
        mode=mode, total=len(out), create=count["create"], update=count["update"],
        duplicate=count["duplicate"] + count["unchanged"], invalid=count["invalid"],
        new_courses=sum(r.new_course for r in out), imported=0, skipped=len(out), rows=out)


def _changes(cls: ClassSession, v: dict, teacher: User | None) -> list[str]:
    changed = []
    if v["class_name"] and v["class_name"] != cls.name:
        changed.append("class_name")
    for field in ("classroom_code", "term", "location"):
        if v[field] and v[field] != (getattr(cls, field) or ""):
            changed.append(field)
    for field in ("year", "capacity"):
        if v[field] is not None and v[field] != getattr(cls, field):
            changed.append(field)
    if teacher is not None and teacher.id != cls.teacher_id:
        changed.append("teacher_username")
    return changed


async def apply_class_import(db: AsyncSession, report: ClassImportReport, user: User) -> None:
    """Execute a plan with no invalid rows (not committed)."""
    courses = {c.code: c for c in (await db.execute(select(Course))).scalars()}
    teachers = {u.username: u for u in (await db.execute(select(User).where(User.role == "teacher"))).scalars()}
    for row in report.rows:
        if row.status not in ("create", "update"):
            continue
        course = courses.get(row.course_code)
        if course is None:
            course = courses[row.course_code] = Course(code=row.course_code, name=row.course_name)
            db.add(course)
            await db.flush()
        teacher = teachers[row.teacher_username]
        if row.status == "create":
            cls = ClassSession(name=row.class_name, code=row.class_code, course_id=course.id,
                               course_section=row.section, teacher_id=teacher.id, created_by=user.id,
                               classroom_code=row.classroom_code, term=row.term, year=row.year,
                               capacity=row.capacity or 0, location=row.location)
            cls.faculty = [teacher]          # like the form: the primary teacher is also faculty
            db.add(cls)
        else:
            cls = (await db.execute(select(ClassSession).where(ClassSession.code == row.class_code))).scalar_one()
            for field in row.changes:
                if field == "teacher_username":
                    # new primary teacher; co-faculty other than the old primary stay
                    old = cls.teacher_id
                    cls.faculty = [teacher] + [f for f in cls.faculty if f.id not in (old, teacher.id)]
                    cls.teacher_id = teacher.id
                elif field == "class_name":
                    cls.name = row.class_name
                else:
                    setattr(cls, field, getattr(row, field))
        await db.flush()


def export_rows(courses: dict[int, Course], classes: list[ClassSession],
                usernames: dict[int, str]) -> tuple[str, int]:
    """Course sections in the import layout (formula-safe), and how many
    classes were left out because they belong to no course (they couldn't be
    re-imported: course_code is required)."""
    sections = sorted((c for c in classes if c.course_id in courses),
                      key=lambda c: (courses[c.course_id].code, c.course_section or "", c.code))
    rows = [[courses[c.course_id].code, courses[c.course_id].name, c.course_section or "", c.code,
             usernames.get(c.teacher_id, ""), c.name, c.classroom_code or "", c.term or "",
             c.year or "", c.capacity or "", c.location or ""] for c in sections]
    return to_csv(REQUIRED + OPTIONAL, rows), len(classes) - len(sections)
