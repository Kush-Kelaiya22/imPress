"""Class session router: teacher sees assigned classes, activate/deactivate."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, ClassSession, StudentEnrollment, EspDevice
from ..schemas import ClassCreate, ClassJoin, ClassResponse, DeviceTreeResponse, DeviceTreeNode
from ..auth import get_current_user, require_teacher_or_admin
from ..activity import log_activity
from ..schedule import find_schedule_conflicts
from ..services.presence import presence_snapshot
from sqlalchemy import select

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


def _has_access(cls: ClassSession, user: User) -> bool:
    """Primary teacher, any secondary faculty, or any admin may work with the class."""
    if user.role in ("admin", "super_admin"):
        return True
    if user.role == "teacher":
        return cls.teacher_id == user.id or any(f.id == user.id for f in (cls.faculty or []))
    return False


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
        quiz_count=len(cls.quizzes) if cls.quizzes else 0,
        poll_count=len(cls.polls) if cls.polls else 0,
        warnings=warnings or [],
    )


@router.get("/", response_model=list[ClassResponse])
async def list_classes(
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Teacher sees only assigned classes. Admin sees all (use /admin/classes)."""
    if user.role in ("admin", "super_admin"):
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
    user: User = Depends(require_teacher_or_admin),
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
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not _has_access(cls, user):
        raise HTTPException(403, "You don't have access to this class")
    sc = await _count_students(db, cls.id)
    return _to_response(cls, sc)


@router.get("/{class_id}/presence")
async def class_presence(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Live presence snapshot for all ESP devices in this class."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not _has_access(cls, user):
        raise HTTPException(403, "You don't have access to this class")
    return await presence_snapshot(db, class_id)


@router.post("/{class_id}/activate", response_model=ClassResponse)
async def activate_class(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not _has_access(cls, user):
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
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not _has_access(cls, user):
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
    user: User = Depends(require_teacher_or_admin),
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
    if user.role == "teacher" and not _has_access(cls, user):
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
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if user.role not in ("admin", "super_admin") and cls.teacher_id != user.id:
        raise HTTPException(403, "Only the primary teacher or admin can delete this class")

    await log_activity(db, "class.delete", user.id, "class", class_id, {"name": cls.name})
    await db.delete(cls)
    await db.commit()
    return {"status": "deleted"}


# ── Live device presence (teacher dashboard polling) ────────────────

live_router = APIRouter(prefix="/api/devices", tags=["devices", "live"])


@live_router.get("/live")
async def list_live_devices(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
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
    if not _has_access(cls, user):
        raise HTTPException(403, "You don't have access to this class")
    return await presence_snapshot(db, class_id)


@live_router.get("/tree", response_model=DeviceTreeResponse)
async def get_device_tree(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
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
    if not _has_access(cls, user):
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
