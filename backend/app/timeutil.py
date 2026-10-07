"""Indian Standard Time (IST) helpers — the backend's single source of truth for time.

IST = Asia/Kolkata = UTC+05:30. It has no DST, so a *naive* IST timestamp is
unambiguous — storing DateTime columns as naive IST keeps SQLite simple and
gives every consumer of the API/DB a timestamp that reads as wall-clock India
time without any tz round-tripping.

Use ``istnow()`` everywhere you would have used ``datetime.utcnow()``, and
``istnow_aware()`` when an offset-aware value is required (e.g. ISO strings).
"""
from __future__ import annotations

from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo

IST_TZ: tzinfo = ZoneInfo("Asia/Kolkata")
IST_OFFSET_HOURS = 5.5  # UTC+05:30


def istnow() -> datetime:
    """Current time as a naive IST datetime (no tzinfo attached)."""
    return datetime.now(IST_TZ).replace(tzinfo=None)


def istnow_aware() -> datetime:
    """Current time as an offset-aware IST datetime."""
    return datetime.now(IST_TZ)


def as_ist(dt: datetime) -> datetime:
    """Convert any aware/naive datetime to naive IST; naive input is treated as UTC."""
    if dt.tzinfo is None:
        # Legacy rows were written as naive UTC — interpret them as UTC.
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(IST_TZ).replace(tzinfo=None)


def ist_iso(dt: datetime | None = None) -> str:
    """ISO-8601 string of *dt* (or now) in IST with explicit +05:30 offset."""
    return (dt or istnow_aware()).astimezone(IST_TZ).isoformat()


def ist_epoch_ms(dt: datetime | None) -> int | None:
    """Epoch milliseconds for a naive-IST *dt*, independent of host timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST_TZ)
    return int(dt.timestamp() * 1000)