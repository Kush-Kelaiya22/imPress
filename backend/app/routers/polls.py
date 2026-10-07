"""Poll router: create (planned/live), start, vote, end."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, ClassSession, Poll, PollVote, EspDevice
from ..schemas import PollCreate, PollResponse, PollVoteSubmit
from ..auth import get_current_user, require_teacher_or_admin
from ..ws.manager import manager
from ..activity import log_activity
from ..timeutil import istnow
from .device import _verify_api_key

router = APIRouter(prefix="/api/polls", tags=["polls"])


async def _verify_class_access(class_id: int, user: User, db: AsyncSession) -> ClassSession:
    result = await db.execute(select(ClassSession).where(ClassSession.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if user.role == "teacher" and cls.teacher_id != user.id:
        raise HTTPException(403, "You don't have access to this class")
    return cls


async def _poll_response(poll: Poll, db: AsyncSession) -> PollResponse:
    count_result = await db.execute(
        select(func.count()).select_from(PollVote).where(PollVote.poll_id == poll.id)
    )
    total = count_result.scalar() or 0
    return PollResponse(
        id=poll.id,
        class_session_id=poll.class_session_id,
        title=poll.title,
        options=poll.options,
        poll_mode=poll.poll_mode,
        status=poll.status,
        is_live=poll.is_live or False,
        total_votes=total,
        created_at=poll.created_at,
    )


# ── Create Poll ─────────────────────────────────────────────────────

@router.post("/", response_model=PollResponse, status_code=201)
async def create_poll(
    body: PollCreate,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a poll. Live polls start immediately, planned polls wait for faculty to go live."""
    cls = await _verify_class_access(body.class_session_id, user, db)

    poll = Poll(
        class_session_id=body.class_session_id,
        title=body.title,
        options=body.options,
        poll_mode=body.poll_mode,
        status="draft",
        is_live=False,
    )

    if body.poll_mode == "live":
        poll.status = "active"
        poll.is_live = True
        poll.started_at = istnow()

    db.add(poll)
    await db.flush()

    await log_activity(db, "poll.create", user.id, "poll", poll.id, {
        "title": body.title,
        "poll_mode": body.poll_mode,
        "class_id": body.class_session_id,
    })
    await db.commit()
    await db.refresh(poll)

    if poll.is_live:
        await manager.broadcast_to_class(cls.id, {
            "type": "poll_started",
            "poll_id": poll.id,
            "title": poll.title,
            "options": poll.options,
        })

    return await _poll_response(poll, db)


# ── List Polls ──────────────────────────────────────────────────────

@router.get("/class/{class_id}", response_model=list[PollResponse])
async def list_polls(
    class_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    await _verify_class_access(class_id, user, db)
    result = await db.execute(
        select(Poll).where(Poll.class_session_id == class_id).order_by(Poll.id.desc())
    )
    polls = result.scalars().all()
    return [await _poll_response(p, db) for p in polls]


@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(
    poll_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(404, "Poll not found")
    return await _poll_response(poll, db)


# ── Start Poll (planned → live) ────────────────────────────────────

@router.post("/{poll_id}/start", response_model=PollResponse)
async def start_poll(
    poll_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Make a planned poll live."""
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(404, "Poll not found")

    cls = await _verify_class_access(poll.class_session_id, user, db)

    if poll.status == "active":
        raise HTTPException(400, "Poll is already active")

    poll.status = "active"
    poll.is_live = True
    poll.started_at = istnow()

    await log_activity(db, "poll.start", user.id, "poll", poll_id, {"title": poll.title})
    await db.commit()
    await db.refresh(poll)

    await manager.broadcast_to_class(cls.id, {
        "type": "poll_started",
        "poll_id": poll.id,
        "title": poll.title,
        "options": poll.options,
    })

    return await _poll_response(poll, db)


# ── End Poll ────────────────────────────────────────────────────────

@router.post("/{poll_id}/end", response_model=PollResponse)
async def end_poll(
    poll_id: int,
    user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(404, "Poll not found")

    cls = await _verify_class_access(poll.class_session_id, user, db)

    poll.status = "closed"
    poll.is_live = False
    poll.ended_at = istnow()

    await log_activity(db, "poll.end", user.id, "poll", poll_id, {"title": poll.title})
    await db.commit()
    await db.refresh(poll)

    # Broadcast results
    votes_result = await db.execute(
        select(PollVote).where(PollVote.poll_id == poll_id)
    )
    votes = votes_result.scalars().all()
    option_counts = [0] * len(poll.options)
    for v in votes:
        if 0 <= v.selected_option < len(option_counts):
            option_counts[v.selected_option] += 1

    await manager.broadcast_to_class(cls.id, {
        "type": "poll_ended",
        "poll_id": poll.id,
        "title": poll.title,
        "option_counts": option_counts,
        "total_votes": len(votes),
    })

    return await _poll_response(poll, db)


# ── Vote ────────────────────────────────────────────────────────────

@router.post("/{poll_id}/vote", dependencies=[Depends(_verify_api_key)])
async def vote_poll(
    poll_id: int,
    body: PollVoteSubmit,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(404, "Poll not found")
    if poll.status != "active":
        raise HTTPException(400, "Poll is not active")
    if body.selected_option >= len(poll.options):
        raise HTTPException(422, "selected_option out of range for this poll")
    # device_id is the de-dup key, so it must be a real registered device.
    if await db.get(EspDevice, body.device_id) is None:
        raise HTTPException(404, "Device not registered")

    # Prevent duplicate votes from same device
    existing = await db.execute(
        select(PollVote).where(
            PollVote.poll_id == poll_id,
            PollVote.device_id == body.device_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already voted")

    vote = PollVote(
        poll_id=poll_id,
        device_id=body.device_id,
        selected_option=body.selected_option,
    )
    db.add(vote)
    await db.commit()

    # Get updated total
    count_result = await db.execute(
        select(func.count()).select_from(PollVote).where(PollVote.poll_id == poll_id)
    )
    total_votes = count_result.scalar() or 0

    cls_result = await db.execute(select(ClassSession).where(ClassSession.id == poll.class_session_id))
    cls = cls_result.scalar_one_or_none()
    if cls:
        await manager.broadcast_to_class(cls.id, {
            "type": "poll_vote",
            "poll_id": poll_id,
            "device_id": body.device_id,
            "selected_option": body.selected_option,
            "total_votes": total_votes,
        })

    return {"status": "recorded"}


# ── Results ─────────────────────────────────────────────────────────

@router.get("/{poll_id}/results")
async def poll_results(
    poll_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(404, "Poll not found")

    votes_result = await db.execute(
        select(PollVote).where(PollVote.poll_id == poll_id)
    )
    votes = votes_result.scalars().all()

    option_counts = [0] * len(poll.options)
    for v in votes:
        if 0 <= v.selected_option < len(option_counts):
            option_counts[v.selected_option] += 1

    return {
        "poll_id": poll_id,
        "title": poll.title,
        "options": poll.options,
        "poll_mode": poll.poll_mode,
        "status": poll.status,
        "total_votes": len(votes),
        "option_counts": option_counts,
    }
