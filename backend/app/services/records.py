"""Integrity-preserving multi-table operations shared by several routers.

Foreign keys are enforced (database.py), so every delete must first deal with
the rows that reference what it removes. Keeping these in one place stops the
teacher and admin paths from drifting apart (#41: the teacher class delete
failed with a NOT NULL error while the admin one worked).
"""

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Attendance, ClassSession, EspDevice, StudentModule, Poll, PollVote, Quiz, QuizAnswer, QuizQuestion, Student,
    StudentEnrollment, class_faculty,
)


async def ensure_section_free(db: AsyncSession, course_id: int | None, section: str | None,
                              exclude_id: int | None = None) -> None:
    """409 if another class already is this (course, section). Mirrors the
    partial unique index uq_class_sessions_course_section."""
    section = (section or "").strip()
    if course_id is None or not section:
        return
    q = select(ClassSession.id).where(ClassSession.course_id == course_id,
                                      ClassSession.course_section == section)
    if exclude_id is not None:
        q = q.where(ClassSession.id != exclude_id)
    if (await db.execute(q)).first() is not None:
        raise HTTPException(409, f"Section '{section}' already exists for this course")


async def delete_class_records(db: AsyncSession, class_id: int) -> None:
    """Delete a class and everything that belongs to it (not committed).

    Student modules linked to the class's enrollments are kept and unlinked;
    the class's gateway node row is kept (the link lives on the class row).
    """
    enrollments = select(StudentEnrollment.id).where(StudentEnrollment.class_session_id == class_id)
    await db.execute(update(EspDevice).where(EspDevice.student_enrollment_id.in_(enrollments))
                     .values(student_enrollment_id=None))
    quizzes = select(Quiz.id).where(Quiz.class_session_id == class_id)
    await db.execute(delete(QuizAnswer).where(QuizAnswer.quiz_id.in_(quizzes)))
    await db.execute(delete(QuizQuestion).where(QuizQuestion.quiz_id.in_(quizzes)))
    await db.execute(delete(Quiz).where(Quiz.class_session_id == class_id))
    polls = select(Poll.id).where(Poll.class_session_id == class_id)
    await db.execute(delete(PollVote).where(PollVote.poll_id.in_(polls)))
    await db.execute(delete(Poll).where(Poll.class_session_id == class_id))
    await db.execute(delete(Attendance).where(Attendance.class_session_id == class_id))
    await db.execute(delete(StudentEnrollment).where(StudentEnrollment.class_session_id == class_id))
    await db.execute(delete(class_faculty).where(class_faculty.c.class_session_id == class_id))
    await db.execute(update(StudentModule).where(StudentModule.class_session_id == class_id)
                     .values(class_session_id=None))
    await db.execute(delete(ClassSession).where(ClassSession.id == class_id))


async def erase_student(db: AsyncSession, student_id: int) -> None:
    """Permanently remove a student's identity (not committed).

    Their answers and votes stay, anonymised (student_id NULL), so completed
    quizzes and polls keep their totals; attendance and enrollments go; any
    student module linked to an enrollment is unlinked.
    """
    enrollments = select(StudentEnrollment.id).where(StudentEnrollment.student_id == student_id)
    await db.execute(update(QuizAnswer).where(QuizAnswer.student_id == student_id).values(student_id=None))
    await db.execute(update(PollVote).where(PollVote.student_id == student_id).values(student_id=None))
    await db.execute(update(EspDevice).where(EspDevice.student_enrollment_id.in_(enrollments))
                     .values(student_enrollment_id=None))
    await db.execute(delete(Attendance).where(Attendance.student_enrollment_id.in_(enrollments)))
    await db.execute(delete(StudentEnrollment).where(StudentEnrollment.student_id == student_id))
    roll = await db.scalar(select(Student.roll_number).where(Student.id == student_id))
    if roll:     # the module stays in the inventory, no longer tied to them
        await db.execute(update(StudentModule).where(StudentModule.enrollment_number == roll)
                         .values(enrollment_number=""))
    await db.execute(delete(Student).where(Student.id == student_id))
