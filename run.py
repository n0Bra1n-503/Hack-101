#!/usr/bin/env python3
"""SkyGuard AI - Production Service Launcher.

Unified single-port runner serving:
  - React SPA Frontend (built in frontend/dist)
  - Static Assets (/assets)
  - REST API Endpoints (/api/*)
  - Live Telemetry WebSocket (/ws/live)
  - Interactive API Docs (/docs, /redoc)
"""

import os
import sys
from pathlib import Path

# Ensure root workspace directory is in python search path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from backend.app.core.config import settings


def main():
    host = os.environ.get("HOST", settings.HOST)
    port = int(os.environ.get("PORT", str(settings.PORT)))
    log_level = os.environ.get("LOG_LEVEL", settings.LOG_LEVEL).lower()

    frontend_dist = ROOT_DIR / "frontend" / "dist"
    frontend_status = "Built (Active)" if (frontend_dist / "index.html").exists() else "Missing (Run 'npm run build' in frontend/)"

    print("=" * 65)
    print("  SKYGUARD AI - UNIFIED PRODUCTION SERVICE")
    print(f"  Environment    : {settings.ENVIRONMENT}")
    print(f"  Host / Port    : {host}:{port}")
    print(f"  Web Interface  : http://{host if host != '0.0.0.0' else 'localhost'}:{port}/")
    print(f"  REST API Docs  : http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print(f"  WebSocket Feed : ws://{host if host != '0.0.0.0' else 'localhost'}:{port}/ws/live")
    print(f"  Frontend Dist  : {frontend_status}")
    print("=" * 65)

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        log_level=log_level,
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
