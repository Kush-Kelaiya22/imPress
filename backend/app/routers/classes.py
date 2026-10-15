"""Class session router: teacher sees assigned classes, activate/deactivate."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..policy import class_access, class_owner_or_admin, require, sees_all_classes
from ..database import get_db
from ..models import User, ClassOccurrenceException, ClassSession, StudentEnrollment, EspDevice
from ..schemas import (
    ClassCreate, ClassJoin, ClassResponse, DeviceTreeResponse, DeviceTreeNode,
    OccurrenceExceptionCreate, OccurrenceExceptionResponse,
)

from ..activity import log_activity
from ..schedule import find_schedule_conflicts, occupancy
from ..services.presence import presence_snapshot
from ..services.records import delete_class_records, ensure_section_free

router = APIRouter(prefix="/api/classes", tags=["classes"])


async def _count_students(db: AsyncSession, class_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(StudentEnrollment)
        .where(StudentEnrollment.class_session_id == class_id, StudentEnrollment.is_active == True)  # noqa: E712
    )
    return result.scalar() or 0


async def _reload_class(db: AsyncSession, class_id: int) -> ClassSession:
    """Re-select a class after mutation so selectin relationships load in the async context."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    return result.scalar_one()


def _to_response(cls: ClassSession, student_count: int = 0, warnings: list | None = None) -> ClassResponse:
    course = cls.course if getattr(cls, "course", None) else None
    faculty = cls.faculty or []  # lazy="selectin", safe to touch
    teacher_ids = sorted({f.id for f in faculty} | {cls.teacher_id} if cls.teacher_id else {f.id for f in faculty})
    faculty_names = [{"id": f.id, "full_name": f.full_name or f.username} for f in faculty]

    # Exam fields: prefer course-level if available, fall back to class-level for legacy
    exam_date = course.exam_date if course and course.exam_date else cls.exam_start_date
    exam_start_time = course.exam_start_time if course and course.exam_start_time else None
    exam_end_time = course.exam_end_time if course and course.exam_end_time else None
    reading_week_start = exam_date - timedelta(days=7) if exam_date else None

    return ClassResponse(
        id=cls.id,
        name=cls.name,
        subject=getattr(cls, "subject", ""),
        code=cls.code,
        teacher_id=cls.teacher_id,
        teacher_name=cls.teacher.full_name if cls.teacher else "",
        is_active=cls.is_active,
        created_at=cls.created_at,
        course_id=cls.course_id,
        course_code=course.code if course else "",
        course_name=course.name if course else "",
        course_section=cls.course_section or "",
        icon=cls.icon or "", color=cls.color or "",
        term=cls.term or "",
        year=cls.year,
        start_date=cls.start_date,
        end_date=cls.end_date,
        exam_date=exam_date,
        exam_start_time=exam_start_time,
        exam_end_time=exam_end_time,
        reading_week_start=reading_week_start,
        meeting_schedule=cls.meeting_schedule or [],
        location=cls.location or "",
        capacity=cls.capacity or 0,
        classroom_code=cls.classroom_code or "",
        teacher_ids=teacher_ids,
        faculty_names=faculty_names,
        student_count=student_count,
        quiz_count=cls.quiz_count or 0,
        poll_count=cls.poll_count or 0,
        warnings=warnings or [],
    )


@router.get("/", response_model=list[ClassResponse])
async def list_classes(
    user: User = Depends(require("classes.read")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher sees only assigned classes. Admin sees all (use /admin/classes)."""
    if sees_all_classes(user):
        result = await db.execute(select(ClassSession).order_by(ClassSession.id.desc()))
    else:
        # Primary teacher OR any secondary faculty (many-to-many) sees the class
        result = await db.execute(
            select(ClassSession)
            .where(
                or_(
                    ClassSession.teacher_id == user.id,
                    ClassSession.faculty.any(User.id == user.id),
                )
            )
            .order_by(ClassSession.id.desc())
        )
    classes = result.scalars().all()
    out = []
    for cls in classes:
        sc = await _count_students(db, cls.id)
        out.append(_to_response(cls, sc))
    return out


@router.post("/", response_model=ClassResponse, status_code=201)
async def create_class(
    body: ClassCreate,
    user: User = Depends(require("classes.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new classroom (assigned to self). Admin should use /admin/classes."""
    schedule = [s.model_dump() if hasattr(s, "model_dump") else s for s in (body.meeting_schedule or [])]
    teacher_id = body.teacher_id if body.teacher_id is not None else user.id
    warnings = await find_schedule_conflicts(
        db, teacher_id, schedule, body.location,
        term=body.term, year=body.year,
        start_date=body.start_date, end_date=body.end_date,
    )

    await ensure_section_free(db, body.course_id, body.course_section)
    cls = ClassSession(
        name=body.name,
        subject=getattr(body, "subject", ""),
        code=body.code.strip(),
        teacher_id=teacher_id,
        created_by=user.id,
        course_id=body.course_id,
        course_section=body.course_section,
        term=body.term,
        year=body.year,
        start_date=body.start_date,
        end_date=body.end_date,
        exam_start_date=body.exam_start_date,
        exam_end_date=body.exam_end_date,
        meeting_schedule=schedule,
        location=body.location,
        capacity=body.capacity,
        icon=body.icon, color=body.color,
    )
    db.add(cls)
    await db.flush()
    await log_activity(db, "class.create", user.id, "class", cls.id, {"name": body.name})
    await db.commit()
    cls = await _reload_class(db, cls.id)
    return _to_response(cls, 0, warnings=warnings)


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    user: User = Depends(require("classes.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")
    sc = await _count_students(db, cls.id)
    return _to_response(cls, sc)


@router.get("/{class_id}/presence")
async def class_presence(
    class_id: int,
    user: User = Depends(require("classes.read")),
    db: AsyncSession = Depends(get_db),
):
    """Live presence snapshot for all ESP devices in this class."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")
    return await presence_snapshot(db, class_id)


@router.post("/{class_id}/activate", response_model=ClassResponse)
async def activate_class(
    class_id: int,
    user: User = Depends(require("classes.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")

    cls.is_active = True
    await log_activity(db, "class.activate", user.id, "class", class_id)
    await db.commit()
    await db.refresh(cls)
    sc = await _count_students(db, cls.id)
    return _to_response(cls, sc)


@router.post("/{class_id}/deactivate", response_model=ClassResponse)
async def deactivate_class(
    class_id: int,
    user: User = Depends(require("classes.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")

    cls.is_active = False
    await log_activity(db, "class.deactivate", user.id, "class", class_id)
    await db.commit()
    await db.refresh(cls)
    sc = await _count_students(db, cls.id)
    return _to_response(cls, sc)


@router.post("/join", response_model=ClassResponse)
async def join_class(
    body: ClassJoin,
    user: User = Depends(require("classes.join")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.code == body.code))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found or code is invalid")
    if not cls.is_active:
        raise HTTPException(400, "Class is not active")

    # A teacher joining by code becomes CO-FACULTY. The primary teacher is never
    # replaced here: knowing a (shared, short) join code must not transfer
    # ownership. Re-assigning the primary teacher is an admin action
    # (/api/admin/classes/{id}/assign-teacher).
    if not class_access(user, cls):
        cls.faculty.append(user)
        await log_activity(db, "class.join_via_code", user.id, "class", cls.id,
                           {"as": "co-faculty"})
        await db.commit()
        cls = await _reload_class(db, cls.id)

    sc = await _count_students(db, cls.id)
    return _to_response(cls, sc)


@router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    user: User = Depends(require("classes.manage")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_owner_or_admin(user, cls):
        raise HTTPException(403, "Only the primary teacher or admin can delete this class")

    await log_activity(db, "class.delete", user.id, "class", class_id, {"name": cls.name})
    await delete_class_records(db, class_id)
    await db.commit()
    return {"status": "deleted"}


# ── Live device presence (teacher dashboard polling) ────────────────

live_router = APIRouter(prefix="/api/devices", tags=["devices", "live"])


# ── Timetable exceptions (#126) ───────────────────────────────────────────

async def _accessible_class(db: AsyncSession, class_id: int, user: User) -> ClassSession:
    cls = (await db.execute(select(ClassSession).where(ClassSession.id == class_id))).scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")
    return cls


@router.get("/{class_id}/exceptions", response_model=list[OccurrenceExceptionResponse])
async def list_exceptions(
    class_id: int,
    user: User = Depends(require("classes.read")),
    db: AsyncSession = Depends(get_db),
):
    """Cancelled, moved and extra occurrences of this class, by date."""
    await _accessible_class(db, class_id, user)
    rows = await db.execute(select(ClassOccurrenceException)
                            .where(ClassOccurrenceException.class_session_id == class_id)
                            .order_by(ClassOccurrenceException.date, ClassOccurrenceException.slot_start))
    return rows.scalars().all()


@router.post("/{class_id}/exceptions", response_model=OccurrenceExceptionResponse, status_code=201)
async def add_exception(
    class_id: int,
    body: OccurrenceExceptionCreate,
    user: User = Depends(require("classes.manage")),
    db: AsyncSession = Depends(get_db),
):
    """Record a cancelled, moved or extra occurrence. A moved or extra one
    that overlaps another booking of its room comes back with `warnings`."""
    cls = await _accessible_class(db, class_id, user)
    if body.kind in ("moved", "extra") and not (body.new_start and body.new_end):
        raise HTTPException(422, "new_start and new_end are required for a moved or extra occurrence")
    if body.kind == "moved" and not body.slot_start:
        raise HTTPException(422, "slot_start: which regular slot is moved")
    e = ClassOccurrenceException(
        class_session_id=cls.id, kind=body.kind, date=body.date, slot_start=body.slot_start,
        new_date=(body.new_date or body.date) if body.kind == "moved" else (body.date if body.kind == "extra" else None),
        new_start=body.new_start if body.kind != "cancelled" else "",
        new_end=body.new_end if body.kind != "cancelled" else "",
        classroom_code=body.classroom_code.strip() if body.kind != "cancelled" else "",
        note=body.note, source="local", created_by=user.id)
    db.add(e)
    await db.flush()
    warnings = []
    room = e.classroom_code or cls.classroom_code or ""
    if e.kind != "cancelled" and room:
        day = e.new_date
        a = datetime.combine(day, datetime.strptime(e.new_start, "%H:%M").time())
        b = datetime.combine(day, datetime.strptime(e.new_end, "%H:%M").time())
        for busy in await occupancy(db, room, a, b if b > a else b + timedelta(days=1)) or []:
            if busy.class_id != cls.id:
                warnings.append({"type": "room", "class_id": busy.class_id, "start": busy.start.isoformat(),
                                 "end": busy.end.isoformat(), "message": f"Room {room} is booked by class #{busy.class_id}"})
    await log_activity(db, "class.exception", user.id, "class", cls.id, {"kind": e.kind, "date": str(e.date)})
    await db.commit()
    out = OccurrenceExceptionResponse.model_validate(e)
    out.warnings = warnings
    return out


@router.delete("/{class_id}/exceptions/{exception_id}", status_code=204)
async def delete_exception(
    class_id: int,
    exception_id: int,
    user: User = Depends(require("classes.manage")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a local timetable change. AURIS-sourced changes are replaced by
    the next import instead (#127)."""
    await _accessible_class(db, class_id, user)
    e = (await db.execute(select(ClassOccurrenceException).where(
        ClassOccurrenceException.id == exception_id,
        ClassOccurrenceException.class_session_id == class_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "No such timetable change")
    if e.source != "local":
        raise HTTPException(409, {"code": "SOURCE_MANAGED", "message": f"This change comes from {e.source}; it is "
                                  "updated by the next import"})
    await db.delete(e)
    await log_activity(db, "class.exception_removed", user.id, "class", class_id, {"date": str(e.date)})
    await db.commit()


@live_router.get("/live")
async def list_live_devices(
    class_id: int,
    user: User = Depends(require("classes.read")),
    db: AsyncSession = Depends(get_db),
):
    """Latest ESP device presence for a class.

    Returns every device in the class relay tree (C6 gateway + relayed S3 /
    student nodes) with is_connected, online, last_seen, battery_pct, rssi.
    Same access rule as GET /api/classes/{id}/presence: primary teacher,
    secondary faculty, or any admin.
    """
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")
    return await presence_snapshot(db, class_id)


@live_router.get("/tree", response_model=DeviceTreeResponse)
async def get_device_tree(
    class_id: int,
    user: User = Depends(require("classes.read")),
    db: AsyncSession = Depends(get_db),
):
    """Device tree (relay topology) for a class.

    Returns the C6 gateway as root and all student nodes with hop count,
    RSSI, and parent enrollment (if relayed). Faculty sees only their class.
    """
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not class_access(user, cls):
        raise HTTPException(403, "You don't have access to this class")

    if not cls.device_id:
        raise HTTPException(404, "No root device found for class")
    root = (await db.execute(
        select(EspDevice).where(EspDevice.id == cls.device_id)
    )).scalar_one_or_none()
    if not root:
        raise HTTPException(404, "No root device found for class")

    # All devices: root + relayed tree, BFS via gateway_id (same as presence_snapshot)
    result = await db.execute(select(EspDevice))
    children_map = {}
    for d in result.scalars().all():
        if d.gateway_id is not None:
            children_map.setdefault(d.gateway_id, []).append(d)

    def enrollment_of(dev: EspDevice) -> str | None:
        se = dev.student_enrollment
        if se is not None and se.student is not None:
            return se.student.roll_number
        return str(dev.device_id) if dev.device_id else None

    # Build tree nodes recursively
    def build_node(device: EspDevice, hop_count: int = 0, parent_enrollment: str = None) -> DeviceTreeNode:
        is_direct = (device.gateway_id == root.id) if root else (hop_count <= 1)
        return DeviceTreeNode(
            id=device.id,
            enrollment=enrollment_of(device),
            device_id=device.device_id or 0,
            hop_count=hop_count,
            rssi=device.rssi or 0,
            is_direct=is_direct,
            parent_enrollment=parent_enrollment,
            device_type=device.device_type,
            student_name=device.student_name,
            is_connected=device.is_connected,
            battery_pct=device.battery_pct or 0,
        )

    # Build node list via BFS
    nodes = []
    queue = [(root, 0, None)]
    while queue:
        device, hop_count, parent_enrollment = queue.pop(0)
        node = build_node(device, hop_count, parent_enrollment)
        nodes.append(node)
        for child in children_map.get(device.id, []):
            queue.append((child, hop_count + 1, enrollment_of(device)))

    root_node = nodes[0] if nodes else None
    if not root_node:
        raise HTTPException(404, "Failed to build device tree")

    return DeviceTreeResponse(
        class_id=class_id,
        root=root_node,
        nodes=nodes,
    )
