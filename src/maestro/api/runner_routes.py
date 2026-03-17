"""Orchestrator/Runner REST API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/state")
async def get_state(request: Request) -> dict:
    """Get orchestrator state snapshot."""
    orch = getattr(request.app.state, "orchestrator", None)
    if not orch:
        return {"running": False, "message": "Orchestrator not started"}
    return orch.get_state_snapshot()


@router.get("/issues/{identifier}")
async def get_issue(request: Request, identifier: str) -> dict:
    """Get single issue detail from the orchestrator."""
    orch = getattr(request.app.state, "orchestrator", None)
    if not orch:
        raise HTTPException(status_code=503, detail="Orchestrator not started")

    snapshot = orch.get_state_snapshot()
    for run in snapshot.get("running", []):
        if run.get("identifier") == identifier:
            return run
    raise HTTPException(status_code=404, detail=f"Issue {identifier} not found")


@router.post("/refresh")
async def trigger_refresh(request: Request) -> dict:
    """Trigger an immediate poll tick."""
    orch = getattr(request.app.state, "orchestrator", None)
    if not orch:
        raise HTTPException(status_code=503, detail="Orchestrator not started")

    # Signal the orchestrator to poll immediately
    if hasattr(orch, "_refresh_event"):
        orch._refresh_event.set()
    return {"status": "refresh_triggered"}


@router.post("/start")
async def start_orchestrator(request: Request) -> dict:
    """Start the orchestrator daemon."""
    # This would need to start the orchestrator in a background task
    return {"status": "not_implemented", "message": "Use 'maestro start' CLI to run with orchestrator"}


@router.post("/stop")
async def stop_orchestrator(request: Request) -> dict:
    """Stop the orchestrator daemon."""
    orch = getattr(request.app.state, "orchestrator", None)
    if not orch:
        raise HTTPException(status_code=503, detail="Orchestrator not started")

    orch.shutdown()
    return {"status": "stopping"}
