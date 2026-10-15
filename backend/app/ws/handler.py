"""WebSocket endpoint handler for class rooms."""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from .manager import manager
from .. import gpc
from ..config import settings
from ..database import async_session
from ..models import EspDevice, ClassSession
from ..policy import is_staff
from ..transport import https_required, is_loopback
from ..services.presence import mark_online, _push_after_commit
from ..timeutil import istnow

logger = logging.getLogger(__name__)
router = APIRouter()


async def _device_refusal(key: str | None, class_id: int) -> tuple[int, str] | None:
    """Why a device may not join this class room, or None (#66, #121).

    A per-device key identifies the gateway: it may join only the class it is
    linked to (class_sessions.device_id). The shared provisioning key names no
    device, so it can't be bound to a class; it is accepted only while
    IMPRESS_DEVICE_KEYS_REQUIRED is off (firmware from before #66)."""
    from ..device_auth import caller_for_key
    async with async_session() as db:
        caller = await caller_for_key(db, key)
        if caller is None:
            return 4401, "invalid device api_key"
        if caller.shared:
            return (4401, "per-device key required") if gpc.device_keys_required(settings) else None
        if caller.device.is_active is False:
            return 4401, "device disabled"
        await db.commit()                       # first use activates the key
        linked = (await db.execute(select(ClassSession.id).where(
            ClassSession.id == class_id, ClassSession.device_id == caller.device.id))).scalar_one_or_none()
        return None if linked else (4403, "device is not linked to this class")


async def _teacher_refusal(user, class_id: int) -> tuple[int, str] | None:
    """The REST class-access rule (primary teacher, co-faculty, admin) (#121)."""
    from ..policy import class_access
    async with async_session() as db:
        cls = (await db.execute(select(ClassSession).where(ClassSession.id == class_id))).scalar_one_or_none()
        if cls is None:
            return 4404, "class not found"
        return None if class_access(user, cls) else (4403, "no access to this class")


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


def _same_origin(websocket: WebSocket) -> bool:
    """A browser sends Origin on every WebSocket handshake; it must name this
    server. Non-browser clients (scripts, tests) send none."""
    origin = websocket.headers.get("origin")
    if origin is None:
        return True
    from urllib.parse import urlsplit
    return urlsplit(origin).netloc.lower() == (websocket.headers.get("host") or "").lower()


async def _refuse(websocket: WebSocket, role: str, code: int, reason: str) -> None:
    """Refuse a socket so that its client can tell why (#160).

    Browsers only see a close code after the handshake succeeded; a refusal
    before accept reaches them as a failed handshake (1006), which looks like
    a network error and makes the page retry forever. So teacher sockets are
    accepted and then closed with the code. Gateways keep the HTTP 403 on the
    handshake, which their firmware reports (#132)."""
    if role == "teacher":
        await websocket.accept()
    await websocket.close(code=code, reason=reason)


@router.websocket("/ws/class/{class_id}")
async def class_websocket(websocket: WebSocket, class_id: int):
    """
    WebSocket endpoint for real-time class communication.

    Connect with: wss://host/ws/class/{class_id}?role=teacher|device

    Roles:
      - teacher   (browser): the login session (HttpOnly cookie, or a bearer header) of a user with
                             access to this class (primary teacher, co-faculty, admin)
      - device    (C6):      must present the device key as an X-API-Key header
                             (or ?api_key= for older firmware); a per-device key
                             joins only the class its gateway is linked to (#121)

    Commands for the devices come from the server (services/mesh_bridge.py),
    never relayed from a browser socket (#121).

    Teacher connections receive:
      - quiz_question, quiz_end
      - poll_start, poll_end, poll_vote_received
      - answer_received

    Device (C6) connections receive:
      - command to forward to mesh (quiz questions, polls)
    """
    role = websocket.query_params.get("role", "teacher")
    user = None

    # Teachers' sockets carry the session token: wss:// only (#152). Devices
    # follow IMPRESS_DEVICE_HTTPS_ONLY.
    client = websocket.client.host if websocket.client else None
    if (https_required() and websocket.url.scheme != "wss" and not is_loopback(client)
            and (role != "device" or gpc.device_https_only(settings))):
        await _refuse(websocket, role, 4403, "wss:// required")
        return

    # ── Auth gate ──────────────────────────────────────────────────────────
    if settings.WS_REQUIRE_AUTH:
        if role == "device":
            key = websocket.headers.get("x-api-key") or websocket.query_params.get("api_key")
            refusal = await _device_refusal(key, class_id)
            if refusal:
                await _refuse(websocket, role, refusal[0], refusal[1])
                return
        elif role == "teacher":
            # The browser's session cookie (or a bearer header from a script),
            # never a URL parameter. Browsers send cookies on cross-site
            # WebSocket handshakes too, so the page must be one of ours.
            if not _same_origin(websocket):
                await _refuse(websocket, role, 4403, "cross-site WebSocket refused")
                return
            from ..auth import session_token_from
            user = await _ws_user_from_token(session_token_from(websocket))
            if not is_staff(user):
                await _refuse(websocket, role, 4401, "unauthorized teacher token")
                return
            refusal = await _teacher_refusal(user, class_id)
            if refusal:
                await _refuse(websocket, role, refusal[0], refusal[1])
                return
        else:
            await _refuse(websocket, role, 4400, "invalid role")
            return
    elif role not in ("teacher", "device"):
        await _refuse(websocket, role, 4400, "invalid role")
        return

    from ..dbgateway import ANONYMOUS, act_as, as_device, as_user
    act_as(as_user(user) if user is not None else as_device(None) if role == "device" else ANONYMOUS)
    await manager.connect(websocket, class_id, role, user_id=user.id if user is not None else None)
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

            elif event == "device_data" and role == "device":
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
