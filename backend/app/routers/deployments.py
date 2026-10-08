"""Firmware deployments: individual and bulk OTA rollouts (#38, #34)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..activity import log_activity
from ..auth import require_admin
from ..database import commit_or_conflict, get_db
from ..models import FirmwareArtifact, FirmwareDeployment, User
from ..services import deployments as engine

router = APIRouter(prefix="/api/admin/deployments", tags=["deployments"])


class Strategy(BaseModel):
    canary: int = Field(default=1, ge=0, le=50)
    batch_size: int = Field(default=5, ge=1, le=500)
    max_concurrent: int = Field(default=5, ge=1, le=100)
    max_failures: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=2, ge=1, le=5)
    timeout_s: int = Field(default=900, ge=60, le=86400)


class DeploymentCreate(BaseModel):
    artifact_id: int
    # selection: any combination narrows it; at least one is required
    device_ids: list[int] | None = None
    class_id: int | None = None
    device_type: str | None = None
    running_version: str | None = None
    all_compatible: bool = False                 # every device of the image's type
    strategy: Strategy = Strategy()
    allow_downgrade: bool = False                # required to roll devices back to an older version
    idempotency_key: str | None = Field(default=None, max_length=64)


def target_dict(t) -> dict:
    d = t.device
    return {"id": t.id, "device_id": t.device_id, "mac_address": d.mac_address, "device_name": d.device_name,
            "device_type": d.device_type, "stage": t.stage, "state": t.state, "attempts": t.attempts,
            "from_version": t.from_version, "final_version": t.final_version, "error": t.error,
            "error_code": t.error_code, "started_at": t.started_at, "updated_at": t.updated_at,
            "finished_at": t.finished_at, "is_connected": d.is_connected}


def deployment_dict(dep: FirmwareDeployment, with_targets=True) -> dict:
    counts: dict[str, int] = {}
    for t in dep.targets:
        counts[t.state] = counts.get(t.state, 0) + 1
    a = dep.artifact
    out = {"id": dep.id, "artifact_id": dep.artifact_id, "target": a.target, "version": a.version,
           "kind": dep.kind, "state": dep.state, "note": dep.note, "strategy": engine.strategy_of(dep),
           "requested_by": dep.requested_by, "created_at": dep.created_at, "started_at": dep.started_at,
           "finished_at": dep.finished_at, "total": len(dep.targets), "counts": counts,
           "stages": max((t.stage for t in dep.targets), default=0) + 1}
    if with_targets:
        out["targets"] = [target_dict(t) for t in dep.targets]
    return out


async def _get(db, dep_id) -> FirmwareDeployment:
    dep = await db.get(FirmwareDeployment, dep_id)
    if dep is None:
        raise HTTPException(404, "Deployment not found")
    return dep


@router.post("")
async def create_deployment(
    body: DeploymentCreate,
    dry_run: bool = Query(False, description="only show which devices would be included"),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Roll an approved image out to the selected devices: canary first, then
    batches. Devices that can't take it (wrong type, disabled, already on it,
    busy in another deployment, a downgrade without allow_downgrade) are
    excluded with the reason. The same idempotency_key returns the deployment
    it created before."""
    if body.idempotency_key:
        prior = (await db.execute(select(FirmwareDeployment).where(
            FirmwareDeployment.idempotency_key == body.idempotency_key))).scalar_one_or_none()
        if prior is not None:
            return {"deployment": deployment_dict(prior), "excluded": [], "replayed": True}
    artifact = await db.get(FirmwareArtifact, body.artifact_id)
    if artifact is None:
        raise HTTPException(404, "Firmware not found")
    if artifact.status != "approved":
        raise HTTPException(409, f"{artifact.target} {artifact.version} is {artifact.status}; only approved images deploy")
    if not (body.device_ids or body.class_id is not None or body.device_type or body.running_version
            or body.all_compatible):
        raise HTTPException(422, "Select devices: device_ids, class_id, device_type, running_version or all_compatible")
    devices = await engine.select_devices(
        db, artifact, device_ids=body.device_ids, class_id=body.class_id,
        device_type=body.device_type or (artifact.target if body.all_compatible else None),
        running_version=body.running_version)
    if dry_run:
        excluded = [{"device_id": d.id, "mac_address": d.mac_address, "reason": r} for d in devices
                    if (r := await engine.exclusion_reason(db, artifact, d, body.allow_downgrade))]
        skip = {e["device_id"] for e in excluded}
        ok = [d for d in devices if d.id not in skip]
        plan = engine.stages(len(ok), body.strategy.canary, body.strategy.batch_size)
        return {"included": [{"device_id": d.id, "mac_address": d.mac_address, "stage": s,
                              "from_version": d.firmware_version} for d, s in zip(ok, plan)],
                "excluded": excluded}
    dep, excluded = await engine.create_deployment(
        db, artifact, devices, user_id=user.id, strategy=body.strategy.model_dump(),
        allow_downgrade=body.allow_downgrade, idempotency_key=body.idempotency_key)
    if dep is None:
        raise HTTPException(409, {"message": "No selected device can take this image", "excluded": excluded})
    await engine.advance(db, dep)                     # start the canary now
    await log_activity(db, "deployment.create", user.id, "deployment", dep.id, {
        "artifact_id": artifact.id, "target": artifact.target, "version": artifact.version,
        "devices": len(dep.targets), "excluded": len(excluded), "kind": dep.kind})
    await commit_or_conflict(db, "A device was added to another deployment at the same time; retry")
    dep = await _get(db, dep.id)
    return {"deployment": deployment_dict(dep), "excluded": excluded, "replayed": False}


@router.get("")
async def list_deployments(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    deps = (await db.execute(select(FirmwareDeployment).order_by(FirmwareDeployment.id.desc()).limit(200))).scalars()
    return [deployment_dict(d, with_targets=False) for d in deps]


@router.get("/{dep_id}")
async def get_deployment(dep_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return deployment_dict(await _get(db, dep_id))


async def _act(db, user, dep_id, action):
    dep = await _get(db, dep_id)
    if action == "pause":
        if dep.state != "running":
            raise HTTPException(409, f"Deployment is {dep.state}")
        dep.state, dep.note = "paused", "paused by an administrator"
    elif action == "resume":
        if dep.state != "paused":
            raise HTTPException(409, f"Deployment is {dep.state}")
        engine.resume(dep)
        await engine.advance(db, dep)
    elif action == "cancel":
        if dep.state not in ("running", "paused"):
            raise HTTPException(409, f"Deployment is {dep.state}")
        engine.cancel(dep)
    await log_activity(db, f"deployment.{action}", user.id, "deployment", dep.id, {})
    await db.commit()
    return deployment_dict(await _get(db, dep_id))


@router.post("/{dep_id}/pause")
async def pause_deployment(dep_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await _act(db, user, dep_id, "pause")


@router.post("/{dep_id}/resume")
async def resume_deployment(dep_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Continue a paused deployment, accepting the failures that paused it."""
    return await _act(db, user, dep_id, "resume")


@router.post("/{dep_id}/cancel")
async def cancel_deployment(dep_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Cancel devices that haven't started installing; the rest finish."""
    return await _act(db, user, dep_id, "cancel")
