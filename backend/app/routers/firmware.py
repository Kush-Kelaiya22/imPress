"""Firmware version manager (#35 upload/registry, #36 lifecycle).

Lifecycle of an image: uploaded → approved → deprecated (re-approval allowed).
Only approved images can be pushed. Binaries are immutable; only the channel
and release notes can be edited. Deletion is refused for anything a device
runs or is about to install (rollback candidates), and for approved images.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..activity import log_activity
from ..auth import require_admin
from ..database import commit_or_conflict, get_db
from ..models import ActivityLog, EspDevice, FirmwareArtifact, User
from ..schemas import FirmwareArtifactResponse
from ..services.firmware_store import artifact_path, store_upload
from ..timeutil import istnow

router = APIRouter(prefix="/api/admin/firmware", tags=["firmware"])


class FirmwareUpdate(BaseModel):
    channel: str | None = Field(default=None, pattern="^(stable|beta)$")
    release_notes: str | None = Field(default=None, max_length=5000)


def _semver(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


async def _usage(db: AsyncSession) -> dict[tuple[str, str], dict[str, int]]:
    """(target, version) -> {running, pending} device counts."""
    out: dict[tuple[str, str], dict[str, int]] = {}
    for d in (await db.execute(select(EspDevice))).scalars():
        t = (d.device_type or "").lower()
        if d.firmware_version:
            out.setdefault((t, d.firmware_version), {"running": 0, "pending": 0})["running"] += 1
        if d.pending_version:
            out.setdefault((t, d.pending_version), {"running": 0, "pending": 0})["pending"] += 1
    return out


def _response(a: FirmwareArtifact, usage: dict, latest: dict[str, int]) -> FirmwareArtifactResponse:
    r = FirmwareArtifactResponse.model_validate(a)
    u = usage.get((a.target, a.version), {})
    r.devices_running, r.devices_pending = u.get("running", 0), u.get("pending", 0)
    r.latest_approved = latest.get(a.target) == a.id
    return r


def _latest_approved(artifacts: list[FirmwareArtifact]) -> dict[str, int]:
    best: dict[str, FirmwareArtifact] = {}
    for a in artifacts:
        if a.status == "approved" and (a.target not in best or _semver(a.version) > _semver(best[a.target].version)):
            best[a.target] = a
    return {t: a.id for t, a in best.items()}


async def _get(db: AsyncSession, artifact_id: int) -> FirmwareArtifact:
    a = await db.get(FirmwareArtifact, artifact_id)
    if a is None:
        raise HTTPException(404, "Firmware not found")
    return a


async def _register_upload(db, user, file, **kw) -> FirmwareArtifactResponse:
    artifact, created = await store_upload(db, file, user.id, **kw)
    if created:
        await log_activity(db, "firmware.upload", user.id, "firmware", artifact.id, {
            "target": artifact.target, "version": artifact.version, "sha256": artifact.sha256,
            "size": artifact.size, "filename": file.filename or ""})
    await commit_or_conflict(db, "This version was registered by a concurrent upload; reload")
    resp = FirmwareArtifactResponse.model_validate(artifact)
    resp.created = created
    return resp


@router.post("", response_model=FirmwareArtifactResponse)
async def upload_firmware_image(
    file: UploadFile = File(...),
    channel: str = Form("stable"),
    release_notes: str = Form(""),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload a firmware image. Target, chip and version are read from the
    image (422 if it isn't a valid imPress app image). Re-uploading identical
    bytes is a no-op; a different image under an existing version is 409."""
    return await _register_upload(db, user, file, channel=channel, release_notes=release_notes)


@router.post("/upload", response_model=FirmwareArtifactResponse)
async def upload_firmware_form(
    device_type: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pre-v2.1 form upload, kept for scripts: device_type and version must
    match what the image says."""
    if device_type not in ("c6", "s3", "student"):
        raise HTTPException(400, "device_type must be c6 | s3 | student")
    return await _register_upload(db, user, file, device_type=device_type, version=version)


@router.get("", response_model=list[FirmwareArtifactResponse])
async def list_firmware(
    target: str = Query("", description="c6 | s3 | student"),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Every registered image, newest version first per target, with how many
    devices run it or are about to install it."""
    artifacts = list((await db.execute(select(FirmwareArtifact))).scalars())
    latest, usage = _latest_approved(artifacts), await _usage(db)
    if target:
        artifacts = [a for a in artifacts if a.target == target]
    artifacts.sort(key=lambda a: (a.target, [-n for n in _semver(a.version)]))   # newest first per target
    return [_response(a, usage, latest) for a in artifacts]


@router.get("/{artifact_id}")
async def firmware_detail(
    artifact_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """One image: metadata, the devices running / pending it, and its history
    (upload, approval, pushes, device-reported results)."""
    a = await _get(db, artifact_id)
    artifacts = list((await db.execute(select(FirmwareArtifact).where(FirmwareArtifact.target == a.target))).scalars())
    devices = list((await db.execute(select(EspDevice).where(
        EspDevice.device_type == a.target,
        or_(EspDevice.firmware_version == a.version, EspDevice.pending_version == a.version)))).scalars())
    logs = (await db.execute(select(ActivityLog).where(or_(
        (ActivityLog.entity_type == "firmware") & (ActivityLog.entity_id == a.id),
        ActivityLog.action.in_(("module.ota", "module.ota_result")),
    )).order_by(ActivityLog.timestamp.desc(), ActivityLog.id.desc()).limit(500))).scalars()
    history = [{"action": l.action, "timestamp": l.timestamp, "user_id": l.user_id, "device_id": l.entity_id
                if l.entity_type == "device" else None, "details": l.details} for l in logs
               if l.entity_type == "firmware" or (l.details or {}).get("version") == a.version
               or (l.details or {}).get("to_version") == a.version]
    return {
        "artifact": _response(a, await _usage(db), _latest_approved(artifacts)),
        "devices": [{"id": d.id, "mac_address": d.mac_address, "device_name": d.device_name,
                     "firmware_version": d.firmware_version, "pending_version": d.pending_version,
                     "ota_status": d.ota_status, "is_connected": d.is_connected} for d in devices],
        "history": history[:100],
    }


@router.patch("/{artifact_id}", response_model=FirmwareArtifactResponse)
async def update_firmware(
    artifact_id: int,
    body: FirmwareUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Edit channel / release notes. The binary itself is immutable."""
    a = await _get(db, artifact_id)
    changed = body.model_dump(exclude_none=True)
    for k, v in changed.items():
        setattr(a, k, v)
    await log_activity(db, "firmware.update", user.id, "firmware", a.id, changed)
    await db.commit()
    return FirmwareArtifactResponse.model_validate(a)


@router.post("/{artifact_id}/approve", response_model=FirmwareArtifactResponse)
async def approve_firmware(
    artifact_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Allow this image to be pushed to devices."""
    a = await _get(db, artifact_id)
    if a.status == "approved":
        return FirmwareArtifactResponse.model_validate(a)
    a.status, a.approved_by, a.approved_at, a.deprecated_at = "approved", user.id, istnow(), None
    await log_activity(db, "firmware.approve", user.id, "firmware", a.id, {"target": a.target, "version": a.version})
    await db.commit()
    return FirmwareArtifactResponse.model_validate(a)


@router.post("/{artifact_id}/deprecate", response_model=FirmwareArtifactResponse)
async def deprecate_firmware(
    artifact_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stop offering this image for new pushes. Devices already running it,
    or with it pending, are not affected (the file is kept)."""
    a = await _get(db, artifact_id)
    if a.status == "deprecated":
        return FirmwareArtifactResponse.model_validate(a)
    a.status, a.deprecated_at = "deprecated", istnow()
    await log_activity(db, "firmware.deprecate", user.id, "firmware", a.id, {"target": a.target, "version": a.version})
    await db.commit()
    return FirmwareArtifactResponse.model_validate(a)


@router.delete("/{artifact_id}")
async def delete_firmware(
    artifact_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an image that nothing needs. Refused (409) while it is approved,
    while a device runs it (the rollback path) or has it pending."""
    a = await _get(db, artifact_id)
    if a.status == "approved":
        raise HTTPException(409, "Deprecate the image before deleting it")
    use = (await _usage(db)).get((a.target, a.version), {})
    if use.get("running") or use.get("pending"):
        raise HTTPException(409, f"{use.get('running', 0)} device(s) run this version and "
                                 f"{use.get('pending', 0)} have it pending; it is kept for recovery")
    path = artifact_path(a.sha256)
    await log_activity(db, "firmware.delete", user.id, "firmware", a.id,
                       {"target": a.target, "version": a.version, "sha256": a.sha256})
    await db.delete(a)
    await db.commit()
    path.unlink(missing_ok=True)
    return {"status": "deleted", "id": artifact_id}
