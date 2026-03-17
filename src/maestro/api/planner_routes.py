"""Planner REST API endpoints for managing planning sessions."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session storage (replace with persistent storage later)
_sessions: dict[str, dict[str, Any]] = {}


class CreateSessionRequest(BaseModel):
    project_name: str = ""
    project_description: str = ""
    intake_mode: str = "smart"  # "smart" | "standard" | "quick"


class MessageRequest(BaseModel):
    content: str


class ReviewRequest(BaseModel):
    decision: str  # "accept" | "edit" | "reject"
    feedback: str = ""


class ExportRequest(BaseModel):
    format: str = "html"  # "linear" | "markdown" | "html"


@router.post("/sessions")
async def create_session(req: CreateSessionRequest) -> dict:
    """Create a new planning session."""
    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = {
        "id": session_id,
        "project_name": req.project_name,
        "project_description": req.project_description,
        "intake_mode": req.intake_mode,
        "state": None,  # Will hold the LangGraph state
        "graph": None,  # Will hold the compiled graph
    }
    logger.info("Created planning session %s", session_id)
    return {"session_id": session_id}


@router.get("/sessions")
async def list_sessions() -> list[dict]:
    """List all saved planning sessions."""
    return [
        {
            "id": s["id"],
            "project_name": s.get("project_name", ""),
            "has_state": s.get("state") is not None,
        }
        for s in _sessions.values()
    ]


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get full session state as JSON."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = session.get("state") or {}
    return {
        "id": session_id,
        "project_name": session.get("project_name", ""),
        "state": _serialize_state(state),
    }


@router.post("/sessions/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest) -> dict:
    """Send user input to the planning graph and return the result."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Import here to avoid circular imports and allow lazy loading
    from langchain_core.messages import HumanMessage
    from langgraph.checkpoint.memory import MemorySaver

    from maestro.api.ws import manager
    from maestro.planner.graph import create_graph

    # Initialize graph on first message
    if session["graph"] is None:
        checkpointer = MemorySaver()
        session["graph"] = create_graph(checkpointer=checkpointer)
        session["state"] = {}

    graph = session["graph"]
    config = {"configurable": {"thread_id": session_id}}

    # Build input
    input_state: dict[str, Any] = {"messages": [HumanMessage(content=req.content)]}
    if session["state"] is None:
        input_state["_intake_mode"] = session.get("intake_mode", "smart")

    # Invoke graph
    try:
        result = await _invoke_graph(graph, input_state, config, session_id)
        session["state"] = result

        # Broadcast update via WebSocket
        await manager.broadcast(
            f"planner:{session_id}",
            "state_update",
            _serialize_state(result),
        )

        return {"state": _serialize_state(result)}
    except Exception as e:
        logger.error("Graph invocation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/review")
async def submit_review(session_id: str, req: ReviewRequest) -> dict:
    """Submit an accept/edit/reject decision for the current review gate."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Send the review decision as a message to the graph
    review_text = req.decision
    if req.feedback:
        review_text = f"{req.decision}: {req.feedback}"

    message_req = MessageRequest(content=review_text)
    return await send_message(session_id, message_req)


@router.post("/sessions/{session_id}/export")
async def export_session(session_id: str, req: ExportRequest) -> dict:
    """Export the session's plan artifacts."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = session.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Session has no state to export")

    if req.format == "html":
        from maestro.planner.exporters.html import build_export_html

        html_content = build_export_html(state)
        return {"format": "html", "content": html_content}
    elif req.format == "markdown":
        return {"format": "markdown", "content": "Markdown export not yet implemented"}
    elif req.format == "linear":
        return {"format": "linear", "content": "Linear export not yet implemented"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {req.format}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a planning session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del _sessions[session_id]
    return {"deleted": session_id}


async def _invoke_graph(graph, input_state: dict, config: dict, session_id: str) -> dict:
    """Invoke the LangGraph graph, potentially in a background thread."""
    import asyncio

    # LangGraph's invoke is synchronous, run in a thread
    result = await asyncio.to_thread(graph.invoke, input_state, config)
    return result


def _serialize_state(state: dict) -> dict:
    """Convert graph state to JSON-serializable dict."""
    import dataclasses
    import enum

    def _convert(obj: Any) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, enum.Enum):
            return obj.value
        if isinstance(obj, (set, frozenset)):
            return [_convert(item) for item in obj]
        if isinstance(obj, tuple):
            return [_convert(item) for item in obj]
        if isinstance(obj, dict):
            return {str(k): _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(item) for item in obj]
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return _convert(dataclasses.asdict(obj))
        if hasattr(obj, "content"):  # LangChain message objects
            return {"type": type(obj).__name__, "content": obj.content}
        return str(obj)

    result = {}
    for key, value in state.items():
        if key == "messages":
            result["messages"] = [
                {"type": type(m).__name__, "content": getattr(m, "content", str(m))} for m in (value or [])
            ]
        else:
            result[key] = _convert(value)
    return result
