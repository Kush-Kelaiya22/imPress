"""Quiz router: create, start, stop, answer — with planned/impromptu modes and timing."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, ClassSession, Quiz, QuizQuestion, QuizAnswer
from ..schemas import QuizCreate, QuizResponse, QuizAnswerSubmit
from ..auth import get_current_user, require_teacher_or_admin
from ..ws.manager import manager
from ..activity import log_activity
from ..timeutil import istnow

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


async def _verify_class_access(class_id: int, user: User, db: AsyncSession) -> ClassSession:
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if user.role == "teacher" and cls.teacher_id != user.id:
        raise HTTPException(403, "You don't have access to this class")
    return cls


def _quiz_response(quiz: Quiz) -> QuizResponse:
    return QuizResponse(
        id=quiz.id,
        class_session_id=quiz.class_session_id,
        title=quiz.title,
        status=quiz.status,
        quiz_mode=quiz.quiz_mode,
        timing_mode=quiz.timing_mode,
        question_time_limit=quiz.question_time_limit or 0,
        total_time_limit=quiz.total_time_limit or 0,
        current_question=quiz.current_question or 0,
        is_live=quiz.is_live or False,
        question_count=len(quiz.questions) if quiz.questions else 0,
        created_at=quiz.created_at,
        started_at=quiz.started_at,
    )


# ── Create Quiz ─────────────────────────────────────────────────────

@router.post("/", response_model=QuizResponse, status_code=201)
async def create_quiz(
    body: QuizCreate,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a quiz. Can be planned (started later) or impromptu (started immediately)."""
    cls = await _verify_class_access(body.class_session_id, user, db)

    quiz = Quiz(
        class_session_id=body.class_session_id,
        title=body.title,
        quiz_mode=body.quiz_mode,
        timing_mode=body.timing_mode,
        question_time_limit=body.question_time_limit,
        total_time_limit=body.total_time_limit,
        status="draft",
        is_live=False,
    )

    # Impromptu: create and start immediately
    if body.quiz_mode == "impromptu":
        quiz.status = "active"
        quiz.is_live = True
        quiz.current_question = 0
        quiz.started_at = istnow()

    db.add(quiz)
    await db.flush()

    for i, q in enumerate(body.questions):
        question = QuizQuestion(
            quiz_id=quiz.id,
            order_num=i,
            question_text=q.question_text,
            options=q.options,
            correct_option=q.correct_option,
        )
        db.add(question)

    await log_activity(db, "quiz.create", user.id, "quiz", quiz.id, {
        "title": body.title,
        "quiz_mode": body.quiz_mode,
        "timing_mode": body.timing_mode,
        "class_id": body.class_session_id,
        "question_count": len(body.questions),
    })
    await db.commit()
    await db.refresh(quiz)

    # If impromptu, broadcast question 0 to devices
    if quiz.is_live:
        await _broadcast_question(quiz, cls.id)

    return _quiz_response(quiz)


# ── List Quizzes ────────────────────────────────────────────────────

@router.get("/class/{class_id}", response_model=list[QuizResponse])
async def list_quizzes(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    await _verify_class_access(class_id, user, db)
    result = await db.execute(
        select(Quiz).where(Quiz.class_session_id == class_id).order_by(Quiz.id.desc())
    )
    return [_quiz_response(q) for q in result.scalars().all()]


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    await _verify_class_access(quiz.class_session_id, user, db)   # same rule as the class itself
    return _quiz_response(quiz)


# ── Start Quiz (planned → live) ─────────────────────────────────────

@router.post("/{quiz_id}/start", response_model=QuizResponse)
async def start_quiz(
    quiz_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Make a planned quiz live — sends question 0 to all devices."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    cls = await _verify_class_access(quiz.class_session_id, user, db)

    if quiz.status == "active":
        raise HTTPException(400, "Quiz is already active")

    quiz.status = "active"
    quiz.is_live = True
    quiz.current_question = 0
    quiz.started_at = istnow()

    await log_activity(db, "quiz.start", user.id, "quiz", quiz_id, {
        "title": quiz.title,
        "class_id": quiz.class_session_id,
    })
    await db.commit()
    await db.refresh(quiz)

    await _broadcast_question(quiz, cls.id)
    return _quiz_response(quiz)


# ── Stop Quiz ───────────────────────────────────────────────────────

@router.post("/{quiz_id}/stop", response_model=QuizResponse)
async def stop_quiz(
    quiz_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    cls = await _verify_class_access(quiz.class_session_id, user, db)

    quiz.status = "completed"
    quiz.is_live = False
    quiz.ended_at = istnow()

    await log_activity(db, "quiz.stop", user.id, "quiz", quiz_id, {"title": quiz.title})
    await db.commit()
    await db.refresh(quiz)

    # Broadcast quiz_ended to devices
    await manager.broadcast_to_class(cls.id, {
        "type": "quiz_ended",
        "quiz_id": quiz_id,
        "title": quiz.title,
    })

    return _quiz_response(quiz)


# ── Next Question (manual timing mode) ──────────────────────────────

@router.post("/{quiz_id}/next", response_model=QuizResponse)
async def next_question(
    quiz_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Advance to the next question. Used in manual and per_question timing modes."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    cls = await _verify_class_access(quiz.class_session_id, user, db)

    if quiz.status != "active":
        raise HTTPException(400, "Quiz is not active")

    next_idx = (quiz.current_question or 0) + 1
    if next_idx >= len(quiz.questions):
        # No more questions — end quiz
        quiz.status = "completed"
        quiz.is_live = False
        quiz.ended_at = istnow()
        await db.commit()
        await db.refresh(quiz)

        await manager.broadcast_to_class(cls.id, {
            "type": "quiz_ended",
            "quiz_id": quiz_id,
            "title": quiz.title,
        })
        return _quiz_response(quiz)

    quiz.current_question = next_idx
    await db.commit()
    await db.refresh(quiz)

    await _broadcast_question(quiz, cls.id)
    return _quiz_response(quiz)


# ── Device Answers ──────────────────────────────────────────────────

@router.post("/{quiz_id}/answer")
async def submit_answer(
    quiz_id: int,
    body: QuizAnswerSubmit,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    if quiz.status != "active":
        raise HTTPException(400, "Quiz is not active")

    current_q = quiz.current_question or 0

    # Prevent duplicate answers for the same question
    existing = await db.execute(
        select(QuizAnswer).where(
            QuizAnswer.quiz_id == quiz_id,
            QuizAnswer.question_order == current_q,
            QuizAnswer.device_id == body.device_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already answered this question")

    answer = QuizAnswer(
        quiz_id=quiz_id,
        question_order=current_q,
        device_id=body.device_id,
        selected_option=body.selected_option,
        response_time_ms=body.response_time_ms,
    )
    db.add(answer)
    await db.commit()

    # Broadcast updated answer count
    count_result = await db.execute(
        select(QuizAnswer).where(
            QuizAnswer.quiz_id == quiz_id,
            QuizAnswer.question_order == current_q,
        )
    )
    total = len(count_result.scalars().all())

    cls_result = await db.execute(select(ClassSession).where(ClassSession.id == quiz.class_session_id))
    cls = cls_result.scalar_one_or_none()
    if cls:
        await manager.broadcast_to_class(cls.id, {
            "type": "quiz_answer",
            "quiz_id": quiz_id,
            "question_order": current_q,
            "total_answers": total,
            "device_id": body.device_id,
        })

    return {"status": "recorded"}


# ── Results ─────────────────────────────────────────────────────────

@router.get("/{quiz_id}/results")
async def quiz_results(
    quiz_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    await _verify_class_access(quiz.class_session_id, user, db)   # same rule as the class itself

    questions_result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_num)
    )
    questions = questions_result.scalars().all()

    results = []
    for q in questions:
        answers_result = await db.execute(
            select(QuizAnswer).where(
                QuizAnswer.quiz_id == quiz_id,
                QuizAnswer.question_order == q.order_num,
            )
        )
        answers = answers_result.scalars().all()

        option_counts = [0, 0, 0, 0, 0, 0]
        for a in answers:
            if 0 <= a.selected_option < 6:
                option_counts[a.selected_option] += 1

        results.append({
            "question_num": q.order_num,
            "question_text": q.question_text,
            "options": q.options,
            "correct_option": q.correct_option,
            "total_answers": len(answers),
            "option_counts": option_counts[:len(q.options)],
        })

    return {
        "quiz_id": quiz_id,
        "title": quiz.title,
        "status": quiz.status,
        "quiz_mode": quiz.quiz_mode,
        "timing_mode": quiz.timing_mode,
        "results": results,
    }


# ── Helpers ──────────────────────────────────────────────────────────

async def _broadcast_question(quiz: Quiz, class_id: int):
    """Send the current question to all devices in the class."""
    current_q = quiz.current_question or 0
    q = next((q for q in quiz.questions if q.order_num == current_q), None)
    if not q:
        return

    await manager.broadcast_to_class(class_id, {
        "type": "quiz_question",
        "quiz_id": quiz.id,
        "title": quiz.title,
        "question_order": q.order_num,
        "total_questions": len(quiz.questions),
        "question_text": q.question_text,
        "options": q.options,
        "timing_mode": quiz.timing_mode,
        "time_limit": quiz.question_time_limit if quiz.timing_mode == "per_question" else 0,
    })
