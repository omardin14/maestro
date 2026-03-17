"""WebSocket connection manager for real-time event streaming."""

import json
import logging
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with room-based subscriptions.

    Rooms are string keys like "planner:{session_id}" or "dashboard".
    Clients can join multiple rooms and receive broadcasts for each.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, room: str) -> None:
        """Accept a WebSocket and subscribe it to a room."""
        await websocket.accept()
        self._connections.add(websocket)
        self._rooms[room].add(websocket)
        logger.debug("WebSocket connected to room %s (total: %d)", room, len(self._connections))

    def disconnect(self, websocket: WebSocket, room: str) -> None:
        """Remove a WebSocket from a room and the global set."""
        self._rooms[room].discard(websocket)
        self._connections.discard(websocket)
        if not self._rooms[room]:
            del self._rooms[room]
        logger.debug("WebSocket disconnected from room %s (total: %d)", room, len(self._connections))

    async def broadcast(self, room: str, event_type: str, data: dict) -> None:
        """Send a JSON event to all connections in a room."""
        message = json.dumps({"type": event_type, "data": data})
        dead: list[WebSocket] = []
        for ws in self._rooms.get(room, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: dict) -> None:
        """Send a JSON event to a single WebSocket."""
        message = json.dumps({"type": event_type, "data": data})
        await websocket.send_text(message)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singleton manager
manager = ConnectionManager()


def register_ws_routes(app: FastAPI) -> None:
    """Register WebSocket endpoint handlers on the FastAPI app."""

    @app.websocket("/ws/planner/{session_id}")
    async def planner_ws(websocket: WebSocket, session_id: str) -> None:
        """WebSocket for streaming planner graph execution events."""
        room = f"planner:{session_id}"
        await manager.connect(websocket, room)
        try:
            while True:
                # Keep connection alive; client sends messages via REST
                data = await websocket.receive_text()
                # Client can send ping/keepalive
                if data == "ping":
                    await manager.send_personal(websocket, "pong", {})
        except WebSocketDisconnect:
            manager.disconnect(websocket, room)

    @app.websocket("/ws/runner")
    async def runner_ws(websocket: WebSocket) -> None:
        """WebSocket for streaming orchestrator state changes."""
        room = "dashboard"
        await manager.connect(websocket, room)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await manager.send_personal(websocket, "pong", {})
        except WebSocketDisconnect:
            manager.disconnect(websocket, room)
