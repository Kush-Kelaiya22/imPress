"""Server events for the web app (v2.2): one in-process publish/subscribe.

Every signed-in browser holds one Server-Sent Events stream (GET
/api/events). The server publishes three kinds of event:

  changed  {"topics": [table names]}  data changed: pages showing it refetch
  alert    {"level", "message"}       a toast (e.g. for administrators only)
  status   {"test_mode", "db"}        the system banner and the database state

Changes are coalesced (one event per 300 ms with the union of the topics), so
a burst of answers is one refresh, not hundreds.

ponytail: in-process queues: one server process (the supported deployment,
uvicorn --workers 1). Several processes would need a shared broker.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

COALESCE_S = 0.3
QUEUE_MAX = 100


@dataclass(eq=False)
class Subscriber:
    admin: bool                                  # receives administrators' alerts (policy decides)
    user_id: int
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(QUEUE_MAX))


_subscribers: set[Subscriber] = set()
_pending_topics: set[str] = set()
_flush_scheduled = False


def subscribe(admin: bool, user_id: int) -> Subscriber:
    sub = Subscriber(admin, user_id)
    _subscribers.add(sub)
    return sub


def unsubscribe(sub: Subscriber) -> None:
    _subscribers.discard(sub)


def subscriber_count() -> int:
    return len(_subscribers)


def to_user(user_id: int, event: dict) -> None:
    """One person's open pages only (e.g. their account was disabled)."""
    _deliver(event, only_user=user_id)


def _deliver(event: dict, audience: str = "all", only_user: int | None = None) -> None:
    data = json.dumps(event, default=str)
    for sub in list(_subscribers):
        if audience == "admins" and not sub.admin:
            continue
        if only_user is not None and sub.user_id != only_user:
            continue
        try:
            sub.queue.put_nowait(data)
        except asyncio.QueueFull:              # a stalled browser: drop its oldest event
            try:
                sub.queue.get_nowait()
                sub.queue.put_nowait(data)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass


def changed(tables) -> None:
    """Data in these tables changed (called after a commit)."""
    global _flush_scheduled
    _pending_topics.update(t for t in tables if t)
    if _flush_scheduled or not _pending_topics:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:                       # no loop (a script): nobody is listening
        _pending_topics.clear()
        return
    _flush_scheduled = True
    loop.call_later(COALESCE_S, _flush)


def _flush() -> None:
    global _flush_scheduled
    _flush_scheduled = False
    topics = sorted(_pending_topics)
    _pending_topics.clear()
    if topics:
        _deliver({"type": "changed", "topics": topics})


def alert(message: str, level: str = "warning", audience: str = "admins") -> None:
    """A toast for everyone, or for administrators and super admins only."""
    logger.warning("alert (%s): %s", audience, message)
    _deliver({"type": "alert", "level": level, "message": message}, audience)


def status(payload: dict, audience: str = "all") -> None:
    """A state change for open pages. The database's integrity state is for
    administrators only (audience="admins"): it tells an attacker when it
    was tampered with."""
    _deliver({"type": "status", **payload}, audience)
