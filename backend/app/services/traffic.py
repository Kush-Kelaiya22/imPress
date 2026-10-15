"""Traffic monitor (v2.2): notices unusual request rates and tells administrators. It never blocks anything.

Every API request is counted per origin address, per signed-in account and per kind of endpoint over a sliding
minute. Each kind has its own limit (signing in is stricter than reading a list; devices that report the answers of a
whole room are far more generous than people). The limits are deliberately high: this is a classroom system used by
staff, so a flag means a script or a fault, not a busy lesson.

* **DoS**  one origin or one account goes over the limit of one kind of endpoint.
* **DDoS** the total for one kind of endpoint is several times its limit and comes from many different origins.

A flag raises an alert for administrators and super admins (who, from where, which pages, how fast) and an entry in
the activity log. Nothing is refused or slowed down: the response is the people's. Each account also gets a **risk
score** from 0 to 100 (request volume, refused requests, many addresses at once, earlier flags, refused database
writes) shown as a badge: Safe, Potentially Unsafe or Likely Compromised. The score only informs; a super admin
decides whether to sign someone out.

The counters are in memory and start again with the server.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections import Counter, defaultdict, deque

from .. import gpc

WINDOW_S = 60
COOLDOWN_S = 600
DDOS_FACTOR, DDOS_ORIGINS = 4, 8

# kind of endpoint → (per origin per minute, per account per minute)
LIMITS: dict[str, tuple[int, int]] = {
    "sign-in": (60, 60), "device": (12000, 12000), "live": (90, 90), "status": (300, 300),
    "read": (1200, 1800), "write": (400, 600), "admin": (900, 1200),
}

_hits_ip: dict[tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=20000))
_hits_acct: dict[tuple[int, str], deque] = defaultdict(lambda: deque(maxlen=20000))
_hits_kind: dict[str, deque] = defaultdict(lambda: deque(maxlen=60000))
_acct: dict[int, dict] = defaultdict(lambda: {"req": deque(maxlen=5000), "refused": deque(maxlen=500), "ips": {}, "flags": deque(maxlen=50)})
_last_flag: dict[tuple, float] = {}
_alerts: deque = deque(maxlen=200)
_tasks: set = set()
_seq = [0]


def kind_of(path: str, method: str) -> str:
    if path in ("/api/auth/login", "/api/auth/change-password"):
        return "sign-in"
    if path.startswith(("/api/device", "/ws")):
        return "device"
    if path == "/api/events":
        return "live"
    if path in ("/api/system/status", "/api/auth/session-status", "/api/auth/session", "/api/auth/activity"):
        return "status"
    if path.startswith("/api/admin"):
        return "admin"
    return "read" if method in ("GET", "HEAD") else "write"


def _prune(q: deque, now: float, span: float = WINDOW_S) -> None:
    while q and now - q[0][0] > span:
        q.popleft()


def _spawn(make_coro) -> None:
    t = asyncio.get_running_loop().create_task(make_coro())
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


def _route(path: str) -> str:
    return re.sub(r"/\d+", "/{id}", path)


def record(ip: str, path: str, method: str, status: int, user_id: int | None, now: float | None = None) -> None:
    """Count one request and flag what is unusual. Cheap: a few deque operations."""
    if not gpc.get("traffic.monitor") or not path.startswith(("/api", "/ws")):
        return
    from . import features
    if not features.enabled("traffic_monitor"):
        return
    now = time.monotonic() if now is None else now
    kind, route = kind_of(path, method), _route(path)
    limit_ip, limit_acct = LIMITS[kind]
    q = _hits_ip[(ip, kind)]
    q.append((now, route))
    _prune(q, now)
    k = _hits_kind[kind]
    k.append((now, ip))
    _prune(k, now)
    if len(q) > limit_ip:
        _flag("DoS", kind, ip, None, len(q), limit_ip, q, now)
    if user_id is not None:
        a = _acct[user_id]
        a["req"].append((now, route))
        a["ips"][ip] = now
        if status in (401, 403, 422, 429):
            a["refused"].append((now, status))
        qa = _hits_acct[(user_id, kind)]
        qa.append((now, route))
        _prune(qa, now)
        if len(qa) > limit_acct:
            _flag("DoS", kind, ip, user_id, len(qa), limit_acct, qa, now)
    if len(k) > limit_ip * DDOS_FACTOR:
        origins = {x[1] for x in k}
        if len(origins) >= DDOS_ORIGINS:
            _flag("DDoS", kind, f"{len(origins)} origins", None, len(k), limit_ip, k, now, origins=sorted(origins)[:20])


def _flag(label: str, kind: str, origin: str, user_id: int | None, rate: int, limit: int, q: deque, now: float,
          origins: list | None = None) -> None:
    key = (label, kind, origin, user_id)
    if now - _last_flag.get(key, -1e9) < COOLDOWN_S:
        return
    _last_flag[key] = now
    _seq[0] += 1
    top = Counter(x[1] for x in q if isinstance(x[1], str) and x[1].startswith("/")).most_common(5)
    alert = {"id": _seq[0], "message": f"Possible {label}: {rate} requests a minute to {kind} pages from {origin}; "
                                     f"the usual limit is {limit}. Nothing was blocked.",
              "at": time.time(), "type": label, "endpoint_kind": kind, "origin": origin, "origins": origins or [origin],
             "user_id": user_id, "requests_per_minute": rate, "limit_per_minute": limit,
             "pages": [{"path": p, "requests": n} for p, n in top]}
    _alerts.appendleft(alert)
    if user_id is not None:
        _acct[user_id]["flags"].append(time.time())
    try:
        _spawn(lambda: _persist(alert))
    except RuntimeError:                                  # no running loop (a unit test)
        pass


async def _persist(alert: dict) -> None:
    from ..activity import log_activity
    from ..database import async_session
    from ..dbgateway import SYSTEM, act_as
    from ..models import User
    from . import events
    act_as(SYSTEM)
    who = ""
    async with async_session() as db:
        if alert["user_id"]:
            u = await db.get(User, alert["user_id"])
            who = f" (account {u.username})" if u else ""
            alert["username"] = u.username if u else ""
        text = alert["message"].replace(f"from {alert['origin']};", f"from {alert['origin']}{who};")
        alert["message"] = text
        await log_activity(db, "traffic.flagged", alert["user_id"], "system", None,
                           {"flag": True, "type": alert["type"], "kind": alert["endpoint_kind"], "origin": alert["origin"],
                            "rate": alert["requests_per_minute"], "limit": alert["limit_per_minute"],
                            "pages": alert["pages"][:3]})
        await db.commit()
    events.alert(text, "error")


def alerts(limit: int = 50) -> list[dict]:
    return list(_alerts)[:limit]


def busiest(n: int = 8) -> list[dict]:
    now, out = time.monotonic(), []
    for (ip, kind), q in list(_hits_ip.items()):
        _prune(q, now)
        if q:
            out.append({"origin": ip, "kind": kind, "requests_per_minute": len(q), "limit_per_minute": LIMITS[kind][0]})
    return sorted(out, key=lambda r: -r["requests_per_minute"] / r["limit_per_minute"])[:n]


# ── risk ─────────────────────────────────────────────────────────────────

BADGES = ((25, "Safe"), (60, "Potentially Unsafe"), (101, "Likely Compromised"))


def label(score: int) -> str:
    return next(name for top, name in BADGES if score < top)


def score(user_id: int, refused_writes: int = 0, now: float | None = None) -> dict:
    """0-100 from this account's recent behaviour; `reasons` explains every point."""
    now = time.monotonic() if now is None else now
    a = _acct.get(user_id)
    pts, why = 0, []
    if a:
        req = sum(1 for t, _ in a["req"] if now - t <= 600)
        if req > 1500:
            add = min(30, (req - 1500) // 100 + 5)
            pts += add
            why.append(f"{req} requests in ten minutes (+{add})")
        bad = sum(1 for t, _ in a["refused"] if now - t <= 600)
        if bad > 10:
            add = min(25, bad - 10 + 5)
            pts += add
            why.append(f"{bad} refused requests in ten minutes (+{add})")
        ips = sum(1 for t in a["ips"].values() if now - t <= 900)
        if ips > 2:
            add = min(30, (ips - 2) * 15)
            pts += add
            why.append(f"used from {ips} addresses at once (+{add})")
        flags = sum(1 for t in a["flags"] if time.time() - t <= 86400)
        if flags:
            add = min(40, flags * 20)
            pts += add
            why.append(f"{flags} traffic flag(s) today (+{add})")
    if refused_writes:
        add = min(30, refused_writes * 15)
        pts += add
        why.append(f"{refused_writes} refused database write(s) today (+{add})")
    pts = min(100, pts)
    return {"score": pts, "label": label(pts), "reasons": why or ["Nothing unusual."]}


def reset() -> None:
    for d in (_hits_ip, _hits_acct, _hits_kind, _acct, _last_flag):
        d.clear()
    _alerts.clear()
