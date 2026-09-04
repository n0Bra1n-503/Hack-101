"""FastAPI WebSocket endpoint for /ws/live."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("skyguard.websocket_router")
router = APIRouter()


@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """Real-time live telemetry and event stream endpoint."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Respond to client heartbeats or control messages
            logger.debug(f"Received from ws client: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket)
