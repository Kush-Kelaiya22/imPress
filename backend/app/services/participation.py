"""Participation service: quiz/poll delivery and answer aggregation.

Provides helper functions used by routers and WS handlers to manage
the flow of questions from teacher → students and answers back.
"""

import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Quiz, QuizQuestion, QuizAnswer, PollVote
from ..ws.manager import manager

logger = logging.getLogger(__name__)


async def broadcast_question(db: AsyncSession, quiz_id: int, question_order: int) -> Optional[dict]:
    """Broadcast a specific quiz question to the class room via WebSocket."""
    qr = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id, QuizQuestion.order_num == question_order)
    )
    q = qr.scalar_one_or_none()
    if not q:
        return None

    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        return None

    # Get total question count
    total_result = await db.execute(
        select(func.count(QuizQuestion.id)).where(QuizQuestion.quiz_id == quiz_id)
    )
    total = total_result.scalar() or 0

    payload = {
        "event": "quiz_question",
        "quiz_id": quiz_id,
        "question_num": q.order_num,
        "question_order": q.order_num,  # key the C6 firmware reads
        "question_text": q.question_text,
        "options": q.options,
        "time_limit_s": q.time_limit_s,
        "total_questions": total,
    }

    await manager.broadcast_to_class(quiz.class_session_id, payload)
    logger.info("Broadcast question %d of quiz %d", question_order, quiz_id)
    return payload


async def aggregate_question_results(db: AsyncSession, quiz_id: int, question_order: int) -> dict:
    """Aggregate answer counts for a single question."""
    ar = await db.execute(
        select(QuizAnswer)
        .where(QuizAnswer.quiz_id == quiz_id, QuizAnswer.question_order == question_order)
    )
    answers = ar.scalars().all()

    option_counts = [0, 0, 0, 0]
    for a in answers:
        if 0 <= a.selected_option < 4:
            option_counts[a.selected_option] += 1

    return {
        "quiz_id": quiz_id,
        "question_order": question_order,
        "total_answers": len(answers),
        "option_counts": option_counts,
    }


async def aggregate_poll_results(db: AsyncSession, poll_id: int, num_options: int) -> list[int]:
    """Aggregate vote counts for a poll."""
    counts = []
    for i in range(num_options):
        r = await db.execute(
            select(func.count(PollVote.id))
            .where(PollVote.poll_id == poll_id, PollVote.selected_option == i)
        )
        counts.append(r.scalar() or 0)
    return counts