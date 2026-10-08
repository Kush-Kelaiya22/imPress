"""ESP device presence monitoring (online/offline logs).

Requirement: the backend keeps a list of all classrooms and ONLY logs when a
classroom ESP (C6 gateway, S3 hub, or a student node) comes online or goes
offline. No telemetry history — just the presence event.

- register / heartbeat mark a device online and log the transition.
- A periodic sweep marks devices offline when their heartbeat goes stale.
- Live presence snapshot + real-time push to teachers over WebSocket.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from ..models import EspDevice, ActivityLog, ClassSession, StudentModule
from . import student_modules
from ..database import async_session
from ..ws.manager import manager
from ..timeutil import istnow, ist_epoch_ms

logger = logging.getLogger(__name__)

# A device is considered offline when it has been silent this long.
OFFLINE_AFTER_S = 30
# How often the offline sweep runs.
SWEEP_INTERVAL_S = 15


async def _log(db, device: EspDevice, action: str, details: dict | None = None):
    """Write a presence entry to the activity log."""
    db.add(ActivityLog(
        user_id=None,
        action=action,               # "esp_device.online" | "esp_device.offline"
        entity_type="esp_device",
        entity_id=device.id,
        details={
            "mac_address": device.mac_address,
            "device_name": device.device_name,
            "device_type": device.device_type,
            **(details or {}),
        },
    ))


async def mark_online(db, device: EspDevice) -> None:
    """Mark a device online, logging only when it transitions offline → online."""
    was_offline = not device.is_connected
    if was_offline:
        await _log(db, device, "esp_device.online",
                   {"reason": "registered or first heartbeat after gap"})
        logger.info("ESP device online: %s (%s)",
                    device.mac_address, device.device_name)
    device.is_connected = True


async def mark_offline(db, device: EspDevice, reason: str = "heartbeat timeout") -> None:
    """Mark a device offline and log the transition."""
    if device.is_connected:
        await _log(db, device, "esp_device.offline", {"reason": reason})
        logger.info("ESP device offline: %s (%s)",
                    device.mac_address, device.device_name)
    device.is_connected = False


async def class_id_for_device(db, device: EspDevice) -> int | None:
    """Walk gateway_id chain up to the class gateway; return ClassSession.id or None."""
    current = device
    visited = set()
    while current and current.id not in visited:
        visited.add(current.id)
        # If this device IS a class gateway, we found the class
        result = await db.execute(
            select(ClassSession).where(ClassSession.device_id == current.id)
        )
        cls = result.scalar_one_or_none()
        if cls:
            return cls.id
        # Otherwise walk up to parent
        if current.gateway_id:
            result = await db.execute(
                select(EspDevice).where(EspDevice.id == current.gateway_id)
            )
            current = result.scalar_one_or_none()
        else:
            break
    return None


def _device_to_dict(device: EspDevice, now: datetime, server_time_ms: int) -> dict:
    """Convert an EspDevice to the presence snapshot dict."""
    last_seen = device.last_seen
    last_seen_ms = ist_epoch_ms(last_seen)
    last_seen_ago_s = int((now - last_seen).total_seconds()) if last_seen else None
    # Online means is_connected AND heartbeat is fresh (within OFFLINE_AFTER_S)
    online = bool(device.is_connected and last_seen and last_seen_ago_s <= OFFLINE_AFTER_S)
    return {
        "id": device.id,
        "mac_address": device.mac_address,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "student_name": device.student_name,
        "is_connected": device.is_connected,
        "online": online,
        "last_seen": last_seen.isoformat() if last_seen else None,
        "last_seen_ms": last_seen_ms,
        "last_seen_ago_s": last_seen_ago_s,
        "rssi": device.rssi,
        "battery_pct": device.battery_pct,
        "student_count": device.student_count,
        "firmware_version": device.firmware_version,
        "gateway_id": device.gateway_id,
    }


async def presence_snapshot(db, class_id: int) -> dict:
    """Full live snapshot of one class's devices: root gateway + relayed tree."""
    now = istnow()
    server_time_ms = ist_epoch_ms(now)

    # Find the root gateway device for this class
    result = await db.execute(
        select(ClassSession).where(ClassSession.id == class_id)
    )
    cls = result.scalar_one_or_none()
    if not cls or not cls.device_id:
        return {
            "class_id": class_id,
            "server_time": now.isoformat(),
            "server_time_ms": server_time_ms,
            "devices": [],
            "online_count": 0,
            "total_count": 0,
            "student_modules": await class_modules(db, class_id, now),
        }

    # Collect all devices in the relay tree (root + children)
    root_device_id = cls.device_id
    all_devices = []

    # Single query for all devices that are in this class's relay tree
    # We need devices where gateway_id chain eventually leads to root_device_id
    # Simplest: query all devices and filter in Python
    result = await db.execute(select(EspDevice))
    all_esp = result.scalars().all()

    # Build parent -> children map
    children_map = {}
    for dev in all_esp:
        children_map.setdefault(dev.gateway_id, []).append(dev)

    # BFS from root
    queue = [root_device_id]
    while queue:
        pid = queue.pop(0)
        for child in children_map.get(pid, []):
            all_devices.append(child)
            queue.append(child.id)

    # Include root device itself
    root_result = await db.execute(select(EspDevice).where(EspDevice.id == root_device_id))
    root_dev = root_result.scalar_one_or_none()
    if root_dev:
        all_devices.insert(0, root_dev)

    devices_data = [_device_to_dict(d, now, server_time_ms) for d in all_devices]
    online_count = sum(1 for d in devices_data if d["online"])
    total_count = len(devices_data)

    return {
        "class_id": class_id,
        "server_time": now.isoformat(),
        "server_time_ms": server_time_ms,
        "devices": devices_data,
        "online_count": online_count,
        "total_count": total_count,
        "student_modules": await class_modules(db, class_id, now),
    }


async def class_modules(db, class_id: int, now: datetime | None = None) -> list[dict]:
    """The class's student modules (#40), connected first."""
    now = now or istnow()
    rows = (await db.scalars(select(StudentModule).where(StudentModule.class_session_id == class_id)
                             .order_by(StudentModule.last_seen.desc()))).all()
    mods = [student_modules.module_to_dict(m, now) for m in rows]
    return sorted(mods, key=lambda m: m["state"] != "connected")


async def push_presence(db, class_id: int) -> None:
    """Build a presence snapshot and broadcast to teacher connections."""
    try:
        snap = await presence_snapshot(db, class_id)
        await manager.broadcast_to_role(
            class_id, {"event": "presence", "type": "presence", "data": snap}, role="teacher"
        )
    except Exception:
        # Presence push is best-effort; never raise
        pass


async def _push_after_commit(device_id: int) -> None:
    """Background task: open new session, resolve class, push presence."""
    from ..database import async_session as _sess
    from ..models import EspDevice
    from sqlalchemy import select
    try:
        async with _sess() as db:
            d = (await db.execute(select(EspDevice).where(EspDevice.id == device_id))).scalar_one_or_none()
            if not d:
                return
            cid = await class_id_for_device(db, d)
            if cid:
                await push_presence(db, cid)
    except Exception:
        pass  # presence push is best-effort


async def _sweep_once() -> int:
    """Mark stale devices offline. Returns number of transitions logged."""
    cutoff = istnow() - timedelta(seconds=OFFLINE_AFTER_S)
    transitions = 0
    offline_devices = []
    async with async_session() as db:
        result = await db.execute(
            select(EspDevice).where(
                EspDevice.is_connected == True,  # noqa: E712
                EspDevice.last_seen < cutoff,
            )
        )
        for device in result.scalars().all():
            await mark_offline(db, device)
            transitions += 1
            offline_devices.append(device.id)
        # Student modules have their own, longer threshold; their gateways'
        # classes get a fresh snapshot. Not counted as device transitions.
        module_gateways = await student_modules.sweep(db)
        offline_devices += module_gateways
        if transitions or module_gateways:
            await db.commit()
    # Trigger presence pushes for devices that went offline (best-effort, new sessions)
    for dev_id in set(offline_devices):
        asyncio.create_task(_push_after_commit(dev_id))
    return transitions


async def presence_sweep_loop():
    """Background task: periodically sweep and log offline transitions."""
    logger.info("ESP presence sweep started (interval=%ss, offline_after=%ss)",
                SWEEP_INTERVAL_S, OFFLINE_AFTER_S)
    while True:
        try:
            await asyncio.sleep(SWEEP_INTERVAL_S)
            n = await _sweep_once()
            if n:
                logger.info("Presence sweep: %d device(s) went offline", n)
        except asyncio.CancelledError:
            logger.info("Presence sweep stopped")
            return
        except Exception as e:  # keep the loop alive on transient errors
            logger.warning("Presence sweep error: %s", e)