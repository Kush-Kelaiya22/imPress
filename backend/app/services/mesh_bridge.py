"""Bridge service: connects ESP device data to WebSocket clients.

This service provides functions that can be called from device endpoints
to push data to connected frontend clients via WebSocket.
"""

from ..ws.manager import manager


async def push_student_data(class_id: int, data: dict):
    """Push student device data (heartbeats, answers, votes) to teacher dashboard."""
    await manager.broadcast_to_class(class_id, {
        "event": "student_data",
        "data": data,
    })


async def push_device_status(class_id: int, device_id: int, status: dict):
    """Push individual device status update."""
    await manager.broadcast_to_class(class_id, {
        "event": "device_status",
        "device_id": device_id,
        "status": status,
    })


async def send_command_to_devices(class_id: int, command: str, payload: dict):
    """Send a command to C6 devices connected via WebSocket."""
    await manager.broadcast_to_class(class_id, {
        "event": "device_command",
        "command": command,
        "payload": payload,
    })


async def push_quiz_to_mesh(class_id: int, question_data: dict):
    """Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students."""
    await manager.broadcast_to_class(class_id, {
        "event": "quiz_question",
        **question_data,
    })


async def push_poll_to_mesh(class_id: int, poll_data: dict):
    """Push poll through WebSocket → C6 → SPI → S3 → mesh → students."""
    await manager.broadcast_to_class(class_id, {
        "event": "poll_start",
        **poll_data,
    })
