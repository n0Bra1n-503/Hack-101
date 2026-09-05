"""API endpoints for Historical Telemetry Replay."""

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.replay_service import replay_engine

router = APIRouter(prefix="/replay", tags=["replay"])


class ReplayStartRequest(BaseModel):
    station_id: Optional[str] = None
    speed: float = 1.0


class ReplaySpeedRequest(BaseModel):
    speed: float


@router.post("/start")
async def start_replay(req: ReplayStartRequest) -> Dict[str, Any]:
    return await replay_engine.start(station_id=req.station_id, speed=req.speed)


@router.post("/pause")
def pause_replay() -> Dict[str, Any]:
    return replay_engine.pause()


@router.post("/resume")
def resume_replay() -> Dict[str, Any]:
    return replay_engine.resume()


@router.post("/reset")
def reset_replay() -> Dict[str, Any]:
    return replay_engine.reset()


@router.post("/stop")
def stop_replay() -> Dict[str, Any]:
    return replay_engine.reset()


@router.post("/speed")
def adjust_speed(req: ReplaySpeedRequest) -> Dict[str, Any]:
    return replay_engine.set_speed(req.speed)


@router.get("/status")
def get_replay_status() -> Dict[str, Any]:
    return replay_engine.get_status()
