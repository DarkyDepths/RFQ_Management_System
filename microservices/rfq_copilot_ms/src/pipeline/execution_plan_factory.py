"""ExecutionPlanFactory — Stage 2.5 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §2.7 and §3.2.

**The single chokepoint for ``TurnExecutionPlan`` construction.** No code
anywhere else in the repository may instantiate ``TurnExecutionPlan(...)``.
This invariant is mechanically enforced by CI guard §11.5.1 (AST grep).

The factory accepts three input shapes and produces one output:

* ``build_from_intake(decision, actor, session) -> TurnExecutionPlan``
  — FastIntake source.
* ``build_from_planner(validated, actor, session) -> TurnExecutionPlan | FactoryRejection``
  — Planner+Validator source. May reject via rules F1..F8 below.
* ``build_from_escalation(request, actor, session) -> TurnExecutionPlan``
  — Escalation Gate re-entry (constructs Path 8.x plans).

Source-aware policy enforcement (§2.7):

============= =========================================================== ==========
Rule          Check                                                       On failure
============= =========================================================== ==========
F1            (path, intent_topic) exists in registry                     8.1
F2            IntakeSource in IntentConfig.allowed_intake_sources         8.1
F3            Field-alias normalization -> canonical_requested_fields     8.1
F4            canonical_requested_fields ⊆ allowed_fields ∪ forbidden     8.1
F5            canonical_requested_fields ∩ forbidden_fields == ∅          8.1
F6            confidence ≥ IntentConfig.confidence_threshold              8.3
F7            Path 7 only — ∩ comparable_field_groups.C == ∅              8.1
F8            Path 3 only — required_query_slots present in proposal      8.3
============= =========================================================== ==========

The factory and the Escalation Gate are the ONLY two modules permitted
to import from ``src.config.path_registry`` (CI guard §11.5.2).

For FastIntake-source plans, the factory emits a plan with
``allowed_evidence_tools=[]``, ``access_policy=NONE``, ``judge_policy=None``,
``model_profile=None``, etc. — every downstream stage skips per the
§5.1 stage-skip convention, delivering the sub-100ms FastIntake path.

Batch 0 status: STUB ONLY. No rules / no policy resolution yet.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future signature (illustrative — do not import yet):
#
#   from src.models.execution_plan import (
#       TurnExecutionPlan, EscalationRequest, FactoryRejection,
#   )
#   from src.models.intake_decision import IntakeDecision
#   from src.models.planner_proposal import ValidatedPlannerProposal
#
#   class ExecutionPlanFactory:
#       def build_from_intake(self, decision, actor, session) -> TurnExecutionPlan: ...
#       def build_from_planner(self, validated, actor, session) -> TurnExecutionPlan | FactoryRejection: ...
#       def build_from_escalation(self, request, actor, session) -> TurnExecutionPlan: ...


class ExecutionPlanFactory:
    """Stub class. The single TurnExecutionPlan constructor.

    CI guard §11.5.1 (anti-drift test) verifies that
    ``TurnExecutionPlan(...)`` is instantiated **only** in this module.
    """

    def build_from_intake(self, decision, actor, session):  # noqa: ARG002
        raise NotImplementedError(
            "ExecutionPlanFactory.build_from_intake() scaffolded only. "
            "See docs/11-Architecture_Frozen_v2.md §2.7."
        )

    def build_from_planner(self, validated, actor, session):  # noqa: ARG002
        raise NotImplementedError(
            "ExecutionPlanFactory.build_from_planner() scaffolded only. "
            "See docs/11-Architecture_Frozen_v2.md §2.7."
        )

    def build_from_escalation(self, request, actor, session):  # noqa: ARG002
        raise NotImplementedError(
            "ExecutionPlanFactory.build_from_escalation() scaffolded only. "
            "See docs/11-Architecture_Frozen_v2.md §2.7 / §5.2."
        )
