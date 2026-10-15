"""Slow down password guessing (#153).

Failures are counted per key ("user:<name>", "ip:<address>",
"change:<user id>") in the database, so a restart does not reset them. After
the free attempts in a 15-minute window, each further failure doubles the
wait (30 s, 60 s, ... at most 15 min). There is no permanent lockout: that
would let anyone disable a real account by guessing wrong on purpose.
"""

from __future__ import annotations

import math

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LoginThrottle

WINDOW = timedelta(minutes=15)
FIRST_DELAY_S, MAX_DELAY_S = 30, 15 * 60
FREE = {"user": 5, "ip": 20, "change": 5}     # one school NAT address serves many teachers


def _free(key: str) -> int:
    return FREE.get(key.split(":", 1)[0], 5)


async def check(db: AsyncSession, keys: list[str], now: datetime) -> None:
    """Raise 429 while any key is in its waiting period."""
    rows = (await db.execute(select(LoginThrottle).where(LoginThrottle.key.in_(keys)))).scalars().all()
    wait = max(((r.blocked_until - now).total_seconds() for r in rows if r.blocked_until and r.blocked_until > now),
               default=0)
    if wait > 0:
        seconds = math.ceil(wait)
        raise HTTPException(429, {"code": "TOO_MANY_ATTEMPTS",
                                  "message": f"Too many failed attempts. Try again in {seconds} s."},
                            headers={"Retry-After": str(seconds)})


async def failed(db: AsyncSession, keys: list[str], now: datetime) -> None:
    """Count a failure for every key (the caller commits)."""
    for key in keys:
        row = await db.get(LoginThrottle, key)
        if row is None:
            row = LoginThrottle(key=key, failures=0, first_at=now)
            db.add(row)
        if now - row.first_at > WINDOW and not (row.blocked_until and row.blocked_until > now):
            row.failures, row.first_at, row.blocked_until = 0, now, None
        row.failures += 1
        over = row.failures - _free(key)
        if over >= 0:
            row.blocked_until = now + timedelta(seconds=min(FIRST_DELAY_S * 2 ** min(over, 5), MAX_DELAY_S))


async def succeeded(db: AsyncSession, key: str) -> None:
    await db.execute(delete(LoginThrottle).where(LoginThrottle.key == key))


async def reset_account(db: AsyncSession, username: str, user_id: int) -> int:
    """New credentials start with a fresh allowance; address-wide limits stay in place."""
    keys = [f"user:{username.strip().lower()}"[:160], f"change:{user_id}"]
    result = await db.execute(delete(LoginThrottle).where(LoginThrottle.key.in_(keys)))
    return result.rowcount or 0


async def prune(db: AsyncSession, now: datetime) -> None:
    """Forget counters nobody has touched for a day."""
    await db.execute(delete(LoginThrottle).where(LoginThrottle.first_at < now - timedelta(days=1),
                                                 (LoginThrottle.blocked_until.is_(None))
                                                 | (LoginThrottle.blocked_until < now)))
