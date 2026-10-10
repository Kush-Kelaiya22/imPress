"""Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes
when their time is up, and refuse answers that arrive after it.

Durable: all timer state is in the quizzes table (`started_at`,
`question_started_at`), so a restart resumes where it left off. Idempotent:
every transition is a compare-and-set on (status, current_question), so the
teacher's Next/Stop and the timer can never both move the same question.
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Quiz
from ..timeutil import istnow
from ..ws.manager import manager

log = logging.getLogger(__name__)

TICK_S = 1
# Answers pressed just before the deadline still have to cross the mesh and
# the gateway's batch; accept them for this long after it.
GRACE_S = 2
TIMED_MODES = ("per_question", "total")


def deadline(quiz: Quiz) -> datetime | None:
    """When the current question (per_question) or the whole quiz (total)
    runs out; None for manual quizzes and a limit of 0 (no limit)."""
    if quiz.timing_mode == "per_question" and quiz.question_time_limit and quiz.question_started_at:
        return quiz.question_started_at + timedelta(seconds=quiz.question_time_limit)
    if quiz.timing_mode == "total" and quiz.total_time_limit and quiz.started_at:
        return quiz.started_at + timedelta(seconds=quiz.total_time_limit)
    return None


def answer_closed(quiz: Quiz, question_order: int, now: datetime) -> bool:
    """True when an answer to `question_order` arrives after its time ran out."""
    grace = timedelta(seconds=GRACE_S)
    if (quiz.timing_mode == "per_question" and quiz.question_time_limit
            and question_order < (quiz.current_question or 0)):
        # an earlier question closed when the current one went live
        return quiz.question_started_at is not None and now > quiz.question_started_at + grace
    end = deadline(quiz)
    return end is not None and now > end + grace


def time_limit_s(quiz: Quiz, now: datetime) -> int:
    """Seconds a module has for the question it is about to show: the
    per-question limit, or what is left of a total limit; 0 = no limit."""
    if quiz.timing_mode == "per_question":
        return quiz.question_time_limit or 0
    end = deadline(quiz)
    return max(1, math.ceil((end - now).total_seconds())) if end else 0


async def _transition(db: AsyncSession, quiz: Quiz, **values) -> bool:
    res = await db.execute(
        update(Quiz)
        .where(Quiz.id == quiz.id, Quiz.status == "active", Quiz.current_question == quiz.current_question)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    return res.rowcount == 1


async def advance(db: AsyncSession, quiz: Quiz, now: datetime | None = None) -> bool:
    """Move an active quiz to its next question, or complete it after the
    last one. False if the quiz already moved on (teacher or timer won)."""
    now = now or istnow()
    nxt = (quiz.current_question or 0) + 1
    if nxt >= len(quiz.questions):
        return await finish(db, quiz, now)
    return await _transition(db, quiz, current_question=nxt, question_started_at=now)


async def finish(db: AsyncSession, quiz: Quiz, now: datetime | None = None) -> bool:
    return await _transition(db, quiz, status="completed", is_live=False, ended_at=now or istnow())


async def broadcast(quiz: Quiz) -> None:
    """Tell the class what the quiz now shows: its current question, or its end."""
    if quiz.status != "active":
        await manager.broadcast_to_class(quiz.class_session_id, {
            "event": "quiz_end",  # device (C6) contract
            "type": "quiz_ended",
            "quiz_id": quiz.id,
            "title": quiz.title,
        })
        return
    current_q = quiz.current_question or 0
    q = next((q for q in quiz.questions if q.order_num == current_q), None)
    if not q:
        return
    limit = time_limit_s(quiz, istnow())
    await manager.broadcast_to_class(quiz.class_session_id, {
        "event": "quiz_question",  # device (C6) + React contract
        "type": "quiz_question",
        "quiz_id": quiz.id,
        "title": quiz.title,
        "question_order": q.order_num,
        "total_questions": len(quiz.questions),
        "question_text": q.question_text,
        "options": q.options,
        "timing_mode": quiz.timing_mode,
        "time_limit": limit,
        "time_limit_s": limit,
    })


async def tick(db: AsyncSession, now: datetime | None = None) -> list[Quiz]:
    """Advance or end every timed quiz whose time is up. The caller commits,
    then broadcasts the returned quizzes."""
    now = now or istnow()
    quizzes = (await db.execute(
        select(Quiz).where(Quiz.status == "active", Quiz.timing_mode.in_(TIMED_MODES)))).scalars().all()
    changed = []
    for quiz in quizzes:
        if quiz.timing_mode == "per_question" and quiz.question_time_limit and quiz.question_started_at is None:
            quiz.question_started_at = now      # started before this column existed: count from now
            continue
        end = deadline(quiz)
        if end is None or now < end:
            continue
        moved = await (finish(db, quiz, now) if quiz.timing_mode == "total" else advance(db, quiz, now))
        if moved:
            log.info("Quiz %s: time up on question %s", quiz.id, quiz.current_question)
            changed.append(quiz)
    return changed


async def quiz_timer_loop():
    """Background task: run `tick` every TICK_S seconds."""
    from ..database import async_session
    log.info("Quiz timer started (interval=%ss)", TICK_S)
    while True:
        try:
            await asyncio.sleep(TICK_S)
            async with async_session() as db:
                changed = await tick(db)
                if not db.dirty and not changed:
                    continue
                await db.commit()
                for quiz in changed:
                    await db.refresh(quiz)
                    await broadcast(quiz)
        except asyncio.CancelledError:
            return
        except Exception as e:  # keep the loop alive on transient errors
            log.warning("Quiz timer error: %s", e)
