"""WebSocket endpoint handler for class rooms."""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from .manager import manager
from ..config import settings
from ..database import async_session
from ..models import EspDevice, ClassSession
from ..services.presence import mark_online, _push_after_commit
from ..timeutil import istnow

logger = logging.getLogger(__name__)
router = APIRouter()


async def _touch_device_on_message(class_id: int, msg: dict | None) -> None:
    """Refresh presence for the device that spoke over WS.

    The C6's primary heartbeat path is HTTP POST /api/device/heartbeat; this
    guards the WS path so that any WS message from a role=device connection
    (ping, heartbeat, device_data) proves the gateway is alive and refreshes
    EspDevice.last_seen / is_connected. Best-effort, own DB session.
    """
    msg = msg or {}
    mac = msg.get("device_mac") or msg.get("mac_address") or ""
    try:
        async with async_session() as db:
            device = None
            if mac:
                result = await db.execute(
                    select(EspDevice).where(EspDevice.mac_address == mac)
                )
                device = result.scalar_one_or_none()
            if device is None:
                # Fall back to this class's gateway device.
                result = await db.execute(
                    select(ClassSession).where(ClassSession.id == class_id)
                )
                cls = result.scalar_one_or_none()
                if cls and cls.device_id:
                    result = await db.execute(
                        select(EspDevice).where(EspDevice.id == cls.device_id)
                    )
                    device = result.scalar_one_or_none()
            if not device:
                return
            device.last_seen = istnow()
            if isinstance(msg.get("battery_pct"), int):
                device.battery_pct = msg["battery_pct"]
            if isinstance(msg.get("rssi"), int):
                device.rssi = msg["rssi"]
            await mark_online(db, device)
            await db.commit()
            asyncio.create_task(_push_after_commit(device.id))
    except Exception as e:
        logger.warning("WS device presence update failed: %s", e)


async def _ws_user_from_token(token: str):
    """Validate a login session token for WebSocket auth. Returns the User or None.

    Login issues opaque server-side session tokens (auth.create_session), not
    JWTs, so this must use the same check as the HTTP API. refresh_activity is
    off: an open socket must not keep an idle session alive.
    """
    if not token:
        return None
    from ..auth import validate_session
    async with async_session() as db:
        _session, user, error = await validate_session(db, token, refresh_activity=False)
    return user if error is None else None


@router.websocket("/ws/class/{class_id}")
async def class_websocket(websocket: WebSocket, class_id: int):
    """
    WebSocket endpoint for real-time class communication.

    Connect with: ws://host/ws/class/{class_id}?role=teacher|device&api_key=...&token=...

    Roles:
      - teacher   (browser): must present ?token=<login session token> (teacher/admin/super_admin)
      - device    (C6):      must present ?api_key=<settings.DEVICE_API_KEY>

    Teacher connections receive:
      - quiz_question, quiz_end
      - poll_start, poll_end, poll_vote_received
      - answer_received

    Device (C6) connections receive:
      - command to forward to mesh (quiz questions, polls)
    """
    role = websocket.query_params.get("role", "teacher")

    # ── Auth gate ──────────────────────────────────────────────────────────
    if settings.WS_REQUIRE_AUTH:
        if role == "device":
            if websocket.query_params.get("api_key", "") != settings.DEVICE_API_KEY:
                await websocket.close(code=4401, reason="invalid device api_key")
                return
        elif role == "teacher":
            token = websocket.query_params.get("token", "")
            user = await _ws_user_from_token(token)
            if user is None or user.role not in ("teacher", "admin", "super_admin"):
                await websocket.close(code=4401, reason="unauthorized teacher token")
                return
        else:
            await websocket.close(code=4400, reason="invalid role")
            return
    elif role not in ("teacher", "device"):
        await websocket.close(code=4400, reason="invalid role")
        return

    await manager.connect(websocket, class_id, role)
    logger.info(f"WS connected: class={class_id}, role={role}")

    try:
        # Send connection confirmation
        await websocket.send_json({
            "event": "connected",
            "class_id": class_id,
            "role": role,
            "message": f"Connected to class {class_id} as {role}",
        })

        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            msg = json.loads(data)

            if role == "device":
                # Any message from the gateway proves it is alive — refresh presence.
                asyncio.create_task(_touch_device_on_message(class_id, msg))

            event = msg.get("event", "")

            if event == "ping":
                await websocket.send_json({"event": "pong"})

            elif event == "broadcast_command":
                # Teacher sends command to all devices (e.g., start quiz)
                # Forward to device connections
                await manager.broadcast_to_class(class_id, {
                    "event": "device_command",
                    "command": msg.get("command"),
                    "payload": msg.get("payload", {}),
                })

            elif event == "device_data":
                # C6 device sends student data batch
                # Forward to teacher connections
                await manager.broadcast_to_class(class_id, {
                    "event": "student_data",
                    "data": msg.get("data", {}),
                })

            else:
                logger.warning(f"Unknown WS event: {event}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, class_id)
        logger.info(f"WS disconnected: class={class_id}, role={role}")
    except Exception as e:
        logger.error(f"WS error: {e}")
        manager.disconnect(websocket, class_id)
