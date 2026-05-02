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

Batch 0 status: STUB ONLY. No mutators implemented yet.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future signature (illustrative — do not import yet):
#
#   from src.models.actor import Actor
#   from src.models.execution_state import ExecutionState
#   from src.models.execution_plan import TurnExecutionPlan
#
#   def init_state(turn_id: str, actor: Actor, user_message: str) -> ExecutionState: ...
#   def attach_plan(state: ExecutionState, plan: TurnExecutionPlan) -> None: ...
#   def replace_plan_for_escalation(state: ExecutionState, p8_plan: TurnExecutionPlan) -> None: ...


def init_state(turn_id: str, actor, user_message: str):  # noqa: ARG001
    raise NotImplementedError(
        "execution_state.init_state() scaffolded only. "
        "See docs/11-Architecture_Frozen_v2.md §2.5."
    )
