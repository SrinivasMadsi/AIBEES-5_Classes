"""
api/routes_chat.py
POST /api/chat — submit a procurement request, get the resulting PO.
"""
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from core.tracer import tracer
from graph import get_graph, initial_state

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Natural-language PO request")
    thread_id: str | None = Field(None, description="Optional — provide to resume a run")
    user_id: str = Field("anonymous", description="For Langfuse trace attribution")


class ChatResponse(BaseModel):
    thread_id: str
    final_status: str
    final_po: dict | None
    findings: list[dict]
    verdict: str
    critic_summary: str
    iteration_count: int


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Run the PO agent end-to-end. Returns the final PO and audit trail."""
    thread_id = req.thread_id or f"po-{uuid.uuid4().hex[:8]}"
    config = {
        "configurable": {"thread_id": thread_id},
        **tracer.build_config(
            run_name="po-agent",
            session_id=thread_id,
            user_id=req.user_id,
            tags=["po-agent", "api"],
        ),
    }

    state = initial_state(req.message, max_iterations=settings.max_self_correction_iterations)

    try:
        graph = get_graph(use_checkpointer=True)
        result = graph.invoke(state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent run failed: {e}") from e
    finally:
        tracer.flush()

    return ChatResponse(
        thread_id=thread_id,
        final_status=result.get("final_status", "unknown"),
        final_po=result.get("final_po"),
        findings=result.get("findings", []),
        verdict=result.get("verdict", ""),
        critic_summary=result.get("critic_summary", ""),
        iteration_count=result.get("iteration_count", 0),
    )


@router.post("/chat/resume", response_model=ChatResponse)
def resume(thread_id: str):
    """Resume a previously-failed run by thread_id. Reads last checkpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    graph = get_graph(use_checkpointer=True)

    snapshot = graph.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(404, f"No checkpoint found for thread_id={thread_id}")

    try:
        result = graph.invoke(None, config=config)   # None = continue from checkpoint
    except Exception as e:
        raise HTTPException(500, f"Resume failed: {e}") from e

    return ChatResponse(
        thread_id=thread_id,
        final_status=result.get("final_status", "unknown"),
        final_po=result.get("final_po"),
        findings=result.get("findings", []),
        verdict=result.get("verdict", ""),
        critic_summary=result.get("critic_summary", ""),
        iteration_count=result.get("iteration_count", 0),
    )
