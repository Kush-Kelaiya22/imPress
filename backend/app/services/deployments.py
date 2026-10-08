"""Firmware deployments: the OTA state machine and the staged rollout (#34, #38).

Per device (DeploymentTarget.state):

    waiting ─► queued ─► precheck ─► downloading ─► verifying ─► installing ─► rebooting ─► health_check
       │          │                                                                              │
       │          └──► cancelled (only before an unsafe step)                         success ◄──┤
       │                                                                          rolled_back ◄──┤
       └─ (later stage)        any active state ──► failed / timed_out / unreachable / incompatible

- `waiting` targets belong to a stage that hasn't started; `queued` ones
  have been offered the update (pending_version set, prompt sent).
- Devices may only move forward; repeating the current state is a no-op
  (lost acks, relay duplicates). `success` requires the expected version
  running after the reboot; anything else is a failure.
- failed / timed_out / unreachable are retried up to `max_attempts`.
- Stages: stage 0 is the canary, then batches. When every target of a stage
  is final, more than `max_failures` failures pauses the deployment; else
  the next stage starts. At most `max_concurrent` targets are active at once.
- All state is in the database; `advance()` is idempotent and run by a
  loop, so a backend restart simply resumes.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ActivityLog, ClassSession, DeploymentTarget, EspDevice, FirmwareArtifact, FirmwareDeployment
from ..timeutil import istnow
from .firmware_signing import site_key_digest
from .mesh_bridge import send_command_to_devices

log = logging.getLogger(__name__)

FLOW = ["waiting", "queued", "precheck", "downloading", "verifying", "installing", "rebooting", "health_check"]
ACTIVE = tuple(FLOW[1:])                       # offered the update, not finished
FINAL = ("success", "rolled_back", "failed", "cancelled", "timed_out", "incompatible", "unreachable")
FAILURES = ("rolled_back", "failed", "timed_out", "unreachable")
RETRYABLE = ("failed", "timed_out", "unreachable")
CANCELLABLE = ("waiting", "queued", "precheck")  # nothing written to flash yet
DEVICE_STATES = set(FLOW[2:]) | {"success", "rolled_back", "failed"}   # what a device may report

DEFAULT_STRATEGY = {"canary": 1, "batch_size": 5, "max_concurrent": 5, "max_failures": 0,
                    "max_attempts": 2, "timeout_s": 900,
                    "ack_through_stage": -1}   # stages whose failures an admin accepted (resume)

SWEEP_INTERVAL_S = 5


class TransitionError(ValueError):
    pass


def semver(v: str) -> tuple[int, ...] | None:
    try:
        parts = tuple(int(x) for x in (v or "").split("."))
        return parts if len(parts) == 3 else None
    except ValueError:
        return None


def strategy_of(dep: FirmwareDeployment) -> dict:
    return {**DEFAULT_STRATEGY, **(dep.strategy or {})}


# ── Planning ─────────────────────────────────────────────────────────────

async def select_devices(db: AsyncSession, artifact: FirmwareArtifact, *, device_ids=None, class_id=None,
                         device_type=None, running_version=None) -> list[EspDevice]:
    """Resolve a selection (any combination narrows it) to devices."""
    q = select(EspDevice)
    if device_ids:
        q = q.where(EspDevice.id.in_(device_ids))
    if device_type:
        q = q.where(EspDevice.device_type == device_type)
    if running_version:
        q = q.where(EspDevice.firmware_version == running_version)
    devices = list((await db.execute(q.order_by(EspDevice.id))).scalars())
    if class_id is not None:
        cls = await db.get(ClassSession, class_id)
        node = cls.device_id if cls else None
        devices = [d for d in devices if node is not None and (d.id == node or d.gateway_id == node)]
    return devices


async def exclusion_reason(db: AsyncSession, artifact: FirmwareArtifact, device: EspDevice,
                           allow_downgrade: bool) -> str | None:
    if (device.device_type or "").lower() != artifact.target:
        return f"incompatible: a {device.device_type} device can't run a {artifact.target} image"
    if device.device_type == "student":
        return "no over-the-air path to student modules yet (update over serial)"
    if not device.is_active:
        return "device is disabled"
    site = site_key_digest()
    if site and artifact.signer != site:
        return "image is not signed with the site firmware key (#66)"
    if device.firmware_version == artifact.version:
        return f"already running {artifact.version}"
    current, target = semver(device.firmware_version), semver(artifact.version)
    if current and target and target < current and not allow_downgrade:
        return f"would downgrade {device.firmware_version} → {artifact.version} (confirm a rollback)"
    busy = (await db.execute(select(DeploymentTarget.deployment_id).join(FirmwareDeployment).where(
        DeploymentTarget.device_id == device.id,
        DeploymentTarget.state.in_(("waiting",) + ACTIVE),
        FirmwareDeployment.state.in_(("running", "paused"))))).scalar_one_or_none()
    if busy:
        return f"already in deployment #{busy}"
    return None


def stages(n: int, canary: int, batch_size: int) -> list[int]:
    """Stage number for each of n targets: canary (0) first, then batches."""
    c = min(canary, n)
    return [0] * c + [1 + i // max(batch_size, 1) for i in range(n - c)]


async def create_deployment(db: AsyncSession, artifact: FirmwareArtifact, devices: list[EspDevice], *,
                            user_id: int | None, strategy: dict | None = None, allow_downgrade=False,
                            idempotency_key: str | None = None) -> tuple[FirmwareDeployment, list[dict]]:
    """Create a deployment for the eligible devices. Returns (deployment,
    excluded=[{device_id, reason}]). Not committed."""
    included, excluded = [], []
    for d in devices:
        reason = await exclusion_reason(db, artifact, d, allow_downgrade)
        if reason:
            excluded.append({"device_id": d.id, "mac_address": d.mac_address, "reason": reason})
        else:
            included.append(d)
    if not included:
        return None, excluded
    st = {**DEFAULT_STRATEGY, **{k: v for k, v in (strategy or {}).items() if k in DEFAULT_STRATEGY}}
    downgrade = any(semver(d.firmware_version) and semver(artifact.version) < semver(d.firmware_version)
                    for d in included)
    dep = FirmwareDeployment(artifact_id=artifact.id, kind="rollback" if downgrade else "update",
                             strategy=st, requested_by=user_id, idempotency_key=idempotency_key,
                             started_at=istnow())
    db.add(dep)
    await db.flush()
    for d, stage in zip(included, stages(len(included), st["canary"], st["batch_size"])):
        db.add(DeploymentTarget(deployment_id=dep.id, device_id=d.id, stage=stage, state="waiting",
                                from_version=d.firmware_version or ""))
    await db.flush()
    await db.refresh(dep, ["targets"])
    return dep, excluded


# ── Device side ──────────────────────────────────────────────────────────

async def active_target(db: AsyncSession, device: EspDevice) -> DeploymentTarget | None:
    """The device's update in progress. A cancelled or paused deployment can
    still have one: a device that started installing finishes and reports."""
    return (await db.execute(select(DeploymentTarget).where(
        DeploymentTarget.device_id == device.id, DeploymentTarget.state.in_(ACTIVE)))).scalars().first()


def _sync_device(t: DeploymentTarget, retry_left: bool = False) -> None:
    """Mirror the target onto the device row (what the Modules page shows).
    A failure that will be retried keeps pending_version."""
    d = t.device
    d.ota_status = t.state
    if t.state == "success":
        d.firmware_version, d.pending_version = t.final_version, ""
    elif t.state in FINAL and not retry_left:
        d.pending_version = ""


def _finish(t: DeploymentTarget, state: str, error: str = "", code: int | None = None) -> None:
    now = istnow()
    t.state, t.updated_at = state, now
    if state in FINAL:
        t.finished_at = now
    if error:
        t.error = error[:255]
    if code is not None:
        t.error_code = code


async def report(db: AsyncSession, device: EspDevice, state: str, version: str = "",
                 error: str = "", error_code: int | None = None) -> DeploymentTarget | None:
    """Apply a state the device reported. Returns the target, or None when the
    device has no update in progress. Raises TransitionError for a backwards
    or unknown transition (a repeat of the current state is a no-op)."""
    if state not in DEVICE_STATES:
        raise TransitionError(f"unknown state '{state}'")
    t = await active_target(db, device)
    if t is None:
        return None
    if state == t.state:
        return t                                            # duplicate report
    if state in FLOW and FLOW.index(state) < FLOW.index(t.state):
        raise TransitionError(f"{t.state} → {state} goes backwards")
    artifact = t.deployment.artifact
    if state == "success":
        t.final_version = version
        if version != artifact.version:
            state, error = "failed", f"device runs {version or '?'} after the update, expected {artifact.version}"
            if version:
                device.firmware_version = version          # record what really runs
    elif state == "rolled_back":
        t.final_version = t.from_version                   # the old image runs; `version` is the one that failed
    _finish(t, state, error, error_code)
    st = strategy_of(t.deployment)
    _sync_device(t, retry_left=state in RETRYABLE and t.attempts < st["max_attempts"])
    db.add(ActivityLog(action="deployment.device_state", entity_type="device", entity_id=device.id, details={
        "deployment_id": t.deployment_id, "state": state, "version": version or artifact.version,
        "error": error, "error_code": error_code}))
    return t


async def observe_download(db: AsyncSession, device: EspDevice) -> None:
    """The server saw the device start the download: at least 'downloading'."""
    t = await active_target(db, device)
    if t is not None and FLOW.index(t.state) < FLOW.index("downloading"):
        _finish(t, "downloading")
        _sync_device(t)


# ── Scheduler ────────────────────────────────────────────────────────────

async def _route_class(db: AsyncSession, device: EspDevice) -> int | None:
    """The class room whose gateway can reach this device (C6 itself, or the
    C6 relaying an S3)."""
    node = device.id if device.device_type == "c6" else device.gateway_id
    if node is None:
        return None
    return (await db.execute(select(ClassSession.id).where(ClassSession.device_id == node))).scalars().first()


async def _offer(db: AsyncSession, t: DeploymentTarget, artifact: FirmwareArtifact, user_id) -> None:
    """Make the update available to the device and prompt it."""
    now = istnow()
    t.state, t.attempts, t.started_at, t.updated_at = "queued", t.attempts + 1, now, now
    t.finished_at, t.error, t.error_code = None, "", None
    d = t.device
    d.pending_version, d.ota_status, d.ota_requested_at = artifact.version, "queued", now
    class_id = await _route_class(db, d)
    if class_id is not None:
        await send_command_to_devices(class_id, "ota_update", {
            "device_type": d.device_type, "version": artifact.version, "mac_address": d.mac_address})
        db.add(ActivityLog(action="module.ota.prompt", user_id=user_id, entity_type="device",
                           entity_id=d.gateway_id if d.device_type != "c6" else d.id,
                           details={"to_class": class_id, "version": artifact.version}))


async def advance(db: AsyncSession, dep: FirmwareDeployment) -> None:
    """Move one deployment forward: timeouts, retries, stage progression,
    activation within the concurrency limit, completion. Idempotent."""
    if dep.state != "running":
        return
    st, artifact, now = strategy_of(dep), dep.artifact, istnow()
    targets = list(dep.targets)

    for t in targets:                                      # timeouts
        if t.state in ACTIVE and t.started_at and now - t.started_at > timedelta(seconds=st["timeout_s"]):
            _finish(t, "unreachable" if t.state == "queued" else "timed_out",
                    f"not finished within {st['timeout_s']} s (last state {t.state})")
            _sync_device(t, retry_left=t.attempts < st["max_attempts"])
    for t in targets:                                      # bounded retries
        if t.state in RETRYABLE and t.attempts < st["max_attempts"]:
            t.state = "waiting"

    stage_nums = sorted({t.stage for t in targets})
    current = next((s for s in stage_nums if any(t.stage == s and t.state not in FINAL for t in targets)), None)
    if current is None:
        dep.state, dep.finished_at = "completed", now
        return
    # a later stage only starts when every earlier stage passed its health check
    for s in stage_nums:
        if s >= current:
            break
        if s <= st["ack_through_stage"]:
            continue
        failed = sum(t.state in FAILURES for t in targets if t.stage == s)
        if failed > st["max_failures"]:
            dep.state = "paused"
            dep.note = f"stage {s} ({'canary' if s == 0 else 'batch ' + str(s)}): {failed} device(s) failed"
            log.warning("Deployment %s paused: %s", dep.id, dep.note)
            return

    active = sum(t.state in ACTIVE for t in targets)
    for t in (t for t in targets if t.stage == current and t.state == "waiting"):
        if active >= st["max_concurrent"]:
            break
        await _offer(db, t, artifact, dep.requested_by)
        active += 1


async def advance_all(db: AsyncSession) -> int:
    deps = list((await db.execute(select(FirmwareDeployment).where(FirmwareDeployment.state == "running"))).scalars())
    for dep in deps:
        await advance(db, dep)
    return len(deps)


def resume(dep: FirmwareDeployment) -> None:
    """Continue a paused deployment: the failures that paused it are accepted."""
    st = strategy_of(dep)
    done = [t.stage for t in dep.targets if t.state in FINAL]
    dep.strategy = {**st, "ack_through_stage": max(done, default=-1)}
    dep.state, dep.note = "running", ""


def cancel(dep: FirmwareDeployment) -> int:
    """Cancel targets that haven't written anything yet; the rest finish."""
    n = 0
    for t in dep.targets:
        if t.state in CANCELLABLE:
            _finish(t, "cancelled")
            _sync_device(t)
            n += 1
    dep.state, dep.finished_at = "cancelled", istnow()
    return n


async def deployments_loop():
    """Background task: advance running deployments (durable across restarts)."""
    import asyncio

    from ..database import async_session
    log.info("Deployment scheduler started (interval=%ss)", SWEEP_INTERVAL_S)
    while True:
        try:
            await asyncio.sleep(SWEEP_INTERVAL_S)
            async with async_session() as db:
                if await advance_all(db):
                    await db.commit()
        except asyncio.CancelledError:
            return
        except Exception as e:  # keep the loop alive on transient errors
            log.warning("Deployment scheduler error: %s", e)
