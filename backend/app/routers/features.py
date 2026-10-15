"""Features and policy history for administrators (v2.2).

- GET  /api/admin/features              every feature, whether it is on, who set it and when
- PUT  /api/admin/features/{name}       switch it, or restrict who may change it
- GET  /api/admin/features/log          who changed what, when
- GET  /api/admin/system/requirements   what TrustedInstaller found at start-up
- GET  /api/admin/traffic               unusual-traffic alerts and the busiest origins (it never blocks anything)
- GET  /api/admin/risk                  every account's safety badge, score and the reasons
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..activity import log_activity
from ..database import get_db
from ..models import ActivityLog, User
from ..timeutil import istnow
from ..policy import require
from ..services import boot_verify, features, traffic

router = APIRouter(prefix="/api/admin", tags=["features"])


class FeatureUpdate(BaseModel):
    enabled: bool | None = None
    min_rank: int | None = None          # 1 administrators may change it, 2 only super admins


def _actor(user: User) -> tuple[str, int]:
    return user.display_name or user.username, features.rank_of(user)


@router.get("/features")
async def list_features(user: User = Depends(require("features.manage"))):
    return {"features": [features.describe(n) for n in features.FEATURES], "your_rank": features.rank_of(user)}


@router.put("/features/{name}")
async def set_feature(name: str, body: FeatureUpdate, user: User = Depends(require("features.manage")),
                      db: AsyncSession = Depends(get_db)):
    actor, rank = _actor(user)
    try:
        out = await features.set_feature(db, name, body.enabled, actor, rank, body.min_rank)
    except features.Refused as exc:
        raise HTTPException(403, {"code": "FEATURE_LOCKED", "message": str(exc)}) from None
    await log_activity(db, "features.set", user.id, "feature", None, {"flag": True, "name": name, "enabled": out["enabled"]})
    await db.commit()
    return out


@router.get("/features/log")
async def feature_log(flag: str | None = None, limit: int = Query(100, ge=1, le=500),
                      user: User = Depends(require("features.manage")), db: AsyncSession = Depends(get_db)):
    return await features.history(db, flag, limit)


@router.get("/system/requirements")
async def requirements(user: User = Depends(require("features.manage"))):
    return boot_verify.report()


@router.get("/traffic")
async def traffic_overview(user: User = Depends(require("sessions.read")), db: AsyncSession = Depends(get_db)):
    names = {u.id: u.username for u in (await db.execute(select(User))).scalars()}
    alerts = [{**a, "username": names.get(a["user_id"], "") if a["user_id"] else ""} for a in traffic.alerts()]
    return {"enabled": features.enabled("traffic_monitor"), "window_seconds": traffic.WINDOW_S,
            "limits": {k: {"per_origin": a, "per_account": b} for k, (a, b) in traffic.LIMITS.items()},
            "alerts": alerts, "busiest": traffic.busiest()}


@router.get("/risk")
async def account_risk(user: User = Depends(require("sessions.read")), db: AsyncSession = Depends(get_db)):
    if not features.enabled("risk_scores"):
        raise HTTPException(403, {"code": "FEATURE_DISABLED", "message": "Account risk badges are switched off."})
    since = istnow() - timedelta(hours=24)
    refused = dict((await db.execute(select(ActivityLog.user_id, func.count()).where(
        ActivityLog.action == "db.write_refused", ActivityLog.timestamp >= since).group_by(ActivityLog.user_id))).all())
    ids = (await db.execute(select(User.id))).scalars().all()
    return {str(i): traffic.score(i, refused.get(i, 0)) for i in ids}
