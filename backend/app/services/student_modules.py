"""Student module inventory (#40): which modules each gateway's mesh can see.

Joins, leaves and heartbeats relayed by a gateway upsert one row per module,
keyed on the firmware's device_id; nothing is kept but the latest state (the
design does not track students physically).
"""

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EspDevice, StudentModule
from ..timeutil import istnow

# Students send a heartbeat every 30 s (firmware/student/main/config.h):
# three missed beats and the module is shown as seen previously.
MODULE_OFFLINE_AFTER_S = 90


def _uid(msg: dict) -> int | None:
    v = msg.get("device_id")
    if isinstance(v, int) and not isinstance(v, bool) and 0 < v <= 0xFFFFFFFF:
        return v
    return None


async def observe(db: AsyncSession, kind: str, msg: dict, gateway: EspDevice | None,
                  class_id: int | None) -> StudentModule | None:
    """Record a join / leave / heartbeat relayed by `gateway`. Returns the row,
    or None when the message identifies no module (the S3's own heartbeat)."""
    uid = _uid(msg)
    roll = (msg.get("enrollment_number") or "").strip().upper()[:16]
    if uid is not None:
        row = await db.scalar(select(StudentModule).where(StudentModule.device_uid == uid))
    elif roll:      # older firmware: no device_id, the enrollment is the only key
        row = await db.scalar(select(StudentModule).where(StudentModule.device_uid.is_(None),
                                                          StudentModule.enrollment_number == roll))
    else:
        return None
    if row is None:
        row = StudentModule(device_uid=uid, enrollment_number=roll, first_seen=istnow())
        db.add(row)
    if kind == "join" and roll:
        row.enrollment_number = roll
    if gateway is not None:
        row.gateway_id = gateway.id
    if class_id is not None:
        row.class_session_id = class_id
    if kind == "heartbeat":
        if isinstance(msg.get("battery_pct"), int):
            row.battery_pct = msg["battery_pct"]
        if isinstance(msg.get("rssi"), int):
            row.rssi = msg["rssi"]
    row.is_connected = kind != "leave"
    row.last_seen = istnow()
    return row


async def sweep(db: AsyncSession) -> list[int]:
    """Mark silent modules disconnected; returns their gateways' ids."""
    cutoff = istnow() - timedelta(seconds=MODULE_OFFLINE_AFTER_S)
    stale = (StudentModule.is_connected.is_(True), StudentModule.last_seen < cutoff)
    gateways = (await db.scalars(select(StudentModule.gateway_id).where(*stale))).all()
    if gateways:
        await db.execute(update(StudentModule).where(*stale).values(is_connected=False))
    return [g for g in set(gateways) if g]


def module_to_dict(m: StudentModule, now: datetime) -> dict:
    ago = int((now - m.last_seen).total_seconds()) if m.last_seen else None
    connected = bool(m.is_connected and ago is not None and ago <= MODULE_OFFLINE_AFTER_S)
    cls = m.class_session
    return {
        "id": m.id,
        "device_uid": f"{m.device_uid:08X}" if m.device_uid is not None else "",
        "enrollment_number": m.enrollment_number or "",
        "state": "connected" if connected else "seen",
        "gateway_id": m.gateway_id,
        "gateway_name": (m.gateway.device_name or m.gateway.mac_address) if m.gateway else "",
        "class_id": m.class_session_id,
        "class_code": cls.code if cls else "",
        "class_name": cls.name if cls else "",
        "section": (cls.course_section or "") if cls else "",
        "battery_pct": m.battery_pct,
        "rssi": m.rssi,
        "first_seen": m.first_seen.isoformat() if m.first_seen else None,
        "last_seen": m.last_seen.isoformat() if m.last_seen else None,
        "last_seen_ago_s": ago,
    }
