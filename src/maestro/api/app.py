"""FastAPI application factory for Maestro."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    # Serve frontend static files if built
    frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        index_html = frontend_dist / "index.html"
        logger.info("Serving frontend from %s", frontend_dist)

        # Serve static assets (js, css, images)
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

        # SPA fallback middleware — serve index.html for non-API, non-WS, non-file routes
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import Response

        class SPAFallbackMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                response = await call_next(request)
                path = request.url.path
                if (
                    response.status_code == 404
                    and not path.startswith("/api/")
                    and not path.startswith("/ws/")
                    and not path.startswith("/assets/")
                ):
                    # Check if it's a static file in dist/
                    file_path = frontend_dist / path.lstrip("/")
                    if file_path.is_file():
                        return FileResponse(str(file_path))
                    return FileResponse(str(index_html))
                return response

        app.add_middleware(SPAFallbackMiddleware)

    return app
