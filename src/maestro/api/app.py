"""FastAPI application factory for Maestro."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Build and configure the Maestro FastAPI application."""
    app = FastAPI(
        title="Maestro",
        description="Unified Scrum Planner + Agent Orchestrator",
        version="0.1.0",
    )

    # CORS — allow local dev servers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    from maestro.api.planner_routes import router as planner_router
    from maestro.api.runner_routes import router as runner_router

    app.include_router(planner_router, prefix="/api/planner", tags=["planner"])
    app.include_router(runner_router, prefix="/api/runner", tags=["runner"])

    # Register WebSocket endpoints
    from maestro.api.ws import register_ws_routes

    register_ws_routes(app)

    # Serve frontend static files if built
    frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
        logger.info("Serving frontend from %s", frontend_dist)

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    return app
