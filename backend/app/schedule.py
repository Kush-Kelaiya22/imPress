"""Schedule conflict validation for classroom sections (hybrid scheduling).

Conflicts are now *warnings*, not hard blocks (R6): admin/faculty may schedule
combined or clashing classes, but the system surfaces every clash so they can
make an informed choice. The callers surface these as `warnings` on the
ClassResponse.
"""

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ClassSession

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _parse_time(t: str) -> int | None:
    """Convert "HH:MM" → minutes since midnight. Returns None if malformed."""
    if not _TIME_RE.match(t.strip()):
        return None
    try:
        hh, mm = t.strip().split(":")
        return int(hh) * 60 + int(mm)
    except ValueError:
        return None


def _slots_conflict(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """Two time slots overlap when neither fully precedes the other.

    Overnight / wrap-around slots (end <= start) are clamped to 23:59 so a
    late slot still registers an overlap.
    """
    as_ = _parse_time(a_start)
    ae = _parse_time(a_end)
    bs = _parse_time(b_start)
    be = _parse_time(b_end)
    if None in (as_, ae, bs, be):
        return False
    if ae <= as_:
        ae = 24 * 60 - 1
    if be <= bs:
        be = 24 * 60 - 1
    return as_ < be and bs < ae


def _same_academic_window(cls: ClassSession, other: ClassSession) -> bool:
    """Two classes only clash if they run in the same semester/window.

    Priority: term+year match → date-range overlap → treat as unknown (flag).
    """
    mine = (cls.term or "").strip(), cls.year
    theirs = (other.term or "").strip(), other.year
    if mine[0] and mine[1] and theirs[0] and theirs[1]:
        return mine == theirs
    if cls.start_date and cls.end_date and other.start_date and other.end_date:
        return cls.start_date <= other.end_date and other.start_date <= cls.end_date
    return True  # window unknown on either side → conservatively flag


async def find_schedule_conflicts(
    db: AsyncSession,
    teacher_id: int,
    meeting_schedule: list[dict[str, Any]],
    location: str = "",
    exclude_class_id: int | None = None,
    term: str = "",
    year: int | None = None,
    start_date=None,
    end_date=None,
) -> list[dict]:
    """Return a list of clash warnings for the given timetable.

    Never raises — the caller decides whether to proceed. Each warning is:
        {"type": "teacher"|"room", "message": str,
         "class_id": int, "class_name": str, "day": str,
         "start": str, "end": str}
    """
    warnings: list[dict] = []
    if not meeting_schedule:
        return warnings

    # Reference window for this class (projected from params).
    cls_ctx = ClassSession(
        term=term or "",
        year=year,
        start_date=start_date,
        end_date=end_date,
    )

    q = select(ClassSession).where(ClassSession.meeting_schedule.is_not(None))
    if exclude_class_id:
        q = q.where(ClassSession.id != exclude_class_id)
    result = await db.execute(q)
    existing = result.scalars().all()

    for slot in meeting_schedule:
        day = (slot.get("day") or "").strip()
        start = (slot.get("start") or "").strip()
        end = (slot.get("end") or "").strip()
        if not (day and start and end):
            continue
        for other in existing:
            if not _same_academic_window(cls_ctx, other):
                continue
            for other_slot in other.meeting_schedule or []:
                if (other_slot.get("day") or "").strip() != day:
                    continue
                if not _slots_conflict(start, end, other_slot.get("start", ""), other_slot.get("end", "")):
                    continue
                if other.teacher_id == teacher_id:
                    warnings.append({
                        "type": "teacher",
                        "message": (
                            f"Faculty already teaches {other.name or f'class #{other.id}'} "
                            f"on {day} {other_slot.get('start')}–{other_slot.get('end')}"
                        ),
                        "class_id": other.id,
                        "class_name": other.name,
                        "day": day,
                        "start": other_slot.get("start", ""),
                        "end": other_slot.get("end", ""),
                    })
                if location and other.location and other.location.strip().lower() == location.strip().lower():
                    warnings.append({
                        "type": "room",
                        "message": (
                            f"Room {location} already in use by {other.name or f'class #{other.id}'} "
                            f"on {day} {other_slot.get('start')}–{other_slot.get('end')}"
                        ),
                        "class_id": other.id,
                        "class_name": other.name,
                        "day": day,
                        "start": other_slot.get("start", ""),
                        "end": other_slot.get("end", ""),
                    })
    return warnings