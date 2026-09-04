"""FastAPI application initialization, middleware, and lifecycle configuration for SkyGuard AI."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.readings import router as readings_router
from backend.app.api.stations import router as stations_router
from backend.app.api.anomalies import router as anomalies_router
from backend.app.api.maintenance import router as maintenance_router
from backend.app.api.risks import router as risks_router
from backend.app.api.cascade import router as cascade_router
from backend.app.api.replay import router as replay_router
from backend.app.websocket.router import router as ws_router
from backend.app.core.config import settings
from backend.app.database.connection import init_db

# Configure application logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("skyguard.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context managing startup and shutdown tasks."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' environment...")
    init_db()
    # Pre-warm ML models singleton at application startup
    try:
        from backend.app.services.ml_service import get_ml_service
        get_ml_service()
        logger.info("ML inference pipeline loaded and ready.")
    except Exception as e:
        logger.warning(f"ML models warm-up note: {e}")
    logger.info("Database initialized. SkyGuard backend is ready to accept requests.")
    yield
    logger.info("Shutting down SkyGuard backend...")


app = FastAPI(
    title="SkyGuard AI Backend",
    version="1.0.0",
    description=(
        "Production backend for SkyGuard AI: real weather telemetry ingestion, "
        "ML anomaly detection, decision intelligence, trust scoring, digital twin, "
        "predictive maintenance, and validated disaster risk assessment."
    ),
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(readings_router)
app.include_router(stations_router, prefix="/api")
app.include_router(anomalies_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(risks_router, prefix="/api")
app.include_router(cascade_router, prefix="/api")
app.include_router(replay_router, prefix="/api")
app.include_router(ws_router)


from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Detect built frontend assets
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
assets_dir = frontend_dist / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get(
    "/",
    tags=["Root"],
    summary="Root service information",
    description="Returns backend running status and version.",
)
def root_endpoint(request: Request):
    """Return frontend web application for browsers, or service JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and (frontend_dist / "index.html").exists():
        return FileResponse(frontend_dist / "index.html")
    return {
        "message": "SkyGuard AI backend is running",
        "version": settings.APP_VERSION,
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns operational readiness status of the backend application.",
)
def health_endpoint() -> dict:
    """Return service health status."""
    return {
        "status": "ok",
        "service": "skyguard-backend",
    }


from backend.app.api.stations import get_network_summary
from backend.app.database.session import get_db
from fastapi import Depends


@app.get(
    "/summary",
    tags=["Root"],
    summary="Direct network summary alias",
    description="Returns network summary metrics directly for clients requesting /summary without /api prefix.",
)
def root_summary_alias(db=Depends(get_db)):
    """Return network summary directly so /summary never falls through to SPA HTML."""
    return get_network_summary(db=db)


# SPA client-side routing fallback for web pages
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str, request: Request):
    if any(full_path.startswith(p) for p in ("api", "ws", "docs", "redoc", "openapi", "summary")):
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": f"Endpoint '/{full_path}' not found"},
        )

    file_candidate = frontend_dist / full_path
    if full_path and file_candidate.is_file():
        return FileResponse(file_candidate)

    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": f"Resource '/{full_path}' not found"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback exception handler for unhandled internal errors."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected server error occurred. Please contact system operators.",
        },
    )
