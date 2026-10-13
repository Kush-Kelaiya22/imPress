"""Maintenance windows for classroom hubs and gateways (#128).

A hub (S3) or gateway (C6) update takes the room's response system offline
for its duration, so it may start only when the room has no class: before
the first class, after the last, or in a gap between classes. The window must
hold the update (`window_min`) plus a safety buffer on both sides
(`buffer_min`). The deployment engine asks here before *every* offer, so a
class added or moved after the deployment was created still blocks it.

Fail closed: a room whose timetable is unknown or stale waits; a class that
is activated (in session) or has a live quiz or poll waits. A device not
linked to any class has no class to disturb.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ClassSession, EspDevice, Poll, Quiz
from ..schedule import occupancy

ROOM_DEVICES = ("c6", "s3")
LIVE_RECHECK = timedelta(minutes=15)      # a class in session: look again soon
UNKNOWN_RECHECK = timedelta(minutes=30)   # unknown timetable: look again, never assume free
HORIZON = timedelta(days=7)               # how far ahead the next window is searched


async def room_class(db: AsyncSession, device: EspDevice) -> ClassSession | None:
    """The class whose room this device serves: a gateway's linked class, or
    the class of the hub's gateway."""
    node = device.id if (device.device_type or "").lower() == "c6" else device.gateway_id
    if node is None:
        return None
    return (await db.execute(select(ClassSession).where(ClassSession.device_id == node))).scalars().first()


async def _live(db: AsyncSession, cls: ClassSession) -> str:
    if cls.is_active:
        return f"class {cls.name} is activated (in session)"
    for model, what in ((Quiz, "quiz"), (Poll, "poll")):
        if (await db.execute(select(model.id).where(model.class_session_id == cls.id,
                                                     model.status == "active"))).first():
            return f"a {what} is live in {cls.name}"
    return ""


async def next_window(db: AsyncSession, device: EspDevice, now: datetime, window_min: int,
                      buffer_min: int) -> tuple[datetime | None, str]:
    """(None, "") when the update may start now; otherwise (when to look
    again, why not now)."""
    if (device.device_type or "").lower() not in ROOM_DEVICES:
        return None, ""
    cls = await room_class(db, device)
    if cls is None:
        return None, ""
    live = await _live(db, cls)
    if live:
        return now + LIVE_RECHECK, live
    need, buf = timedelta(minutes=window_min), timedelta(minutes=buffer_min)
    busy = await occupancy(db, cls.classroom_code or "", now - buf, now + HORIZON, now=now,
                           class_id=None if cls.classroom_code else cls.id)
    if busy is None:
        return now + UNKNOWN_RECHECK, "the room's timetable is unknown or out of date (fail closed)"
    start = now
    for b in busy:                                   # sorted by start
        if b.end + buf <= start:
            continue
        if b.start - buf >= start + need:
            break
        start = b.end + buf
    if start == now:
        return None, ""
    return start, f"room busy: next free window {start:%Y-%m-%d %H:%M}"
