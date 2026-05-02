"""ExecutionState pipeline helpers.

See ``docs/11-Architecture_Frozen_v2.md`` §2.5.

The runtime mutable state object that flows through the canonical
pipeline. Stages mutate it as they run. The ``ExecutionState`` Pydantic
type itself lives in ``src/models/execution_state.py``; this module
holds the helper functions stages use to construct + update it.

Key invariants (§2.5):

* ``state.plan`` is **immutable after the factory emits it**. The
  Escalation Gate replaces ``state.plan`` with a new factory-built
  Path 8.x plan rather than mutating the existing one.
* Each stage writes only its own slice (``state.resolved_targets``,
  ``state.evidence_packets``, etc.) — never reaches into another
  stage's slice.
* ``state.intake_path`` is set as soon as either FastIntake hits or
  the Planner emits, and is persisted as a forensic column in
  ``execution_records`` (§4.2).

Status: Batch 4 implements only ``init_state_from_intake`` (the
constructor for the FastIntake → factory → finalizer slice). The
Planner-source constructor and the Gate-source plan replacement land
in later batches when those flows ship.
"""

from __future__ import annotations

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import ExecutionState
from src.models.intake_decision import IntakeDecision


def init_state_from_intake(
    *,
    turn_id: str,
    actor: Actor,
    user_message: str,
    plan: TurnExecutionPlan,
    decision: IntakeDecision,
) -> ExecutionState:
    """Construct an ``ExecutionState`` for a FastIntake-source turn.

    Sets ``intake_path="fast_intake"`` and attaches the original
    ``IntakeDecision`` for forensics (lands in ``execution_records``
    when Persist ships in a later batch).

    All runtime-outcome fields default to empty per the
    ``ExecutionState`` model (Resolver / Tool Executor / Compose / Judge
    don't run for template-only paths).
    """
    return ExecutionState(
        turn_id=turn_id,
        actor=actor,
        plan=plan,
        user_message=user_message,
        intake_path="fast_intake",
        intake_decision=decision,
    )
