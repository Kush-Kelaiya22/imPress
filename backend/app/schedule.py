"""Schedule conflict validation for classroom sections (hybrid scheduling).

Conflicts are now *warnings*, not hard blocks (R6): admin/faculty may schedule
combined or clashing classes, but the system surfaces every clash so they can
make an informed choice. The callers surface these as `warnings` on the
ClassResponse.
"""

import re
from dataclasses import dataclass
from datetime import date as Date, datetime, timedelta
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

# ── Room occupancy (#126) ────────────────────────────────────────────────
# One question for everything that must not disturb a class (OTA windows,
# #128): which intervals is this room booked between `start` and `end`?
# Regular weekly slots within each class's dates, minus cancelled and moved
# occurrences, plus moved-in and extra ones. None means "unknown": the
# authoritative timetable is stale, so a caller must fail closed.

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


@dataclass(frozen=True)
class Busy:
    start: datetime
    end: datetime
    class_id: int
    why: str            # "regular" | "moved" | "extra"


def _at(day: Date, hhmm: str) -> datetime | None:
    m = _parse_time(hhmm or "")
    return None if m is None else datetime(day.year, day.month, day.day) + timedelta(minutes=m)


def _span(day: Date, start: str, end: str) -> tuple[datetime, datetime] | None:
    a, b = _at(day, start), _at(day, end)
    if a is None or b is None:
        return None
    return a, (b if b > a else b + timedelta(days=1))


async def schedule_is_current(db: AsyncSession, now: datetime) -> bool:
    """False when an authoritative source has synced before but not recently."""
    from .config import settings
    from .models import ScheduleSource
    if settings.SCHEDULE_MAX_AGE_HOURS <= 0:
        return True
    rows = (await db.execute(select(ScheduleSource))).scalars().all()
    limit = timedelta(hours=settings.SCHEDULE_MAX_AGE_HOURS)
    return all(now - r.last_synced_at <= limit for r in rows)


async def occupancy(db: AsyncSession, classroom_code: str, start: datetime, end: datetime,
                    now: datetime | None = None) -> list[Busy] | None:
    """Booked intervals of a room overlapping [start, end), or None if unknown."""
    from .models import ClassOccurrenceException
    from .timeutil import istnow
    code = (classroom_code or "").strip().lower()
    if not code or not await schedule_is_current(db, now or istnow()):
        return None
    classes = (await db.execute(select(ClassSession))).scalars().all()
    by_id = {c.id: c for c in classes}
    rooms = {c.id: (c.classroom_code or "").strip().lower() for c in classes}
    first, last = start.date() - timedelta(days=1), end.date()    # an overnight slot can start the day before
    exceptions = (await db.execute(select(ClassOccurrenceException).where(
        (ClassOccurrenceException.date.between(first, last))
        | (ClassOccurrenceException.new_date.between(first, last))))).scalars().all()
    removed = {}                                   # (class, date) -> {slot_start or "" for the whole day}
    for e in exceptions:
        if e.kind in ("cancelled", "moved"):
            removed.setdefault((e.class_session_id, e.date), set()).add(e.slot_start or "")

    busy = []
    day = first
    while day <= last:
        name = WEEKDAYS[day.weekday()]
        for c in classes:
            if rooms[c.id] != code or (c.start_date and day < c.start_date) or (c.end_date and day > c.end_date):
                continue
            gone = removed.get((c.id, day), set())
            for slot in c.meeting_schedule or []:
                if (slot.get("day") or "").strip() != name or "" in gone or (slot.get("start") or "").strip() in gone:
                    continue
                span = _span(day, slot.get("start", ""), slot.get("end", ""))
                if span:
                    busy.append(Busy(*span, c.id, "regular"))
        day += timedelta(days=1)
    for e in exceptions:
        if e.kind not in ("moved", "extra"):
            continue
        cls = by_id.get(e.class_session_id)
        room = (e.classroom_code or (cls.classroom_code if cls else "") or "").strip().lower()
        span = _span(e.new_date or e.date, e.new_start, e.new_end)
        if room == code and span:
            busy.append(Busy(*span, e.class_session_id, e.kind))
    return sorted((b for b in busy if b.start < end and start < b.end), key=lambda b: b.start)
