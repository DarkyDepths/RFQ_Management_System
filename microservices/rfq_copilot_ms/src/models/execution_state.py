"""ExecutionState — runtime mutable state for one turn (§2.5, §14.4).

See ``docs/11-Architecture_Frozen_v2.md`` §2.5 (semantics) and §14.4
(authoritative runtime types).

The Pydantic type that flows through the canonical pipeline. **Stages
mutate it.** It captures what *happened* during this turn, not what
was *planned* (which lives in ``state.plan: TurnExecutionPlan``).

The ``execution_record`` (§4) is a serialization of this object plus
timing/tokens metadata.

Per-source field population (see §4.2 matrix):

============================  ============  =============
Field                         FastIntake    Planner
============================  ============  =============
``intake_path``               fast_intake   planner
``intake_decision``           populated     null
``planner_proposal``          null          populated
``validated_planner_proposal`` null         populated
``planner_latency_ms``        null          populated
``planner_tokens``            null          populated
``turn_execution_plan``       populated     populated
============================  ============  =============

Other fields populated by their respective stages: ``resolved_targets``
(Resolver), ``access_decisions`` (Access), ``working_memory`` /
``episodic_summaries`` (Memory Load), ``tool_invocations`` /
``evidence_packets`` (Tool Executor), ``draft_text`` (Compose),
``guardrail_strips`` (Guardrails), ``judge_verdict`` (Judge),
``final_text`` / ``final_path`` (Finalizer), ``escalations``
(Escalation Gate).

Batch 0 status: STUB ONLY. Pydantic body lands in Slice 1.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future shape (illustrative — do not import yet):
#
#   from typing import Literal, Optional
#   from pydantic import BaseModel, Field
#   from src.models.actor import Actor
#   from src.models.execution_plan import TurnExecutionPlan
#   from src.models.intake_decision import IntakeDecision
#   from src.models.planner_proposal import (
#       PlannerProposal, ValidatedPlannerProposal,
#   )
#
#   class ExecutionState(BaseModel):
#       turn_id: str
#       actor: Actor
#       plan: TurnExecutionPlan
#       user_message: str
#
#       # Intake forensics — set by FastIntake/Planner
#       intake_path: Literal["fast_intake", "planner"]
#       intake_decision: Optional[IntakeDecision] = None
#       planner_proposal: Optional[PlannerProposal] = None
#       validated_planner_proposal: Optional[ValidatedPlannerProposal] = None
#
#       # Filled by downstream stages
#       resolved_targets: list = Field(default_factory=list)
#       access_decisions: list = Field(default_factory=list)
#       working_memory: list = Field(default_factory=list)
#       episodic_summaries: list = Field(default_factory=list)
#       evidence_packets: list = Field(default_factory=list)
#       tool_invocations: list = Field(default_factory=list)
#       draft_text: Optional[str] = None
#       guardrail_strips: list = Field(default_factory=list)
#       judge_verdict: Optional[dict] = None
#       final_text: Optional[str] = None
#       final_path: Optional[str] = None
#       escalations: list = Field(default_factory=list)
