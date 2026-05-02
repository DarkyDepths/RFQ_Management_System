"""POST /rfq-copilot/v2/threads/{thread_id}/turn — full v4 pipeline (Slice 1).

Batch 5 wires the Path 4 manager-grounded operational core. The route
is now thin: parse + delegate to ``V2TurnController`` + serialize. All
pipeline logic lives in the controller / stages.

Active stages in Batch 5:

  FastIntake -> ExecutionPlanFactory                    -> Finalizer (template)
  Planner -> PlannerValidator -> ExecutionPlanFactory
          -> Resolver -> Access -> ToolExecutor -> EvidenceCheck
          -> ContextBuilder -> Path4Renderer (grounded) -> Finalizer (pass-through)

Failures route via ``EscalationGate`` to Path 8.x — the response is
still 200 with the safe template. True 5xx only on the truly
unrecovered case (gate failed AND finalizer crashed).

Stages NOT active (return None / NotImplementedError if reached):

  Compose (LLM), Guardrails, Judge, Persist — Slice 5+ batches.

See ``docs/11-Architecture_Frozen_v2.md`` (canonical) and
``docs/rfq_copilot_architecture_v4.html`` (visual) for the full pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app_context import get_v2_turn_controller
from src.controllers.v2_turn_controller import V2TurnController
from src.models.actor import Actor
from src.models.v2_turn import V2TurnRequest, V2TurnResponse
from src.utils.auth_context import resolve_actor


router = APIRouter(prefix="/threads", tags=["v2"])


@router.post("/{thread_id}/turn", response_model=V2TurnResponse)
def post_turn_v2(
    thread_id: str,
    body: V2TurnRequest,
    actor: Actor = Depends(resolve_actor),
    controller: V2TurnController = Depends(get_v2_turn_controller),
) -> V2TurnResponse:
    """Run the v4 pipeline for one /v2 turn.

    All pipeline logic lives in :class:`V2TurnController`. The route is
    intentionally thin — parse, delegate, serialize.
    """
    return controller.handle_turn(
        thread_id=thread_id,
        request=body,
        actor=actor,
    )
