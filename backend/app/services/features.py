"""Features: every small capability of the web app is a switch (v2.2).

Three authorities may set a switch, and a higher one is never overridden by a lower one:

    TrustedInstaller (4)  turns features off when the host cannot carry them (services/boot_verify.py)
    root             (3)  launch flags and the root console (policy flag features.disabled, `feature` command)
    super admin      (2)  the System page
    administrator    (1)  the System page

A change is allowed when the actor's rank is at least the rank of whoever set the switch last and at least its
`min_rank` (the least authority that may change it). Whoever sets a switch may also raise `min_rank` up to their
own rank, which stops lower ranks changing it. Faculty never see any of this. Every change is written to the
policy log with who and when.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc
from ..models import FeatureFlag, PolicyLog
from ..timeutil import istnow

ADMIN, SUPER, ROOT, TRUSTED = 1, 2, 3, 4
RANK_NAME = {ADMIN: "an administrator", SUPER: "a super administrator", ROOT: "root", TRUSTED: "TrustedInstaller"}
RANK_SHORT = {ADMIN: "administrator", SUPER: "super admin", ROOT: "root", TRUSTED: "TrustedInstaller"}


@dataclass(frozen=True)
class Feature:
    name: str
    title: str
    doc: str
    group: str


FEATURES: dict[str, Feature] = {f.name: f for f in [
    Feature("search", "Global search", "Search over classes, students, devices, accounts and settings.", "Interface"),
    Feature("notifications", "Notification tray", "The bell with alerts and updates.", "Interface"),
    Feature("tutorial", "Guided tour", "The interactive tour offered on first sign-in and from the Tutorial button.", "Interface"),
    Feature("onboarding", "Welcome set-up", "The first sign-in questions: name, password, theme.", "Interface"),
    Feature("sidebar_collapse", "Collapsible sidebar", "Let people collapse the sidebar to icons.", "Interface"),
    Feature("help_menu", "Help and documentation", "The documentation menu for administrators.", "Interface"),
    Feature("password_meter", "Password strength meter", "The strength bar under password fields.", "Interface"),
    Feature("dashboard_widgets", "Dashboard widgets", "Editable dashboard: add, remove and move widgets.", "Personalization"),
    Feature("personalization", "Personalization", "Accent colours, date and time formats.", "Personalization"),
    Feature("accessibility", "Accessibility settings", "Colour-vision modes, contrast, motion and text size.", "Personalization"),
    Feature("advanced_mode", "Advanced mode", "Detailed statistics for administrators.", "Personalization"),
    Feature("class_icons", "Class icons and colours", "Choose an icon and colour for a class.", "Classes"),
    Feature("ta_designation", "Teaching assistants", "The TA designation for faculty accounts.", "Accounts"),
    Feature("trash", "Deleted accounts (30 days)", "Restore a deleted account within 30 days.", "Accounts"),
    Feature("presence", "Active users", "Who is signed in now, last activity and activity graphs.", "Accounts"),
    Feature("backups", "Backups and restore", "Save, view and restore backups of the database and system state.", "System"),
    Feature("activity_charts", "Activity graphs", "Charts of an account's activity over time.", "System"),
    Feature("traffic_monitor", "Traffic monitor", "Detect unusual request rates and alert administrators.", "Security"),
    Feature("risk_scores", "Account risk badges", "A safety badge and score for every account.", "Security"),
    Feature("disabled_overlay", "Disabled-account notice", "Blur the page and explain when the signed-in account is disabled.", "Security"),
    Feature("update_overlay", "Update notice", "Blur the page and explain while the system is being updated.", "System"),
]}

_state: dict[str, dict] = {}


def rank_of(user) -> int:
    return SUPER if getattr(user, "role", "") == "super_admin" else ADMIN


def root_disabled() -> set[str]:
    return {x.strip() for x in str(gpc.get("features.disabled") or "").split(",") if x.strip()}


def enabled(name: str) -> bool:
    """Is the feature on? (the web app asks this through /api/system/status; routes ask it here)"""
    assert name in FEATURES, name
    if name in root_disabled():
        return False
    row = _state.get(name)
    return True if row is None else bool(row["enabled"])


def describe(name: str) -> dict:
    f, row = FEATURES[name], _state.get(name)
    by_root = name in root_disabled()
    return {"name": name, "title": f.title, "doc": f.doc, "group": f.group, "enabled": enabled(name),
            "set_by": "root (launch flag)" if by_root else (row or {}).get("set_by", ""),
            "set_at": None if by_root or not row else row["set_at"],
            "set_rank": ROOT if by_root else (row or {}).get("set_rank", 0),
            "min_rank": ROOT if by_root else (row or {}).get("min_rank", ADMIN)}


def snapshot() -> dict[str, bool]:
    return {n: enabled(n) for n in FEATURES}


async def load(db: AsyncSession) -> None:
    _state.clear()
    for r in (await db.execute(select(FeatureFlag))).scalars():
        _state[r.name] = {"enabled": r.enabled, "min_rank": r.min_rank, "set_rank": r.set_rank, "set_by": r.set_by,
                          "set_at": r.set_at.isoformat() if r.set_at else None, "prev": r.prev}


def require_feature(name: str):
    """Route dependency: 403 when the feature is switched off."""
    from fastapi import HTTPException

    async def dependency() -> None:
        if not enabled(name):
            raise HTTPException(403, {"code": "FEATURE_DISABLED",
                                      "message": f"{FEATURES[name].title} is switched off by an administrator."})
    return dependency


async def log(db: AsyncSession, flag: str, old, new, actor: str, rank: int, note: str = "") -> None:
    db.add(PolicyLog(at=istnow(), flag=flag, old=str(old), new=str(new), actor=actor, actor_rank=rank, note=note))


class Refused(Exception):
    pass


async def set_feature(db: AsyncSession, name: str, on: bool | None, actor: str, rank: int,
                      min_rank: int | None = None, note: str = "") -> dict:
    """Switch a feature and/or change who may change it. Raises Refused with a message fit to show."""
    if name not in FEATURES:
        raise Refused(f"There is no feature called {name}.")
    d = describe(name)
    if name in root_disabled() and rank < ROOT:
        raise Refused("Root switched this off when the server was started. It can only be changed there.")
    if rank < d["set_rank"]:
        raise Refused(f"This was set by {RANK_NAME.get(d['set_rank'], 'someone with more authority')} and "
                      "can only be changed by them or by someone with more authority.")
    if rank < d["min_rank"]:
        raise Refused(f"Changing this needs {RANK_NAME.get(d['min_rank'], 'more authority')}.")
    if min_rank is not None and not ADMIN <= min_rank <= rank:
        raise Refused("You can only restrict a feature to your own level or below.")
    new_on = d["enabled"] if on is None else bool(on)
    new_min = d["min_rank"] if min_rank is None else min_rank
    if new_on == d["enabled"] and new_min == d["min_rank"]:
        return describe(name)
    row = await db.get(FeatureFlag, name)
    prev = row.prev if row else None
    if row is None:
        row = FeatureFlag(name=name)
        db.add(row)
    row.enabled, row.min_rank, row.set_rank, row.set_by, row.set_at, row.prev = new_on, new_min, rank, actor, istnow(), prev
    if new_on != d["enabled"]:
        await log(db, name, "on" if d["enabled"] else "off", "on" if new_on else "off", actor, rank, note)
    if new_min != d["min_rank"]:
        await log(db, name, f"changeable by {RANK_SHORT.get(d['min_rank'])}", f"changeable by {RANK_SHORT.get(new_min)}",
                  actor, rank, note)
    await db.flush()
    await load(db)
    return describe(name)


async def history(db: AsyncSession, flag: str | None = None, limit: int = 100) -> list[dict]:
    q = select(PolicyLog).order_by(PolicyLog.id.desc()).limit(limit)
    if flag:
        q = q.where(PolicyLog.flag == flag)
    return [{"at": r.at.isoformat(), "flag": r.flag, "old": r.old, "new": r.new, "actor": r.actor,
             "actor_role": RANK_SHORT.get(r.actor_rank, ""), "note": r.note} for r in (await db.execute(q)).scalars()]


async def trusted_set(db: AsyncSession, name: str, on: bool, note: str) -> None:
    """TrustedInstaller: turn a feature off because the host fails a requirement, or give it back when it passes."""
    row = await db.get(FeatureFlag, name)
    if not on:
        if row is not None and row.set_rank == TRUSTED:
            return
        prev = None if row is None else {"enabled": row.enabled, "min_rank": row.min_rank, "set_rank": row.set_rank,
                                         "set_by": row.set_by}
        if row is None:
            row = FeatureFlag(name=name)
            db.add(row)
        was = row.enabled if row.enabled is not None else True
        row.enabled, row.min_rank, row.set_rank, row.set_by, row.set_at, row.prev = False, TRUSTED, TRUSTED, "TrustedInstaller", istnow(), prev
        await log(db, name, "on" if was else "off", "off", "TrustedInstaller", TRUSTED, note)
    elif row is not None and row.set_rank == TRUSTED:
        p = row.prev
        if p:
            row.enabled, row.min_rank, row.set_rank, row.set_by, row.prev = p["enabled"], p["min_rank"], p["set_rank"], p["set_by"], None
        else:
            await db.execute(delete(FeatureFlag).where(FeatureFlag.name == name))
        await log(db, name, "off", "on" if not p or p["enabled"] else "off", "TrustedInstaller", TRUSTED, note)
    await db.flush()
    await load(db)


async def refresh_loop(every: float = 5.0) -> None:
    """Pick up changes made by another process (root's console) within a few seconds.
    ponytail: polling a tiny table; a notification channel if there are ever many processes."""
    import asyncio

    from ..database import async_session
    while True:
        await asyncio.sleep(every)
        try:
            async with async_session() as db:
                await load(db)
        except Exception:                                # noqa: BLE001
            pass
