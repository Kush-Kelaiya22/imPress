"""Global search (v2.2): one query over everything the signed-in user may see.

Scoped by permission, not by what the page happens to show: faculty find only their own classes, the students
they registered or teach, courses, and the quizzes and polls of their classes; administrators also find accounts
and devices. The web app adds pages and settings itself (they are not data).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import ClassSession, Course, EspDevice, Poll, Quiz, Student, User
from ..policy import allowed, class_access, require, role_label
from ..services import features
from ..services.records import student_scope

router = APIRouter(prefix="/api", tags=["search"], dependencies=[Depends(features.require_feature("search"))])


def _like(q: str) -> str:
    return "%" + q.replace("%", r"\%").replace("_", r"\_") + "%"


@router.get("/search")
async def search(q: str = Query("", max_length=80), limit: int = Query(6, ge=1, le=20),
                 user: User = Depends(require("classes.read")), db: AsyncSession = Depends(get_db)):
    q = q.strip()
    if len(q) < 2:
        return {"query": q, "groups": []}
    like = _like(q)
    groups: list[dict] = []

    def add(kind: str, label: str, items: list[dict]) -> None:
        if items:
            groups.append({"type": kind, "label": label, "items": items[:limit]})

    classes = (await db.execute(select(ClassSession).where(or_(
        ClassSession.name.ilike(like, escape="\\"), ClassSession.code.ilike(like, escape="\\"),
        ClassSession.subject.ilike(like, escape="\\"), ClassSession.classroom_code.ilike(like, escape="\\"))).limit(60))).scalars().all()
    mine = [c for c in classes if class_access(user, c)]
    add("class", "Classrooms", [{"id": c.id, "title": c.name, "subtitle": f"{c.code}" + (f" · {c.classroom_code}" if c.classroom_code else ""),
                                 "href": f"#/class?id={c.id}", "icon": c.icon or "school", "color": c.color} for c in mine])

    scope = await student_scope(db, user)
    students = (await db.execute(select(Student).where(or_(
        Student.student_name.ilike(like, escape="\\"), Student.roll_number.ilike(like, escape="\\"),
        Student.program.ilike(like, escape="\\"))).order_by(Student.student_name).limit(60))).scalars().all()
    add("student", "Students", [{"id": s.id, "title": s.student_name, "subtitle": f"{s.roll_number} · {s.program or 'no programme'}",
                                 "href": f"#/student?id={s.id}", "icon": "user"}
                                for s in students if scope is None or s.id in scope])

    courses = (await db.execute(select(Course).where(or_(Course.code.ilike(like, escape="\\"), Course.name.ilike(like, escape="\\")))
                                .limit(limit))).scalars().all()
    add("course", "Courses", [{"id": c.id, "title": c.name, "subtitle": c.code, "href": "#/admin/courses", "icon": "book"}
                              for c in courses] if allowed(user, "courses.read") else [])

    ids = [c.id for c in mine] if not allowed(user, "classes.manage_all") else None
    qz = select(Quiz).where(Quiz.title.ilike(like, escape="\\")).limit(30)
    pl = select(Poll).where(Poll.title.ilike(like, escape="\\")).limit(30)
    if ids is not None:
        mine_ids = {c.id for c in (await db.execute(select(ClassSession))).scalars().all() if class_access(user, c)}
        qz, pl = qz.where(Quiz.class_session_id.in_(mine_ids)), pl.where(Poll.class_session_id.in_(mine_ids))
    add("quiz", "Quizzes", [{"id": x.id, "title": x.title, "subtitle": f"Quiz · {x.status}", "href": f"#/class?id={x.class_session_id}",
                             "icon": "clipboard"} for x in (await db.execute(qz)).scalars().all()])
    add("poll", "Polls", [{"id": x.id, "title": x.title, "subtitle": f"Poll · {x.status}", "href": f"#/class?id={x.class_session_id}",
                           "icon": "poll"} for x in (await db.execute(pl)).scalars().all()])

    if allowed(user, "users.read"):
        users = (await db.execute(select(User).where(or_(
            User.username.ilike(like, escape="\\"), User.full_name.ilike(like, escape="\\"),
            User.display_name.ilike(like, escape="\\"), User.email.ilike(like, escape="\\"))).limit(limit))).scalars().all()
        add("user", "Accounts", [{"id": u.id, "title": u.display_name or u.full_name or u.username,
                                  "subtitle": f"@{u.username} · {role_label(u.role, u.designation)}",
                                  "href": "#/admin/users", "icon": "userCog"} for u in users])
    if allowed(user, "devices.read"):
        devs = (await db.execute(select(EspDevice).where(or_(EspDevice.device_name.ilike(like, escape="\\"),
                                                             EspDevice.mac_address.ilike(like, escape="\\"))).limit(limit))).scalars().all()
        add("device", "Devices", [{"id": d.id, "title": d.device_name or d.mac_address, "subtitle": f"{d.device_type} · {d.mac_address}",
                                   "href": "#/admin/modules", "icon": "radio"} for d in devs])
    return {"query": q, "groups": groups}
