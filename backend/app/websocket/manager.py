"""WebSocket Connection Manager for SkyGuard AI live stream."""

import json
import logging
from typing import Any, Dict, List
from fastapi import WebSocket

logger = logging.getLogger("skyguard.websocket")


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts real-time events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        """Broadcast an event matching the frontend contract: { type: str, payload: any }."""
        message = json.dumps({"type": event_type, "payload": payload})
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending message to websocket: {e}")
                self.disconnect(connection)


ws_manager = ConnectionManager()
