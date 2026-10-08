"""Admin router: user management, class (classroom) management & enrollment, activity logs."""

import csv
import hashlib
import io
import re
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import commit_or_conflict, get_db
from ..models import (
    User, ClassSession, Course, Student, StudentEnrollment, EspDevice, ActivityLog,
)
from ..schemas import (
    AdminUserCreate, UserResponse, UserUpdate,
    PasswordReset,
    ClassCreate, ClassUpdate, ClassAssignTeacher, ClassResponse, ClassImportReport,
    ClassFacultyUpdate,
    StudentRegister, StudentResponse, BulkStudentRegister, StudentEnroll,
    ActivityLogResponse,
    DeviceResponse, ModuleAccessUpdate, ModuleOtaRequest, ModuleLinkDevice,
    ClassDevicesResponse,
    CsvImportResult, CsvImportError,
)
from ..services.firmware_store import firmware_path, normalize_version, save_firmware
from ..services.mesh_bridge import send_command_to_devices
from ..timeutil import istnow
from ..auth import require_admin, require_teacher_or_admin
from ..activity import log_activity
from ..schedule import find_schedule_conflicts
from ..services.records import delete_class_records, ensure_section_free
from ..services.class_import import TEMPLATE as CLASS_TEMPLATE, apply_class_import, export_rows, plan_class_import
from ..services.csv_import import read_upload

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── User Management ─────────────────────────────────────────────────

_PRIVILEGED_ROLES = ("admin", "super_admin")


def _require_can_grant(actor: User, role: str) -> None:
    """Only a super admin may grant (or take away) admin-level roles."""
    if role in _PRIVILEGED_ROLES and actor.role != "super_admin":
        raise HTTPException(403, "Only super admin can assign admin roles")


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: AdminUserCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a teacher or admin account. Super admin can also create admins."""
    _require_can_grant(user, body.role)

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Username already taken")

    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    from ..auth import hash_password
    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        created_by=user.id,
    )
    db.add(new_user)
    await db.flush()
    await log_activity(db, "user.create", user.id, "user", new_user.id, {"role": body.role})
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/users/import", response_model=CsvImportResult)
async def import_users_csv(
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Mass-import user accounts from CSV.
    Required columns (all compulsory): username, email, password, full_name, role.
    role must be "teacher" or "admin" (admin accounts require super_admin rights).
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(400, "CSV is empty or has no columns")

    fieldnames = [h.strip().lower() for h in reader.fieldnames]
    reader.fieldnames = fieldnames

    req_cols = {"username", "email", "password", "full_name", "role"}
    field_set = set(fieldnames)
    if field_set != req_cols:
        missing = req_cols - field_set
        extra = field_set - req_cols
        parts = []
        if missing: parts.append(f"missing: {', '.join(sorted(missing))}")
        if extra:   parts.append(f"unexpected columns: {', '.join(sorted(extra))}")
        raise HTTPException(400, "CSV must contain exactly 5 columns (" + "; ".join(parts) + ")")

    from ..auth import hash_password

    user_re = re.compile(r"^[A-Za-z0-9_.]{3,64}$")
    email_re = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    seen_usernames: set[str] = set()
    seen_emails: set[str] = set()
    valid_rows: list[dict] = []
    errors: list[CsvImportError] = []

    for row_idx, row in enumerate(reader, start=2):
        username = (row.get("username") or "").strip()
        email    = (row.get("email") or "").strip()
        password = (row.get("password") or "").strip()
        full_name = (row.get("full_name") or "").strip()
        role      = (row.get("role") or "").strip().lower()

        if not any([username, email, password, full_name, role]):
            continue

        # All 5 fields compulsory
        blanks = [c for c, v in zip(["username", "email", "password", "full_name", "role"],
                                    [username, email, password, full_name, role]) if not v]
        if blanks:
            errors.append(CsvImportError(row=row_idx, roll_number=username or "(empty)",
                error=f"missing required field(s): {', '.join(blanks)}"))
            continue

        # Format validation
        if not user_re.match(username):
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="username must be 3–64 characters (letters, digits, _ .)"))
            continue
        if not email_re.match(email):
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="email is invalid (must be like name@domain.com)"))
            continue
        if len(password) < 6:
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="password must be at least 6 characters"))
            continue
        if role not in ("teacher", "admin"):
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="role must be 'teacher' or 'admin'"))
            continue
        if role == "admin" and user.role != "super_admin":
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="only a super admin can create admin accounts"))
            continue

        # Duplicate checks
        if username in seen_usernames:
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="duplicate username within CSV"))
            continue
        if email in seen_emails:
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="duplicate email within CSV"))
            continue

        existing_u = await db.execute(select(User).where(User.username == username))
        if existing_u.scalar_one_or_none():
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="username already exists in database"))
            continue
        existing_e = await db.execute(select(User).where(User.email == email))
        if existing_e.scalar_one_or_none():
            errors.append(CsvImportError(row=row_idx, roll_number=username,
                error="email already exists in database"))
            continue

        seen_usernames.add(username)
        seen_emails.add(email)
        valid_rows.append({
            "username": username, "email": email, "password": password,
            "full_name": full_name, "role": role,
        })

    inserted = 0
    for v in valid_rows:
        new_user = User(
            username=v["username"],
            email=v["email"],
            hashed_password=hash_password(v["password"]),
            full_name=v["full_name"],
            role=v["role"],
            created_by=user.id,
        )
        db.add(new_user)
        await db.flush()
        await log_activity(db, "user.create", user.id, "user", new_user.id, {"role": v["role"]})
        inserted += 1

    await log_activity(db, "user.csv_import", user.id, "user", None, {
        "inserted": inserted, "skipped": len(errors),
    })
    await db.commit()

    return CsvImportResult(
        inserted=inserted,
        skipped=errors,
        total_rows=len(valid_rows) + len(errors),
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    role: str = Query("", description="Filter by role"),
):
    q = select(User).order_by(User.id.desc())
    if role:
        q = q.where(User.role == role)
    result = await db.execute(q)
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "User not found")
    if target.role == "super_admin" and user.role != "super_admin":
        raise HTTPException(403, "Cannot modify super admin")

    if body.full_name is not None:
        target.full_name = body.full_name
    if body.email is not None:
        target.email = body.email
    if body.is_active is not None:
        target.is_active = body.is_active
    if body.role is not None and body.role != target.role:
        if target.id == user.id:
            raise HTTPException(403, "You cannot change your own role")
        _require_can_grant(user, body.role)     # granting admin-level
        _require_can_grant(user, target.role)   # demoting an admin-level user
        target.role = body.role

    await log_activity(db, "user.update", user.id, "user", user_id, body.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(target)
    return target


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == user.id:
        raise HTTPException(400, "Cannot deactivate yourself")
    if target.role == "super_admin" and user.role != "super_admin":
        raise HTTPException(403, "Cannot deactivate super admin")

    target.is_active = False
    await log_activity(db, "user.deactivate", user.id, "user", user_id)
    await db.commit()
    return {"status": "deactivated"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    body: PasswordReset,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin sets a new password for a user (forgot-password flow)."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "User not found")
    if target.role == "super_admin" and user.role != "super_admin":
        raise HTTPException(403, "Cannot reset super admin password")

    from ..auth import hash_password
    target.hashed_password = hash_password(body.new_password)
    await log_activity(db, "user.reset_password", user.id, "user", user_id)
    await db.commit()
    return {"status": "ok", "message": "Password reset"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin deletes a user (soft deactivate so historical records stay intact)."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == user.id:
        raise HTTPException(400, "Cannot delete yourself")
    if target.role == "super_admin" and user.role != "super_admin":
        raise HTTPException(403, "Cannot delete super admin")

    target.is_active = False
    await log_activity(db, "user.delete", user.id, "user", user_id, {
        "username": target.username,
    })
    await db.commit()
    return {"status": "ok", "message": "User deactivated", "user_id": user_id}


# ── Class Management ────────────────────────────────────────────────

# ── Courses + sections from CSV (#32) ───────────────────────────────

@router.get("/classes/import-template.csv")
async def class_import_template():
    """Example file with every column. Public: it contains no data."""
    return Response(CLASS_TEMPLATE, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="impress-classes-template.csv"'})


@router.post("/classes/import", response_model=ClassImportReport)
async def import_classes_csv(
    file: UploadFile = File(...),
    mode: str = Query("create", pattern="^(create|update)$",
                      description="create: new sections only; update: also change existing ones"),
    dry_run: bool = Query(True, description="validate only; pass false to store"),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create courses and their sections from a CSV. All-or-nothing: any
    invalid row means nothing is stored (422 with the report). Existing
    sections are skipped in create mode and only updated in update mode."""
    raw = await read_upload(file)
    report = await plan_class_import(db, raw, mode)
    if dry_run:
        return report
    if report.invalid:
        raise HTTPException(422, {"message": f"{report.invalid} invalid row(s); nothing was imported",
                                  "report": report.model_dump()})
    await apply_class_import(db, report, user)
    await log_activity(db, "class.csv_import", user.id, "class", None, {
        "mode": mode, "created": report.create, "updated": report.update,
        "new_courses": report.new_courses, "skipped": report.duplicate,
        "file_sha256": hashlib.sha256(raw).hexdigest(), "filename": file.filename or "",
    })
    try:
        await commit_or_conflict(db, "The classes changed while importing; check again and retry")
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(503, "Database error; nothing was imported")
    report.imported = report.create + report.update
    report.skipped = report.total - report.imported
    report.committed = True
    return report


@router.get("/classes/export.csv")
async def export_classes_csv(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Every course section in the import layout. Cells that would start a
    spreadsheet formula are prefixed with ' (formula injection)."""
    courses = {c.id: c for c in (await db.execute(select(Course))).scalars()}
    classes = list((await db.execute(select(ClassSession))).scalars())
    usernames = {u.id: u.username for u in (await db.execute(select(User))).scalars()}
    body, omitted = export_rows(courses, classes, usernames)
    return Response(body, media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": 'attachment; filename="impress-classes.csv"',
        "X-Omitted-Classes": str(omitted)})


@router.post("/classes", response_model=ClassResponse, status_code=201)
async def admin_create_class(
    body: ClassCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a classroom (course section): picks course, faculty, schedule, location."""
    if not body.code or not body.code.strip():
        raise HTTPException(400, "Classroom code is required")
    if body.classroom_code:
        exists = await db.execute(
            select(ClassSession.id).where(ClassSession.classroom_code == body.classroom_code.strip())
        )
        if exists.scalar_one_or_none():
            raise HTTPException(400, "Room label is already in use by another classroom")

    # Faculty: prefer the many-to-many list, fall back to single teacher_id.
    selected_ids = list(dict.fromkeys(body.teacher_ids or ([body.teacher_id] if body.teacher_id else [])))
    teacher_id = selected_ids[0] if selected_ids else user.id
    schedule = [s.model_dump() if hasattr(s, "model_dump") else s for s in (body.meeting_schedule or [])]
    warnings = await find_schedule_conflicts(
        db, teacher_id, schedule, body.location,
        term=body.term, year=body.year,
        start_date=body.start_date, end_date=body.end_date,
    )

    cls = ClassSession(
        name=body.name,
        subject=body.subject,
        code=body.code.strip(),
        teacher_id=teacher_id,
        created_by=user.id,
        course_id=body.course_id,
        course_section=body.course_section,
        term=body.term,
        year=body.year,
        start_date=body.start_date,
        end_date=body.end_date,
        meeting_schedule=schedule,
        location=body.location,
        capacity=body.capacity,
        classroom_code=(body.classroom_code or "").strip() or None,
    )
    await ensure_section_free(db, body.course_id, body.course_section)
    if selected_ids:
        rows = await db.execute(select(User).where(User.id.in_(selected_ids), User.role == "teacher"))
        teachers = list(rows.scalars().all())
        if len(teachers) != len(set(selected_ids)):
            raise HTTPException(400, "One or more selected faculty are not valid teachers")
        cls.faculty = teachers
    db.add(cls)
    try:
        await db.flush()
        await log_activity(db, "class.create", user.id, "class", cls.id, {
            "name": body.name,
            "course_id": body.course_id,
            "course_section": body.course_section,
            "term": body.term,
            "year": body.year,
            "location": body.location,
        })
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Classroom code is already in use by another classroom")
    cls = await _reload_class(db, cls.id)
    student_count = await _count_students(db, cls.id)
    return _class_to_response(cls, student_count, warnings=warnings)


@router.post("/classes/{class_id}/assign-teacher", response_model=ClassResponse)
async def assign_teacher(
    class_id: int,
    body: ClassAssignTeacher,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin assigns a teacher to a class."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    teacher_result = await db.execute(
        select(User).where(User.id == body.teacher_id, User.role == "teacher")
    )
    teacher = teacher_result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(404, "Teacher not found or user is not a teacher")

    old_teacher = cls.teacher_id
    warnings = await find_schedule_conflicts(
        db, body.teacher_id, cls.meeting_schedule or [],
        cls.location or "", exclude_class_id=class_id,
        term=cls.term or "", year=cls.year,
        start_date=cls.start_date, end_date=cls.end_date,
    )
    cls.teacher_id = body.teacher_id
    await log_activity(db, "class.assign_teacher", user.id, "class", class_id, {
        "old_teacher_id": old_teacher,
        "new_teacher_id": body.teacher_id,
        "teacher_name": teacher.full_name or teacher.username,
    })
    await db.commit()

    cls = await _reload_class(db, class_id)
    student_count = await _count_students(db, class_id)
    return _class_to_response(cls, student_count, warnings=warnings)


@router.get("/classes", response_model=list[ClassResponse])
async def admin_list_classes(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin sees all classes."""
    result = await db.execute(select(ClassSession).order_by(ClassSession.id.desc()))
    classes = result.scalars().all()
    out = []
    for cls in classes:
        student_count = await _count_students(db, cls.id)
        out.append(_class_to_response(cls, student_count))
    return out


@router.put("/classes/{class_id}", response_model=ClassResponse)
async def admin_update_class(
    class_id: int,
    body: ClassUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin edits a classroom's name, code, room label, schedule, capacity, etc."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    updates = body.model_dump(exclude_unset=True)
    schedule = updates.pop("meeting_schedule", None)
    if schedule is not None:
        updates["meeting_schedule"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in schedule]

    # Multi-faculty: replace the full faculty set; first selected becomes primary teacher.
    teacher_ids = updates.pop("teacher_ids", None)
    if teacher_ids is not None:
        ids = list(dict.fromkeys(t for t in teacher_ids if t))
        rows = await db.execute(select(User).where(User.id.in_(ids)))
        teachers = list(rows.scalars().all())
        if len(teachers) != len(ids):
            raise HTTPException(400, "One or more selected faculty are not valid teachers")
        cls.faculty = teachers
        if teachers:
            cls.teacher_id = teachers[0].id

    # Room label edits must stay unique across classrooms (excluding this one).
    room = updates.get("classroom_code")
    if room is not None:
        room = room.strip()
        updates["classroom_code"] = room or None
        exists = await db.execute(
            select(ClassSession.id).where(
                ClassSession.classroom_code == room, ClassSession.id != class_id
            )
        )
        if room and exists.scalar_one_or_none():
            raise HTTPException(400, "Room label is already in use by another classroom")

    if "course_id" in updates or "course_section" in updates:
        await ensure_section_free(db, updates.get("course_id", cls.course_id),
                                  updates.get("course_section", cls.course_section), exclude_id=class_id)

    for field, value in updates.items():
        setattr(cls, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Classroom code is already in use by another classroom")
    await db.refresh(cls)
    student_count = await _count_students(db, cls.id)
    return _class_to_response(cls, student_count)


@router.delete("/classes/{class_id}")
async def admin_delete_class(
    class_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin permanently deletes a classroom along with its dependent records."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    # The class row holds the FK to its device node (`ClassSession.device_id`);
    # deleting the class simply drops that link. The node row itself is preserved.
    cls_id, name = cls.id, cls.name
    await delete_class_records(db, cls_id)

    await log_activity(db, "class.delete", user.id, "class", cls_id, {"name": name})
    await db.commit()
    return {"status": "ok", "message": "Class deleted", "class_id": cls_id}


@router.put("/classes/{class_id}/faculty", response_model=ClassResponse)
async def admin_set_class_faculty(
    class_id: int,
    body: ClassFacultyUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Replace the set of faculty teaching a class (many-to-many)."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    teachers = await db.execute(select(User).where(User.id.in_(body.teacher_ids or [])))
    faculty = list(teachers.scalars().all())
    cls.faculty = faculty  # replaces the many-to-many set

    await log_activity(db, "class.faculty", user.id, "class", class_id,
                       {"teacher_ids": [f.id for f in faculty]})
    await db.commit()
    await db.refresh(cls)
    student_count = await _count_students(db, cls.id)
    return _class_to_response(cls, student_count)


# ── CSV Import for Class Students ─────────────────────────────────────

@router.post("/classes/{class_id}/import-students", response_model=CsvImportResult)
async def admin_import_students_csv(
    class_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Import students from CSV and enroll them into a specific class.
    Columns: roll_number, student_name, email, phone, program,
    enrollment_year, graduation_year, device_mac
    """
    # Verify class exists
    cls = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    if not cls.scalar_one_or_none():
        raise HTTPException(404, "Class not found")

    # Reuse the students router logic
    from ..routers.students import import_students_csv
    return await import_students_csv(file, class_session_id=class_id, user=user, db=db)


@router.get("/activity", response_model=list[ActivityLogResponse])
async def get_activity_logs(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    entity_type: str = Query("", description="Filter by entity type"),
):
    """View activity history."""
    q = select(ActivityLog, User.username).outerjoin(User, ActivityLog.user_id == User.id)
    if entity_type:
        q = q.where(ActivityLog.entity_type == entity_type)
    q = q.order_by(ActivityLog.timestamp.desc()).limit(limit)
    result = await db.execute(q)
    rows = result.all()
    return [
        ActivityLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username or "",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details or {},
            timestamp=log.timestamp,
        )
        for log, username in rows
    ]


# ── Student Registration & Enrollment ────────────────────────────────

def _student_response(s: Student) -> StudentResponse:
    return StudentResponse(
        id=s.id,
        roll_number=s.roll_number,
        student_name=s.student_name,
        email=s.email,
        phone=s.phone,
        program=s.program,
        enrollment_year=s.enrollment_year,
        graduation_year=s.graduation_year,
        device_mac=s.device_mac,
        is_active=s.is_active,
        registered_at=s.registered_at,
    )


@router.post("/students", response_model=StudentResponse, status_code=201)
async def register_student(
    body: StudentRegister,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a universal Student and optionally enroll them in a class."""
    dup = await db.execute(select(Student).where(Student.roll_number == body.roll_number))
    if dup.scalar_one_or_none():
        raise HTTPException(400, f"Roll number {body.roll_number!r} already exists")

    student = Student(
        roll_number=body.roll_number,
        student_name=body.student_name,
        email=body.email,
        phone=body.phone,
        program=body.program,
        enrollment_year=body.enrollment_year,
        graduation_year=body.graduation_year,
        device_mac=body.device_mac or None,
        registered_by=user.id,
    )
    db.add(student)
    await db.flush()

    if body.class_session_id:
        await _enroll_student(db, student.id, body.class_session_id, user, log=False)

    await log_activity(db, "student.create", user.id, "student", student.id, {
        "student_name": student.student_name,
        "roll_number": student.roll_number,
        "class_id": body.class_session_id,
    })
    await db.commit()
    await db.refresh(student)
    return _student_response(student)


@router.post("/students/bulk", response_model=list[StudentResponse], status_code=201)
async def bulk_register_students(
    body: BulkStudentRegister,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Bulk-register universal students, optionally enrolling in a class."""
    registered = []
    for s in body.students:
        dup = await db.execute(select(Student).where(Student.roll_number == s.roll_number))
        if dup.scalar_one_or_none():
            raise HTTPException(400, f"Roll number {s.roll_number!r} already exists")
        student = Student(
            roll_number=s.roll_number,
            student_name=s.student_name,
            email=s.email,
            phone=s.phone,
            program=s.program,
            enrollment_year=s.enrollment_year,
            graduation_year=s.graduation_year,
            device_mac=s.device_mac or None,
            registered_by=user.id,
        )
        db.add(student)
        await db.flush()
        if body.class_session_id:
            await _enroll_student(db, student.id, body.class_session_id, user, log=False)
        registered.append(student)

    await log_activity(db, "student.bulk_create", user.id, "student", None, {
        "count": len(registered),
        "class_id": body.class_session_id,
    })
    await db.commit()
    for s in registered:
        await db.refresh(s)
    return [_student_response(s) for s in registered]


async def _enroll_student(
    db: AsyncSession, student_id: int, class_id: int, user: User, log: bool = True
) -> StudentEnrollment:
    """Link an existing student to a class (with role/ownership checks)."""
    cls_res = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if user.role == "teacher" and cls.teacher_id != user.id:
        raise HTTPException(403, "You can only manage students in your own classes")

    student_res = await db.execute(select(Student).where(Student.id == student_id))
    student = student_res.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    if not student.is_active:
        raise HTTPException(400, "Student is deactivated")

    exists = await db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.class_session_id == class_id,
            StudentEnrollment.student_id == student_id,
        )
    )
    existing = exists.scalar_one_or_none()
    if existing:
        if not existing.is_active:
            existing.is_active = True
        return existing

    enrollment = StudentEnrollment(
        class_session_id=class_id,
        student_id=student_id,
        enrolled_by=user.id,
    )
    db.add(enrollment)
    await db.flush()
    if log:
        await log_activity(db, "class.enroll", user.id, "student", student_id, {
            "class_id": class_id,
            "student_name": student.student_name,
            "roll_number": student.roll_number,
        })
    return enrollment


@router.post("/classes/{class_id}/enroll", response_model=StudentResponse)
async def enroll_student(
    class_id: int,
    body: StudentEnroll,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enroll an existing student into a classroom."""
    await _enroll_student(db, body.student_id, class_id, user)
    await db.commit()
    res = await db.execute(select(Student).where(Student.id == body.student_id))
    return _student_response(res.scalar_one())


@router.post("/classes/{class_id}/enroll-bulk")
async def enroll_students_bulk(
    class_id: int,
    body: dict,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enroll a list of existing student ids into a classroom."""
    student_ids = body.get("student_ids", [])
    if not student_ids:
        raise HTTPException(400, "No student ids provided")
    for sid in student_ids:
        await _enroll_student(db, sid, class_id, user, log=False)
    await log_activity(db, "class.enroll_bulk", user.id, "class", class_id, {
        "count": len(student_ids),
    })
    await db.commit()
    return {"status": "enrolled", "count": len(student_ids)}


@router.delete("/classes/{class_id}/unenroll/{student_id}")
async def unenroll_student(
    class_id: int,
    student_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a student from a classroom."""
    cls_res = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if user.role == "teacher" and cls.teacher_id != user.id:
        raise HTTPException(403, "You can only manage students in your own classes")

    res = await db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.class_session_id == class_id,
            StudentEnrollment.student_id == student_id,
        )
    )
    enrollment = res.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(404, "Student not enrolled in this class")

    enrollment.is_active = False
    await log_activity(db, "class.unenroll", user.id, "student", student_id, {
        "class_id": class_id,
    })
    await db.commit()
    return {"status": "unenrolled"}


@router.get("/students/class/{class_id}", response_model=list[StudentResponse])
async def list_class_students(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all students enrolled in a class (roster)."""
    cls_result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = cls_result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if user.role == "teacher" and cls.teacher_id != user.id:
        raise HTTPException(403, "Access denied")

    result = await db.execute(
        select(StudentEnrollment, Student)
        .join(Student, StudentEnrollment.student_id == Student.id)
        .where(
            StudentEnrollment.class_session_id == class_id,
            StudentEnrollment.is_active == True,  # noqa: E712
        )
        .order_by(Student.roll_number)
    )
    rows = result.all()
    return [_student_response(s) for e, s in rows]


@router.get("/students/{student_id}/participation")
async def student_participation(
    student_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a student's participation summary across quizzes and polls."""
    from ..models import QuizAnswer, Quiz, PollVote, Poll, Attendance

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    # Classroom ids this student is enrolled in
    enroll_rows = await db.execute(
        select(StudentEnrollment.class_session_id)
        .where(StudentEnrollment.student_id == student_id, StudentEnrollment.is_active == True)  # noqa: E712
    )
    class_ids = [r[0] for r in enroll_rows.all()]

    if user.role == "teacher":
        verified = await db.execute(
            select(ClassSession).where(
                ClassSession.id.in_(class_ids),
                ClassSession.teacher_id == user.id,
            )
        )
        class_ids = [c.id for c in verified.scalars().all()]

    if not class_ids:
        return {
            "student": {"id": student.id, "name": student.student_name, "roll_number": student.roll_number},
            "quizzes_answered": 0, "total_quiz_answers": 0,
            "polls_voted": 0, "total_poll_votes": 0,
            "attendance_count": 0, "total_classes": 0,
            "quiz_details": [], "poll_details": [],
        }

    # Quiz answers — filtered to THIS student (enrollment-number identity)
    quiz_q = await db.execute(
        select(QuizAnswer, Quiz.title)
        .join(Quiz, QuizAnswer.quiz_id == Quiz.id)
        .where(Quiz.class_session_id.in_(class_ids), QuizAnswer.student_id == student_id)
    )
    quiz_answers = quiz_q.all()

    # Poll votes — filtered to THIS student
    poll_q = await db.execute(
        select(PollVote, Poll.title)
        .join(Poll, PollVote.poll_id == Poll.id)
        .where(Poll.class_session_id.in_(class_ids), PollVote.student_id == student_id)
    )
    poll_votes = poll_q.all()

    # Attendance — filtered to THIS student's enrollments
    stud_enr_ids = await db.execute(
        select(StudentEnrollment.id)
        .where(StudentEnrollment.student_id == student_id, StudentEnrollment.class_session_id.in_(class_ids))
    )
    enr_ids = [r[0] for r in stud_enr_ids.all()]
    att_q = await db.execute(
        select(Attendance)
        .where(Attendance.student_enrollment_id.in_(enr_ids))
    )
    attendance = att_q.scalars().all()

    return {
        "student": {
            "id": student.id,
            "name": student.student_name,
            "roll_number": student.roll_number,
        },
        "quizzes_answered": len(set(a.quiz_id for a, _ in quiz_answers)),
        "total_quiz_answers": len(quiz_answers),
        "polls_voted": len(set(v.poll_id for v, _ in poll_votes)),
        "total_poll_votes": len(poll_votes),
        "attendance_count": sum(1 for a in attendance if a.is_present),
        "total_classes": len(attendance),
        "quiz_details": [
            {"quiz_id": a.quiz_id, "quiz_title": title, "question_order": a.question_order, "selected_option": a.selected_option}
            for a, title in quiz_answers
        ],
        "poll_details": [
            {"poll_id": v.poll_id, "poll_title": title, "selected_option": v.selected_option}
            for v, title in poll_votes
        ],
    }


# ── Module / Device Management (R7 connectivity, R8 OTA) ─────────────

def _device_response(dev: EspDevice) -> DeviceResponse:
    """Map an EspDevice to its API response, attaching class context."""
    class_code = ""
    class_name = ""
    class_id = None
    if getattr(dev, "class_session", None):
        class_id = dev.class_session.id
        class_code = dev.class_session.code or ""
        class_name = dev.class_session.name or ""
    return DeviceResponse(
        id=dev.id,
        mac_address=dev.mac_address,
        device_name=dev.device_name or "",
        device_type=dev.device_type or "student",
        student_name=dev.student_name or "",
        battery_pct=dev.battery_pct or 0,
        rssi=dev.rssi or 0,
        is_connected=bool(dev.is_connected),
        gateway_id=dev.gateway_id,
        is_active=bool(dev.is_active),
        firmware_version=dev.firmware_version or "0.0.0",
        pending_version=dev.pending_version or "",
        ota_status=dev.ota_status or "idle",
        ota_requested_at=dev.ota_requested_at,
        verified_at=dev.verified_at,
        last_seen=dev.last_seen,
        class_id=class_id,
        class_code=class_code,
        class_name=class_name,
        student_count=dev.student_count or 0,
        free_heap=dev.free_heap or 0,
        total_flash=dev.total_flash or 0,
    )


@router.get("/modules", response_model=list[DeviceResponse])
async def admin_list_modules(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    device_type: str = Query("", description="Filter: c6 | s3 | student"),
):
    """View every node/device and its connectivity + firmware state."""
    q = select(EspDevice).order_by(EspDevice.device_type, EspDevice.id)
    if device_type:
        q = q.where(EspDevice.device_type == device_type)
    result = await db.execute(q)
    return [_device_response(d) for d in result.scalars().all()]


@router.get("/classes/{class_id}/devices", response_model=ClassDevicesResponse)
async def admin_class_devices(
    class_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Class node + the student devices logically linked to it (R8)."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")

    node = None
    if cls.device_id:
        dev_result = await db.execute(select(EspDevice).where(EspDevice.id == cls.device_id))
        node_dev = dev_result.scalar_one_or_none()
        if node_dev:
            node = _device_response(node_dev)

    if node and node.id:
        links = await db.execute(
            select(EspDevice).where(
                EspDevice.gateway_id == node.id,
                EspDevice.is_active == True,  # noqa: E712
            )
        )
        student_devices = [_device_response(d) for d in links.scalars().all()]
    else:
        student_devices = []

    return ClassDevicesResponse(node=node, student_devices=student_devices)


@router.get("/modules/{device_id}", response_model=DeviceResponse)
async def admin_get_module(
    device_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EspDevice).where(EspDevice.id == device_id))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Module not found")
    return _device_response(dev)


@router.post("/modules/{device_id}/access", response_model=DeviceResponse)
async def admin_toggle_module_access(
    device_id: int,
    body: ModuleAccessUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable a module — a disabled module stops accepting heartbeat/attendance."""
    result = await db.execute(select(EspDevice).where(EspDevice.id == device_id))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Module not found")

    dev.is_active = body.is_active
    await log_activity(db, "module.access", user.id, "device", device_id,
                       {"is_active": body.is_active, "mac": dev.mac_address})
    await db.commit()
    await db.refresh(dev)
    return _device_response(dev)


@router.post("/modules/{device_id}/ota", response_model=DeviceResponse)
async def admin_push_ota(
    device_id: int,
    body: ModuleOtaRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Queue a firmware version for a node; the device pulls it on its next poll (R8).

    For an S3 hub (usually off-WiFi), the backend can't wait for its next poll —
    it must be prompted.  We find the C6 gateway that relays this S3 and push a
    WebSocket `ota_update` command to it, which the C6 relays to the S3 over SPI.
    """
    result = await db.execute(select(EspDevice).where(EspDevice.id == device_id))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Module not found")
    # A push used to accept any version string and show 'downloading' while
    # the device then got 404 on download (#33).
    version = normalize_version(body.version)
    dt = (dev.device_type or "").lower()
    if not firmware_path(dt, version).is_file():
        raise HTTPException(404, f"No uploaded {dt or 'device'} firmware {version}; upload it first")
    body.version = version

    dev.pending_version = body.version
    dev.ota_status = "downloading"
    dev.ota_requested_at = istnow()
    await log_activity(db, "module.ota", user.id, "device", device_id,
                       {"to_version": body.version, "mac": dev.mac_address})
    await db.commit()
    await db.refresh(dev)

    # S3 hub: prompt its paired C6 so the prompt travels C6 → SPI → S3 → WiFi OTA.
    if (dev.device_type or "").lower() == "s3" and dev.gateway_id:
        c6_rs = await db.execute(select(EspDevice).where(EspDevice.id == dev.gateway_id))
        c6 = c6_rs.scalar_one_or_none()
        cls_id = None
        if c6 and c6.class_session:
            cls_id = c6.class_session.id
        elif dev.class_session:
            cls_id = dev.class_session.id

        if cls_id:
            await send_command_to_devices(
                cls_id,
                "ota_update",
                {"device_type": "s3", "version": body.version,
                 "mac_address": dev.mac_address},
            )
            await log_activity(db, "module.ota.prompt", user.id, "device",
                               dev.gateway_id, {"to_class": cls_id,
                                                "version": body.version})
            await db.commit()

    return _device_response(dev)


@router.post("/firmware/upload", response_model=DeviceResponse)
async def admin_upload_firmware(
    device_type: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload a firmware binary. Device type must be c6, s3, or student.
    The uploaded .bin is stored as <device_type>-<version>.bin and served
    by /api/device/firmware/download when the target device polls for OTA. """
    if device_type not in ("c6", "s3", "student"):
        raise HTTPException(400, "device_type must be c6 | s3 | student")

    await save_firmware(file, device_type, version)
    await log_activity(db, "firmware.upload", user.id, "firmware", 0,
                       {"device_type": device_type, "version": version})
    await db.commit()
    return DeviceResponse(
        id=0, mac_address="", device_name="", device_type=device_type,
        firmware_version=version, pending_version="", ota_status="uploaded"
    )


@router.post("/modules/{device_id}/verify", response_model=DeviceResponse)
async def admin_verify_module(
    device_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stamp a node as officially verified (checked/firmware confirmed)."""
    result = await db.execute(select(EspDevice).where(EspDevice.id == device_id))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Module not found")

    dev.verified_at = istnow()
    await log_activity(db, "module.verify", user.id, "device", device_id,
                       {"mac": dev.mac_address})
    await db.commit()
    await db.refresh(dev)
    return _device_response(dev)


@router.post("/modules/{node_id}/link-device", response_model=DeviceResponse)
async def admin_link_device(
    node_id: int,
    body: ModuleLinkDevice,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Logically connect a student device to a class/gateway node (R7)."""
    node_result = await db.execute(select(EspDevice).where(EspDevice.id == node_id))
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(404, "Gateway node not found")

    dev_result = await db.execute(select(EspDevice).where(EspDevice.id == body.device_id))
    dev = dev_result.scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Device not found")
    if dev.id == node_id:
        raise HTTPException(400, "A node cannot relay itself")

    dev.gateway_id = node_id
    dev.is_connected = True
    await log_activity(db, "module.link", user.id, "device", dev.id,
                       {"node_id": node_id, "mac": dev.mac_address})
    await db.commit()
    await db.refresh(dev)
    return _device_response(dev)


@router.post("/modules/{device_id}/unlink", response_model=DeviceResponse)
async def admin_unlink_device(
    device_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Detach a student device from its gateway (logical link, R7)."""
    result = await db.execute(select(EspDevice).where(EspDevice.id == device_id))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Module not found")

    dev.gateway_id = None
    dev.is_connected = False
    await log_activity(db, "module.unlink", user.id, "device", device_id,
                       {"mac": dev.mac_address})
    await db.commit()
    await db.refresh(dev)
    return _device_response(dev)


# ── Helpers ──────────────────────────────────────────────────────────

async def _reload_class(db: AsyncSession, class_id: int) -> ClassSession:
    """Re-select a class after mutation so selectin relationships load in the async context."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    return result.scalar_one()


async def _count_students(db: AsyncSession, class_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(StudentEnrollment)
        .where(StudentEnrollment.class_session_id == class_id, StudentEnrollment.is_active == True)  # noqa: E712
    )
    return result.scalar() or 0


def _class_to_response(cls: ClassSession, student_count: int, warnings: list | None = None) -> ClassResponse:
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
