"""Course catalog router: universal courses referenced by classroom sections."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Course, ClassSession
from ..schemas import CourseCreate, CourseUpdate, CourseResponse
from ..auth import require_admin, require_teacher_or_admin
from ..activity import log_activity

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("/", response_model=CourseResponse, status_code=201)
async def create_course(
    body: CourseCreate,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a course in the universal catalog."""
    existing = await db.execute(select(Course).where(Course.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Course code {body.code!r} already exists")

    course = Course(
        code=body.code.strip().upper(),
        name=body.name.strip(),
        description=body.description,
        credits=body.credits,
        department=body.department,
        exam_date=body.exam_date,
        exam_start_time=body.exam_start_time,
        exam_end_time=body.exam_end_time,
    )
    db.add(course)
    await db.flush()
    await log_activity(db, "course.create", user.id, "course", course.id, {
        "code": course.code, "name": course.name,
    })
    await db.commit()
    await db.refresh(course)
    return course


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    user=Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all courses (admins see inactive too; faculty see active)."""
    q = select(Course).order_by(Course.code)
    if user.role not in ("admin", "super_admin"):
        q = q.where(Course.is_active == True)  # noqa: E712
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    user=Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(404, "Course not found")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    body: CourseUpdate,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(404, "Course not found")

    changed = {}
    if body.code is not None:
        new_code = body.code.strip().upper()
        dup = await db.execute(select(Course).where(Course.code == new_code, Course.id != course_id))
        if dup.scalar_one_or_none():
            raise HTTPException(400, f"Course code {new_code!r} already exists")
        course.code, changed["code"] = new_code, new_code
    if body.name is not None:
        course.name, changed["name"] = body.name.strip(), body.name.strip()
    for field in ("description", "credits", "department", "is_active", "exam_date", "exam_start_time", "exam_end_time"):
        val = getattr(body, field)
        if val is not None:
            setattr(course, field, val)
            changed[field] = val

    await log_activity(db, "course.update", user.id, "course", course_id, changed)
    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete: deactivate the course. Refuse if sections still reference it."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(404, "Course not found")

    section_count = await db.execute(
        select(func.count()).select_from(ClassSession).where(ClassSession.course_id == course_id)
    )
    if section_count.scalar() or 0 > 0:
        # Deactivate instead of hard delete to preserve classroom history
        course.is_active = False
        await log_activity(db, "course.delete", user.id, "course", course_id, {"deactivated": True})
        await db.commit()
        return {"status": "deactivated"}

    await log_activity(db, "course.delete", user.id, "course", course_id)
    await db.delete(course)
    await db.commit()
    return {"status": "deleted"}