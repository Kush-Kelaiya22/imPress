"""Student registry router: universal student records shared across classrooms."""

import csv
import io
import re
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, ClassSession, Student, StudentEnrollment
from ..schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentRegister, BulkStudentRegister,
    CsvImportResult, CsvImportError,
)
from ..auth import require_teacher_or_admin
from ..services.records import erase_student
from ..activity import log_activity

router = APIRouter(prefix="/api/students", tags=["students"])


def _to_response(s: Student) -> StudentResponse:
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


async def _create_one(
    db: AsyncSession, body: StudentRegister, user: User
) -> Student:
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
    return student


@router.post("/", response_model=StudentResponse, status_code=201)
async def create_student(
    body: StudentCreate,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin or faculty creates a student in the universal registry."""
    student = await _create_one(db, StudentRegister(**body.model_dump()), user)
    await log_activity(db, "student.create", user.id, "student", student.id, {
        "roll_number": student.roll_number,
        "student_name": student.student_name,
        "program": student.program,
    })
    await db.commit()
    await db.refresh(student)
    return _to_response(student)


@router.post("/bulk", response_model=list[StudentResponse], status_code=201)
async def bulk_create_students(
    body: BulkStudentRegister,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create many students at once (optionally enroll in a class)."""
    created = []
    for item in body.students:
        student = await _create_one(db, StudentRegister(**item.model_dump()), user)
        created.append(student)

    # Optional: enroll all into a class
    section = None
    if body.class_session_id:
        res = await db.execute(select(ClassSession).where(ClassSession.id == body.class_session_id))
        section = res.scalar_one_or_none()
        if not section:
            raise HTTPException(404, "Class not found")
        for student in created:
            exists = await db.execute(
                select(StudentEnrollment).where(
                    StudentEnrollment.class_session_id == body.class_session_id,
                    StudentEnrollment.student_id == student.id,
                )
            )
            if not exists.scalar_one_or_none():
                db.add(StudentEnrollment(
                    class_session_id=body.class_session_id,
                    student_id=student.id,
                    enrolled_by=user.id,
                ))

    await log_activity(db, "student.bulk_create", user.id, "student", None, {
        "count": len(created),
        "class_id": body.class_session_id,
    })
    await db.commit()
    for s in created:
        await db.refresh(s)
    return [_to_response(s) for s in created]


@router.get("/", response_model=list[StudentResponse])
async def list_students(
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
    search: str = Query("", description="Match roll number or name"),
):
    q = select(Student).order_by(Student.roll_number)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(or_(
            Student.roll_number.ilike(like),
            Student.student_name.ilike(like),
        ))
    result = await db.execute(q)
    return [_to_response(s) for s in result.scalars().all()]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    return _to_response(student)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    body: StudentUpdate,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    changed = {}
    for field in ("student_name", "email", "phone", "program", "enrollment_year",
                  "graduation_year", "is_active"):
        val = getattr(body, field)
        if val is not None:
            setattr(student, field, val)
            changed[field] = val
    if body.device_mac is not None:
        student.device_mac = body.device_mac or None
        changed["device_mac"] = student.device_mac

    await log_activity(db, "student.update", user.id, "student", student_id, changed)
    await db.commit()
    await db.refresh(student)
    return _to_response(student)


@router.delete("/{student_id}")
async def deactivate_student(
    student_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a student (deactivate)."""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    student.is_active = False
    await log_activity(db, "student.deactivate", user.id, "student", student_id)
    await db.commit()
    return {"status": "deactivated"}


@router.delete("/{student_id}/hard-delete")
async def hard_delete_student(
    student_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a student record and its related rows.
    Requires admin (removing records is irreversible).
    """
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(403, "Only admins can permanently delete a student record")

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    roll = student.roll_number
    name = student.student_name
    # answers/votes stay (anonymised) so completed results keep their totals
    await erase_student(db, student_id)

    await log_activity(db, "student.hard_delete", user.id, "student", student_id, {
        "roll_number": roll,
        "student_name": name,
    })
    await db.commit()
    return {"status": "deleted", "roll_number": roll}


@router.get("/{student_id}/classes")
async def student_classes(
    student_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Which classrooms is this student enrolled in?"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    rows = await db.execute(
        select(StudentEnrollment, ClassSession)
        .join(ClassSession, StudentEnrollment.class_session_id == ClassSession.id)
        .where(StudentEnrollment.student_id == student_id, StudentEnrollment.is_active == True)  # noqa: E712
    )
    out = []
    for enrollment, cls in rows.all():
        course = cls.course
        out.append({
            "enrollment_id": enrollment.id,
            "class_id": cls.id,
            "course_code": course.code if course else "",
            "course_name": course.name if course else cls.name,
            "subject": cls.subject,
            "course_section": cls.course_section,
            "term": cls.term,
            "year": cls.year,
            "meeting_schedule": cls.meeting_schedule or [],
            "location": cls.location,
            "teacher_name": cls.teacher.full_name or cls.teacher.username if cls.teacher else "",
            "is_active": cls.is_active,
        })
    return out


# ── CSV Import ──────────────────────────────────────────────────────────

# Exactly 7 required columns — all compulsory, no extras accepted
_CSV_REQUIRED_COLUMNS = [
    "roll_number", "student_name", "email", "phone",
    "program", "enrollment_year", "graduation_year",
]

# Email validation: must contain @, local part non-empty, domain has at least one dot
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Phone validation: digits, hyphens, parens, plus, spaces — 7 to 15 chars
_PHONE_RE = re.compile(r"^[\d\-+() ]{7,15}$")


@router.post("/import", response_model=CsvImportResult)
async def import_students_csv(
    file: UploadFile = File(...),
    class_session_id: int = Form(None),
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Import students from CSV.
    Required columns (all compulsory): roll_number, student_name, email, phone,
    program, enrollment_year, graduation_year.
    No other fields are accepted or generated.
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

    # Normalize headers to lowercase, strip whitespace
    fieldnames = [h.strip().lower() for h in reader.fieldnames]
    reader.fieldnames = fieldnames

    # Require exactly the 7 known columns (order-insensitive)
    field_set = set(fieldnames)
    required_set = set(_CSV_REQUIRED_COLUMNS)
    if field_set != required_set:
        missing = required_set - field_set
        extra = field_set - required_set
        parts = []
        if missing: parts.append(f"missing: {', '.join(sorted(missing))}")
        if extra:   parts.append(f"unexpected columns: {', '.join(sorted(extra))}")
        raise HTTPException(400, "CSV must contain exactly 7 columns (" + "; ".join(parts) + ")")

    roll_re = re.compile(r"^[A-Za-z0-9]{10}$")
    seen_rolls: set[str] = set()
    valid_rows: list[dict] = []
    errors: list[CsvImportError] = []

    for row_idx, row in enumerate(reader, start=2):  # 1-based, +1 for header
        # Skip blank rows
        if not all(v.strip() == "" for v in row.values()):
            # At least one non-empty value: all 7 must be filled
            pass

        # ── All 7 fields are compulsory — any blank → reject row ──
        roll        = (row.get("roll_number")    or "").strip()
        name        = (row.get("student_name")   or "").strip()
        email_raw   = (row.get("email")          or "").strip()
        phone_raw   = (row.get("phone")          or "").strip()
        program     = (row.get("program")         or "").strip()
        ey_raw      = (row.get("enrollment_year") or "").strip()
        gy_raw      = (row.get("graduation_year") or "").strip()

        # Skip fully blank rows
        if not any([roll, name, email_raw, phone_raw, program, ey_raw, gy_raw]):
            continue

        # Check all fields present and non-empty
        blanks = [col for col, val in zip(_CSV_REQUIRED_COLUMNS,
                   [roll, name, email_raw, phone_raw, program, ey_raw, gy_raw])
                  if not val]
        if blanks:
            errors.append(CsvImportError(
                row=row_idx, roll_number=roll or "(empty)",
                error=f"missing required field(s): {', '.join(blanks)}",
            ))
            continue

        # ── Format validation per field ───────────────────────────────
        # Roll number: exactly 10 alphanumeric, uppercased
        roll = roll.upper()
        if not roll_re.match(roll):
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="roll_number must be exactly 10 alphanumeric characters"))
            continue
        if roll in seen_rolls:
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="duplicate roll_number within CSV"))
            continue

        # Student name: non-empty already checked, basic length check
        if len(name) > 128:
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="student_name must be 128 characters or fewer"))
            continue

        # Email: must look like user@domain.tld
        if not _EMAIL_RE.match(email_raw):
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="email is invalid (must be valid format like name@domain.com)"))
            continue

        # Phone: digits, hyphens, parens, plus, spaces — 7 to 15 chars
        if not _PHONE_RE.match(phone_raw):
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="phone must be 7–15 characters (digits, hyphens, +, parens, spaces only)"))
            continue

        # Program: non-empty already checked
        if len(program) > 128:
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="program must be 128 characters or fewer"))
            continue

        # Enrollment year: must be integer, 2000–2099
        try:
            enrollment_year = int(ey_raw)
        except ValueError:
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="enrollment_year must be a valid integer"))
            continue
        if not (2000 <= enrollment_year <= 2099):
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="enrollment_year must be between 2000 and 2099"))
            continue

        # Graduation year: must be integer, 2000–2099, >= enrollment_year
        try:
            graduation_year = int(gy_raw)
        except ValueError:
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="graduation_year must be a valid integer"))
            continue
        if not (2000 <= graduation_year <= 2099):
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="graduation_year must be between 2000 and 2099"))
            continue
        if graduation_year < enrollment_year:
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="graduation_year must be >= enrollment_year"))
            continue

        # Check DB for existing
        exists = await db.execute(select(Student).where(Student.roll_number == roll))
        if exists.scalar_one_or_none():
            errors.append(CsvImportError(row=row_idx, roll_number=roll,
                error="roll_number already exists in database"))
            continue

        seen_rolls.add(roll)

        valid_rows.append({
            "roll_number": roll,
            "student_name": name,
            "email": email_raw,
            "phone": phone_raw,
            "program": program,
            "enrollment_year": enrollment_year,
            "graduation_year": graduation_year,
            "class_session_id": class_session_id,
        })

    # Insert valid students
    inserted = 0
    for v in valid_rows:
        student = Student(
            roll_number=v["roll_number"],
            student_name=v["student_name"],
            email=v["email"],
            phone=v["phone"],
            program=v["program"],
            enrollment_year=v["enrollment_year"],
            graduation_year=v["graduation_year"],
            registered_by=user.id,
        )
        db.add(student)
        await db.flush()

        # Enroll in class if specified
        class_id = v["class_session_id"]
        if class_id:
            cls = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
            cls_obj = cls.scalar_one_or_none()
            if cls_obj:
                enrolled = await db.execute(
                    select(StudentEnrollment).where(
                        StudentEnrollment.class_session_id == class_id,
                        StudentEnrollment.student_id == student.id,
                    )
                )
                if not enrolled.scalar_one_or_none():
                    db.add(StudentEnrollment(
                        class_session_id=class_id,
                        student_id=student.id,
                        enrolled_by=user.id,
                    ))

        inserted += 1

    await log_activity(db, "student.csv_import", user.id, "student", None, {
        "inserted": inserted,
        "skipped": len(errors),
        "class_session_id": class_session_id,
    })
    await db.commit()

    return CsvImportResult(
        inserted=inserted,
        skipped=errors,
        total_rows=len(valid_rows) + len(errors),
    )


@router.post("/classes/{class_id}/import-students", response_model=CsvImportResult)
async def import_students_to_class_csv(
    class_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Import students and enroll them into a specific class.
    Reuses the same CSV logic but forces class_session_id = class_id.
    """
    # Verify class exists
    cls = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    if not cls.scalar_one_or_none():
        raise HTTPException(404, "Class not found")

    return await import_students_csv(file, class_session_id=class_id, user=user, db=db)