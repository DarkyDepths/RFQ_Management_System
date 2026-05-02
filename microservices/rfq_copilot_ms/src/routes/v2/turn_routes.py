"""POST /rfq-copilot/v2/threads/{thread_id}/turn — FastIntake template slice.

Batch 4 slice — only the FastIntake -> ExecutionPlanFactory ->
template Finalizer path is wired. For trivial messages (greetings,
thanks, farewells, empty input, pure punctuation), /v2 returns 200
with a templated answer. For everything else (including out-of-scope
prose like "write me a recipe"), /v2 returns 501 — the GPT-4o
Planner pipeline is not implemented yet.

Pipeline stages active in Batch 4:

  FastIntake -> ExecutionPlanFactory -> [no Resolver / Access / Tool
  Executor / Compose / Guardrails / Judge — template-only] -> Finalizer

Stages NOT active (return None / NotImplementedError if reached):

  Planner, PlannerValidator (factory still calls these in tests, but
  the route never invokes them — FastIntake-miss returns 501 before
  the Planner would run).

See ``docs/11-Architecture_Frozen_v2.md`` (canonical) and
``docs/rfq_copilot_architecture_v4.html`` (visual) for the full pipeline.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.models.actor import Actor
from src.models.execution_plan import FactoryRejection
from src.pipeline import execution_state as exec_state_helpers
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.fast_intake import try_match
from src.pipeline.finalizer import finalize
from src.utils.auth_context import resolve_actor


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/threads", tags=["v2 (FastIntake slice)"])


# Module-level singleton — the factory is stateless beyond the registry
# reference; safe to share. Slice 5+ will move this into proper DI when
# /v2 needs the full pipeline (Planner, manager connector, etc.).
_factory = ExecutionPlanFactory()


# ── Request / response wire types (v2-specific) ───────────────────────────


class V2TurnRequest(BaseModel):
    """v2 lane turn request body. Field name ``message`` (NOT
    ``user_message`` like /v1) because /v2 is a fresh contract."""

    message: str


# ── Stable 501 body for non-FastIntake messages ───────────────────────────


_PLANNER_NOT_IMPLEMENTED_MESSAGE = (
    "Your message did not match a deterministic FastIntake pattern. "
    "The full v4 Planner pipeline (LLM classification, manager-grounded "
    "retrieval, compose, judge) is not implemented yet — it lands in "
    "later batches. For now, /v2 supports greetings, 'thanks', "
    "farewells, empty input, and pure punctuation. "
    "See docs/11-Architecture_Frozen_v2.md."
)


def _planner_not_implemented_body(thread_id: str) -> dict:
    return {
        "error": "PlannerNotImplemented",
        "lane": "v2",
        "status": "planner_not_implemented",
        "thread_id": thread_id,
        "message": _PLANNER_NOT_IMPLEMENTED_MESSAGE,
    }


# ── Route ─────────────────────────────────────────────────────────────────


@router.post("/{thread_id}/turn", include_in_schema=True)
def post_turn_v2(
    thread_id: str,
    body: V2TurnRequest,
    actor: Actor = Depends(resolve_actor),
):
    """v2 turn endpoint — FastIntake template slice.

    Flow:

    1. FastIntake.try_match(message)
       - hit  -> ExecutionPlanFactory.build_from_intake -> Finalizer -> 200
       - miss -> 501 PlannerNotImplemented

    The route does NOT persist anything to the DB in Batch 4 — Persist
    is a later batch. The thread_id is echoed back in the response for
    client correlation.
    """
    decision = try_match(body.message)

    # FastIntake miss — Planner not implemented yet, return 501.
    if decision is None:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content=_planner_not_implemented_body(thread_id),
        )

    # FastIntake hit — build the plan via the factory.
    factory_result = _factory.build_from_intake(
        decision=decision,
        actor=actor,
        session=None,
    )

    # FactoryRejection from a FastIntake decision should not happen for
    # patterns declared in PATH_CONFIGS — but if it does, return a clear
    # diagnostic without exposing internals.
    if isinstance(factory_result, FactoryRejection):
        logger.error(
            "FastIntake -> factory rejection for pattern %s (%s/%s): "
            "trigger=%s rule=%s",
            decision.pattern_id,
            decision.path.value,
            decision.intent_topic,
            factory_result.trigger,
            factory_result.factory_rule,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "lane": "v2",
                "status": "factory_rejection",
                "thread_id": thread_id,
                "message": (
                    "I couldn't process that message safely. Please try "
                    "rephrasing."
                ),
            },
        )

    plan = factory_result

    # Initialize ExecutionState for FastIntake source.
    state = exec_state_helpers.init_state_from_intake(
        turn_id=str(uuid.uuid4()),
        actor=actor,
        user_message=body.message,
        plan=plan,
        decision=decision,
    )

    # Render the template into state.final_text + state.final_path.
    finalize(state)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "lane": "v2",
            "status": "answered",
            "thread_id": thread_id,
            "answer": state.final_text,
            "path": state.final_path.value if state.final_path else None,
            "intent_topic": plan.intent_topic,
            "reason_code": (
                str(plan.finalizer_reason_code)
                if plan.finalizer_reason_code is not None
                else None
            ),
        },
    )
