"""Contract tests — TurnExecutionPlan + EscalationRequest +
FactoryRejection (§2.2, §2.7, §14.3).

These tests enforce the load-bearing separation:

* ``TurnExecutionPlan`` = STRATEGY AND POLICY ONLY.
* Runtime outcomes (resolved_targets, draft_text, judge_verdict, etc.)
  live in ``ExecutionState`` and must be REJECTED here by
  ``extra="forbid"``.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.execution_plan import (
    EscalationRequest,
    FactoryRejection,
    TurnExecutionPlan,
)
from src.models.path_registry import (
    AccessPolicyName,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
)
from src.models.planner_proposal import PlannerProposal, ValidatedPlannerProposal


# ── Helpers ────────────────────────────────────────────────────────────────


def _minimal_plan_kwargs():
    """Smallest valid TurnExecutionPlan: a Path 1 / Path 8.x style
    template-only plan (model_profile=None, no tools, no fetch).
    """
    return dict(
        path=PathId.PATH_1,
        intent_topic="greeting",
        source=IntakeSource.FAST_INTAKE,
        resolver_strategy=ResolverStrategy.NONE,
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_1.greeting",
    )


# ── TurnExecutionPlan minimal valid ────────────────────────────────────────


def test_minimal_turn_execution_plan_constructs():
    plan = TurnExecutionPlan(**_minimal_plan_kwargs())
    assert plan.path is PathId.PATH_1
    assert plan.source is IntakeSource.FAST_INTAKE
    # Defaults for omitted optional fields:
    assert plan.target_candidates == []
    assert plan.allowed_evidence_tools == []
    assert plan.judge_policy is None
    assert plan.model_profile is None
    assert plan.finalizer_reason_code is None


def test_turn_execution_plan_source_must_be_valid_enum():
    bad = _minimal_plan_kwargs() | {"source": "rogue_source"}
    with pytest.raises(ValidationError):
        TurnExecutionPlan(**bad)


# ── Forbidden runtime outcome fields (load-bearing assertions) ────────────

# Each entry is a runtime outcome field that MUST belong to ExecutionState,
# never the plan. extra="forbid" rejects every one.

_FORBIDDEN_RUNTIME_FIELDS = [
    ("resolved_targets", []),
    ("access_decisions", []),
    ("tool_invocations", []),
    ("tool_results", []),  # legacy name shape; same boundary
    ("evidence_packets", []),
    ("draft_text", "anything"),
    ("final_text", "anything"),
    ("final_path", PathId.PATH_8_5.value),
    ("judge_verdict", {"verdict": "pass"}),
    ("guardrail_strips", []),
    ("escalations", []),
    ("working_memory", []),
]


@pytest.mark.parametrize("field_name,value", _FORBIDDEN_RUNTIME_FIELDS)
def test_turn_execution_plan_rejects_runtime_outcome_field(field_name: str, value):
    """Runtime outcomes belong in ExecutionState. Any of these fields
    appearing on a TurnExecutionPlan is a category error and the type
    system rejects it."""
    bad = _minimal_plan_kwargs() | {field_name: value}
    with pytest.raises(ValidationError, match="extra"):
        TurnExecutionPlan(**bad)


def test_turn_execution_plan_rejects_unknown_fields():
    bad = _minimal_plan_kwargs() | {"some_new_unspec_field": True}
    with pytest.raises(ValidationError, match="extra"):
        TurnExecutionPlan(**bad)


# ── frozen attribute reassignment ─────────────────────────────────────────


def test_turn_execution_plan_attribute_reassignment_rejected():
    """frozen=True blocks attribute reassignment. Combined with CI guard
    §11.5.1 (single-construction at the factory), this means downstream
    stages cannot accidentally rewrite plan fields after the fact."""
    plan = TurnExecutionPlan(**_minimal_plan_kwargs())
    with pytest.raises(ValidationError):
        plan.path = PathId.PATH_4  # type: ignore[misc]
    with pytest.raises(ValidationError):
        plan.finalizer_template_key = "different.template"  # type: ignore[misc]


# ── EscalationRequest ──────────────────────────────────────────────────────


def test_escalation_request_minimal_construction():
    req = EscalationRequest(
        target_path=PathId.PATH_8_5,
        reason_code=ReasonCode("source_unavailable"),
        source_stage="tool_executor",
        trigger="manager_unreachable",
    )
    assert req.target_path is PathId.PATH_8_5


def test_escalation_request_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="extra"):
        EscalationRequest(  # type: ignore[call-arg]
            target_path=PathId.PATH_8_5,
            reason_code=ReasonCode("x"),
            source_stage="x",
            trigger="x",
            extra="leak",
        )


# ── FactoryRejection ───────────────────────────────────────────────────────


def test_factory_rejection_minimal_construction():
    inner = PlannerProposal(
        path=PathId.PATH_4,
        intent_topic="margin",
        confidence=0.9,
        classification_rationale="x",
    )
    validated = ValidatedPlannerProposal(
        proposal=inner,
        validated_at=datetime(2026, 5, 2, 12, 0, 0),
    )
    rej = FactoryRejection(
        trigger="forbidden_field_requested",
        reason_code=ReasonCode("forbidden_field_requested"),
        rejected_input=validated,
        factory_rule="F5",
        rejected_at=datetime(2026, 5, 2, 12, 0, 0),
    )
    assert rej.factory_rule == "F5"


def test_factory_rejection_rule_must_be_one_of_the_eight():
    """``factory_rule`` is a closed Literal — cannot be a free-form
    string. If a future batch adds rule F9, this test catches the miss."""
    inner = PlannerProposal(
        path=PathId.PATH_4,
        intent_topic="x",
        confidence=0.9,
        classification_rationale="x",
    )
    validated = ValidatedPlannerProposal(
        proposal=inner,
        validated_at=datetime(2026, 5, 2, 12, 0, 0),
    )
    with pytest.raises(ValidationError):
        FactoryRejection(
            trigger="x",
            reason_code=ReasonCode("x"),
            rejected_input=validated,
            factory_rule="F99",  # type: ignore[arg-type]
            rejected_at=datetime(2026, 5, 2, 12, 0, 0),
        )
