"""POST /rfq-copilot/v2/threads/{thread_id}/turn — placeholder for v4 pipeline.

This route mirrors the /v1 turn endpoint shape but is intentionally
unimplemented in Batch 0. It exists so the /v2 lane is reachable, the
FastAPI app boots cleanly with both prefixes registered, and downstream
clients can discover that /v2 is "scaffolded but not implemented".

Returns HTTP 501 Not Implemented with a stable JSON body so clients can
distinguish "endpoint missing" (404) from "endpoint exists but the
pipeline isn't wired yet" (501).

The real /v2 implementation lands across Slice 1 batches:

  FastIntake -> Planner -> PlannerValidator -> ExecutionPlanFactory ->
  Resolver -> Access -> Memory Load -> Tool Executor -> Evidence Check
  -> Context Builder -> Compose -> Guardrails -> Judge -> Finalizer
  -> Persist

See ``docs/11-Architecture_Frozen_v2.md`` (canonical) and
``docs/rfq_copilot_architecture_v4.html`` (visual) for the full pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/threads", tags=["v2 (scaffolded)"])


_NOT_IMPLEMENTED_BODY = {
    "error": "NotImplemented",
    "message": (
        "The v4 RFQ Copilot pipeline is scaffolded but not implemented yet. "
        "Use /rfq-copilot/v1/* for the current MVP. "
        "See docs/11-Architecture_Frozen_v2.md."
    ),
    "lane": "v2",
    "status": "scaffolded",
}


@router.post("/{thread_id}/turn", include_in_schema=True)
def post_turn_v2_placeholder(thread_id: str):  # noqa: ARG001
    """Placeholder — always 501 in Batch 0."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=_NOT_IMPLEMENTED_BODY,
    )
