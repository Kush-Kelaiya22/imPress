"""WebSocket connection manager for class rooms."""

import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections grouped by class ID.
    Teachers connect to manage quizzes/polls.
    C6 devices connect to receive commands and forward to mesh.
    """

    def __init__(self):
        # class_id → set of websockets (for backward compat)
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # class_id → {websocket: role} for role-aware broadcasting
        self.connection_roles: Dict[int, Dict[WebSocket, str]] = {}

    async def connect(self, websocket: WebSocket, class_id: int, role: str | None = None):
        await websocket.accept()
        if class_id not in self.active_connections:
            self.active_connections[class_id] = set()
            self.connection_roles[class_id] = {}
        self.active_connections[class_id].add(websocket)
        self.connection_roles[class_id][websocket] = role or "unknown"

    def disconnect(self, websocket: WebSocket, class_id: int):
        if class_id in self.active_connections:
            self.active_connections[class_id].discard(websocket)
            if class_id in self.connection_roles:
                self.connection_roles[class_id].pop(websocket, None)
            if not self.active_connections[class_id]:
                del self.active_connections[class_id]
                if class_id in self.connection_roles:
                    del self.connection_roles[class_id]

    async def broadcast_to_class(self, class_id: int, data: dict):
        """Send a JSON message to ALL connections in a class room (teachers + devices)."""
        if class_id not in self.active_connections:
            return

        message = json.dumps(data)
        dead = set()
        for ws in self.active_connections[class_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)

        # Clean up dead connections
        for ws in dead:
            self.active_connections[class_id].discard(ws)
            if class_id in self.connection_roles:
                self.connection_roles[class_id].pop(ws, None)

    async def broadcast_to_role(self, class_id: int, data: dict, role: str = "teacher"):
        """Send a JSON message only to connections matching the given role."""
        if class_id not in self.active_connections or class_id not in self.connection_roles:
            return

        message = json.dumps(data)
        dead = set()
        for ws in self.active_connections[class_id]:
            ws_role = self.connection_roles[class_id].get(ws, "unknown")
            if ws_role == role:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.add(ws)

        # Clean up dead connections
        for ws in dead:
            self.active_connections[class_id].discard(ws)
            self.connection_roles[class_id].pop(ws, None)

    async def send_to_class(self, class_id: int, data: dict):
        """Alias for broadcast_to_class."""
        await self.broadcast_to_class(class_id, data)

    def get_connection_count(self, class_id: int) -> int:
        return len(self.active_connections.get(class_id, set()))


# Singleton instance
manager = ConnectionManager()
