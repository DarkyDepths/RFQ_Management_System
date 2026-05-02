"""ExecutionState pipeline helpers.

See ``docs/11-Architecture_Frozen_v2.md`` §2.5.

The runtime mutable state object that flows through the canonical
pipeline. Stages mutate it as they run. The ``ExecutionState`` Pydantic
type itself lives in ``src/models/execution_state.py``; this module
holds the helper functions stages use to update it (factory, slice
mutators, snapshot-for-persist).

Key invariants:

* ``state.plan`` is **immutable after the factory emits it**. The
  Escalation Gate replaces ``state.plan`` with a new factory-built
  Path 8.x plan rather than mutating the existing one.
* Each stage writes only its own slice (``state.resolved_targets``,
  ``state.evidence_packets``, etc.) — never reaches into another
  stage's slice.
* ``state.intake_path`` is set as soon as either FastIntake hits or
  the Planner emits, and is persisted as a forensic column in
  ``execution_records`` (§4.2).

Status: SIGNATURE STUB. Type contracts wired in Batch 1; mutators land
in a later batch.
"""

from __future__ import annotations

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import ExecutionState


def init_state(
    turn_id: str,  # noqa: ARG001
    actor: Actor,  # noqa: ARG001
    user_message: str,  # noqa: ARG001
    plan: TurnExecutionPlan,  # noqa: ARG001
) -> ExecutionState:
    """Build the initial ExecutionState for a turn (after the factory
    has emitted the plan and the intake source has been recorded)."""
    raise NotImplementedError(
        "execution_state.init_state() scaffolded only. "
        "See docs/11-Architecture_Frozen_v2.md §2.5."
    )


def replace_plan_for_escalation(
    state: ExecutionState,  # noqa: ARG001
    p8_plan: TurnExecutionPlan,  # noqa: ARG001
) -> None:
    """Escalation Gate helper: swap ``state.plan`` for the Path 8.x
    plan freshly built by the factory's ``build_from_escalation``."""
    raise NotImplementedError(
        "execution_state.replace_plan_for_escalation() scaffolded only. "
        "See docs/11-Architecture_Frozen_v2.md §5.2."
    )
