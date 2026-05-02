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

Status: SIGNATURE STUB with registry import wired. Batch 2 makes the
runtime config (``PATH_CONFIGS``) reachable from this module per the
allowlist (§11.5.2 — only this file and ``escalation_gate.py`` may
import ``src.config.path_registry``). Rules F1..F8 + plan construction
land in a later batch.
"""

from __future__ import annotations

# Registry CONFIG import is restricted to this module + escalation_gate.py
# by CI guard §11.5.2. Importing here makes Slice 1 policy data reachable
# for the future build_from_* implementations; it does NOT execute any
# policy lookups in Batch 2 (bodies still raise NotImplementedError).
from src.config.path_registry import PATH_CONFIGS, REGISTRY_VERSION  # noqa: F401
from src.models.actor import Actor
from src.models.execution_plan import (
    EscalationRequest,
    FactoryRejection,
    TurnExecutionPlan,
)
from src.models.intake_decision import IntakeDecision
from src.models.planner_proposal import ValidatedPlannerProposal


class ExecutionPlanFactory:
    """The single ``TurnExecutionPlan`` constructor.

    CI guard §11.5.1 verifies that ``TurnExecutionPlan(...)`` is
    instantiated **only** in this module. CI guard §11.5.2 verifies
    that ``src.config.path_registry`` is imported **only** here and in
    ``escalation_gate.py``.
    """

    def build_from_intake(
        self,
        decision: IntakeDecision,  # noqa: ARG002
        actor: Actor,  # noqa: ARG002
        session: object,  # noqa: ARG002 — SessionState type lands in a later batch
    ) -> TurnExecutionPlan:
        raise NotImplementedError(
            "ExecutionPlanFactory.build_from_intake() scaffolded only. "
            "See docs/11-Architecture_Frozen_v2.md §2.7."
        )

    def build_from_planner(
        self,
        validated: ValidatedPlannerProposal,  # noqa: ARG002
        actor: Actor,  # noqa: ARG002
        session: object,  # noqa: ARG002
    ) -> TurnExecutionPlan | FactoryRejection:
        raise NotImplementedError(
            "ExecutionPlanFactory.build_from_planner() scaffolded only. "
            "See docs/11-Architecture_Frozen_v2.md §2.7."
        )

    def build_from_escalation(
        self,
        request: EscalationRequest,  # noqa: ARG002
        actor: Actor,  # noqa: ARG002
        session: object,  # noqa: ARG002
    ) -> TurnExecutionPlan:
        raise NotImplementedError(
            "ExecutionPlanFactory.build_from_escalation() scaffolded only. "
            "See docs/11-Architecture_Frozen_v2.md §2.7 / §5.2."
        )
