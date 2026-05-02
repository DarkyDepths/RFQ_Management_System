"""ExecutionPlanFactory behavior tests (Batch 3 — §2.7 rules F1..F8).

Verifies:
* All three ``build_from_*`` entry points produce valid TurnExecutionPlan
  objects from valid inputs.
* All eight policy rules (F1..F8) reject the wrong inputs.
* The plan is **self-contained** — copies all needed policy from the
  registry; downstream stages never need registry access.
* TurnExecutionPlan is constructed only inside execution_plan_factory.py
  (re-asserted via the §11.5.1 anti-drift guard).
* The registry-config import allowlist holds.

F7 (Path 7 Group C) and F8 (Path 3 query slots) are exercised with
**injected synthetic registries** because Slice 1 PATH_CONFIGS does not
include Path 3 / Path 7. The factory's ``__init__(registry=...)``
parameter is the dependency-injection seam.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.config.path_registry import PATH_CONFIGS
from src.models.execution_plan import (
    EscalationRequest,
    FactoryRejection,
    TurnExecutionPlan,
)
from src.models.intake_decision import IntakeDecision
from src.models.path_registry import (
    AccessPolicyName,
    ComparableFieldGroups,
    IntakePatternId,
    IntakeSource,
    IntentConfig,
    PathConfig,
    PathId,
    PersistencePolicy,
    PathRegistry,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
)
from src.models.planner_proposal import (
    PlannerProposal,
    ProposedTarget,
    ValidatedPlannerProposal,
)
from src.pipeline.execution_plan_factory import ExecutionPlanFactory


# ── Helpers ───────────────────────────────────────────────────────────────


def _validated_proposal(
    *,
    path: PathId = PathId.PATH_4,
    intent_topic: str = "deadline",
    confidence: float = 0.9,
    requested_fields: list[str] | None = None,
    target_candidates: list[ProposedTarget] | None = None,
    multi_intent_detected: bool = False,
    filters: dict | None = None,
    output_shape: str | None = None,
    sort: str | None = None,
    limit: int | None = None,
) -> ValidatedPlannerProposal:
    inner = PlannerProposal(
        path=path,
        intent_topic=intent_topic,
        confidence=confidence,
        classification_rationale="test fixture",
        target_candidates=target_candidates if target_candidates is not None else [
            ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code"),
        ],
        requested_fields=requested_fields if requested_fields is not None else [],
        multi_intent_detected=multi_intent_detected,
        filters=filters,
        output_shape=output_shape,
        sort=sort,
        limit=limit,
    )
    return ValidatedPlannerProposal(
        proposal=inner,
        validated_at=datetime.now(timezone.utc),
    )


def _intake(
    *,
    path: PathId,
    intent_topic: str,
    pattern_id: str = "test_pattern_v1",
    pattern_version: str = "1.0.0",
    raw_message: str = "hi",
) -> IntakeDecision:
    return IntakeDecision(
        pattern_id=IntakePatternId(pattern_id),
        pattern_version=pattern_version,
        path=path,
        intent_topic=intent_topic,
        matched_at=datetime.now(timezone.utc),
        raw_message=raw_message,
    )


@pytest.fixture
def factory() -> ExecutionPlanFactory:
    return ExecutionPlanFactory()


# ─────────────────────────────────────────────────────────────────────────
# build_from_intake
# ─────────────────────────────────────────────────────────────────────────


def test_build_from_intake_path_1_greeting(factory: ExecutionPlanFactory):
    decision = _intake(path=PathId.PATH_1, intent_topic="greeting", raw_message="hi")
    plan = factory.build_from_intake(decision)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_1
    assert plan.intent_topic == "greeting"
    assert plan.source is IntakeSource.FAST_INTAKE
    assert plan.allowed_evidence_tools == []
    assert plan.access_policy is AccessPolicyName.NONE
    assert plan.judge_policy is None
    assert plan.model_profile is None
    assert plan.finalizer_template_key == "path_1.greeting"
    assert plan.finalizer_reason_code is None
    assert plan.canonical_requested_fields == []
    assert plan.target_candidates == []


def test_build_from_intake_path_8_3_empty_message(factory: ExecutionPlanFactory):
    decision = _intake(
        path=PathId.PATH_8_3, intent_topic="empty_message", raw_message=""
    )
    plan = factory.build_from_intake(decision)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_8_3
    assert plan.source is IntakeSource.FAST_INTAKE
    # Path 8 plans use reason_code as intent_topic (Batch 2 spec).
    assert plan.intent_topic == "empty_message"
    assert plan.finalizer_reason_code == "empty_message"
    assert plan.finalizer_template_key == "path_8_3.empty_message"
    assert plan.allowed_evidence_tools == []
    assert plan.access_policy is AccessPolicyName.NONE


def test_build_from_intake_path_8_2_out_of_scope_nonsense(
    factory: ExecutionPlanFactory,
):
    decision = _intake(
        path=PathId.PATH_8_2,
        intent_topic="out_of_scope_nonsense",
        raw_message="?????",
    )
    plan = factory.build_from_intake(decision)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_8_2
    assert plan.intent_topic == "out_of_scope_nonsense"
    assert plan.finalizer_reason_code == "out_of_scope_nonsense"
    assert plan.finalizer_template_key == "path_8_2.out_of_scope_nonsense"


# ─────────────────────────────────────────────────────────────────────────
# build_from_planner — happy path
# ─────────────────────────────────────────────────────────────────────────


def test_build_from_planner_path_4_deadline(factory: ExecutionPlanFactory):
    proposal = _validated_proposal(
        path=PathId.PATH_4, intent_topic="deadline", confidence=0.9,
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_4
    assert plan.intent_topic == "deadline"
    assert plan.source is IntakeSource.PLANNER  # explicit assertion #5
    # Manager tool ids copied from registry (assertion #6).
    assert "get_rfq_profile" in plan.allowed_evidence_tools
    assert plan.access_policy is AccessPolicyName.MANAGER_MEDIATED
    assert plan.judge_policy is not None
    # Empty requested_fields defaulted to allowed_fields (assertion #8).
    assert plan.canonical_requested_fields == ["deadline"]
    assert plan.finalizer_template_key == "path_4.default"
    assert plan.finalizer_reason_code is None
    # Plan target_candidates carried through.
    assert len(plan.target_candidates) == 1


def test_build_from_planner_canonicalizes_aliases(factory: ExecutionPlanFactory):
    """assertion #7: 'due date' alias normalizes to canonical 'deadline'."""
    proposal = _validated_proposal(
        path=PathId.PATH_4,
        intent_topic="deadline",
        confidence=0.9,
        requested_fields=["due date"],
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.canonical_requested_fields == ["deadline"]


def test_build_from_planner_canonicalizes_multiple_aliases(
    factory: ExecutionPlanFactory,
):
    """Path 4 'blockers' intent has 'blockers' as alias for 'blocker_status'."""
    proposal = _validated_proposal(
        path=PathId.PATH_4,
        intent_topic="blockers",
        confidence=0.9,
        requested_fields=["blockers"],
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert "blocker_status" in plan.canonical_requested_fields


def test_empty_requested_fields_defaults_to_allowed(factory: ExecutionPlanFactory):
    """assertion #8: empty requested_fields uses allowed_fields as default."""
    proposal = _validated_proposal(
        path=PathId.PATH_4,
        intent_topic="summary",
        confidence=0.9,
        requested_fields=[],
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    # Path 4 'summary' intent has 6 allowed_fields.
    assert set(plan.canonical_requested_fields) == {
        "name", "client", "status", "priority", "deadline", "current_stage_name",
    }


# ─────────────────────────────────────────────────────────────────────────
# F1 — registry path/intent exists
# ─────────────────────────────────────────────────────────────────────────


def test_f1_unsupported_path_returns_factory_rejection(factory: ExecutionPlanFactory):
    """Path 5 is intentionally absent from Slice 1 PATH_CONFIGS."""
    proposal = _validated_proposal(
        path=PathId.PATH_5, intent_topic="briefing_summary", confidence=0.9,
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.trigger == "unsupported_intent_topic"
    assert result.reason_code == "unsupported_intent"
    assert result.factory_rule == "F1"


def test_f1_unsupported_intent_returns_factory_rejection(
    factory: ExecutionPlanFactory,
):
    """Path 4 exists but 'rocket_science' isn't a configured intent."""
    proposal = _validated_proposal(
        path=PathId.PATH_4, intent_topic="rocket_science", confidence=0.9,
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.factory_rule == "F1"


# ─────────────────────────────────────────────────────────────────────────
# F2 — intake source allowlist
# ─────────────────────────────────────────────────────────────────────────


def test_f2_fast_intake_attempting_path_4(factory: ExecutionPlanFactory):
    """FastIntake is forbidden for operational Path 4 intents."""
    decision = _intake(path=PathId.PATH_4, intent_topic="deadline")
    result = factory.build_from_intake(decision)
    assert isinstance(result, FactoryRejection)
    assert result.trigger == "intake_source_not_allowed"
    assert result.reason_code == "intake_source_not_allowed"
    assert result.factory_rule == "F2"


# ─────────────────────────────────────────────────────────────────────────
# F3 — alias normalization
# ─────────────────────────────────────────────────────────────────────────


def test_f3_unknown_field_alias(factory: ExecutionPlanFactory):
    proposal = _validated_proposal(
        path=PathId.PATH_4,
        intent_topic="deadline",
        confidence=0.9,
        requested_fields=["completely_unknown_word"],
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.trigger == "unsupported_field_requested"
    assert result.factory_rule == "F3"


# ─────────────────────────────────────────────────────────────────────────
# F4 — canonical_requested_fields ⊆ allowed ∪ forbidden
# ─────────────────────────────────────────────────────────────────────────


def test_f4_field_outside_allowed_or_forbidden():
    """Inject a synthetic registry where an alias maps to a canonical
    that's neither in allowed_fields nor in forbidden_fields. F3 will
    accept the alias mapping; F4 catches the orphaned canonical.
    """
    synthetic = PathConfig(
        intent_topics={
            "deadline": IntentConfig(
                allowed_intake_sources=[IntakeSource.PLANNER],
                evidence_tools=[],
                allowed_fields=["deadline"],
                # alias 'orphan' maps to canonical 'undeclared_field' which
                # is NOT in allowed_fields or forbidden_fields.
                field_aliases={"undeclared_field": ["orphan"]},
                confidence_threshold=0.7,
            ),
        },
        resolver_strategy=ResolverStrategy.NONE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        forbidden_fields=[],
        persistence_policy=PersistencePolicy(),
        finalizer_template_key_default="path_4.default",
    )
    registry: PathRegistry = {PathId.PATH_4: synthetic}
    factory = ExecutionPlanFactory(registry=registry)

    proposal = _validated_proposal(
        path=PathId.PATH_4,
        intent_topic="deadline",
        confidence=0.9,
        requested_fields=["orphan"],
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.trigger == "unsupported_field_requested"
    assert result.factory_rule == "F4"


# ─────────────────────────────────────────────────────────────────────────
# F5 — forbidden field requested
# ─────────────────────────────────────────────────────────────────────────


def test_f5_forbidden_field_requested_directly(factory: ExecutionPlanFactory):
    """'margin' is in Path 4 forbidden_fields."""
    proposal = _validated_proposal(
        path=PathId.PATH_4,
        intent_topic="deadline",
        confidence=0.9,
        requested_fields=["margin"],
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.trigger == "forbidden_field_requested"
    assert result.factory_rule == "F5"


# ─────────────────────────────────────────────────────────────────────────
# F6 — confidence threshold
# ─────────────────────────────────────────────────────────────────────────


def test_f6_low_confidence_rejected(factory: ExecutionPlanFactory):
    """Path 4 deadline confidence_threshold=0.75. 0.5 < 0.75 → reject."""
    proposal = _validated_proposal(
        path=PathId.PATH_4, intent_topic="deadline", confidence=0.5,
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.trigger == "confidence_below_threshold"
    assert result.factory_rule == "F6"


def test_f6_does_not_apply_to_fast_intake(factory: ExecutionPlanFactory):
    """FastIntake is deterministic regex — no confidence to check."""
    decision = _intake(path=PathId.PATH_1, intent_topic="greeting")
    plan = factory.build_from_intake(decision)
    assert isinstance(plan, TurnExecutionPlan)


# ─────────────────────────────────────────────────────────────────────────
# Direct Path 8.x planner emissions
# ─────────────────────────────────────────────────────────────────────────


def test_direct_path_8_1_planner_emission(factory: ExecutionPlanFactory):
    proposal = _validated_proposal(
        path=PathId.PATH_8_1, intent_topic="anything", confidence=0.9,
        target_candidates=[],
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.finalizer_reason_code == "unsupported_intent"
    assert plan.finalizer_template_key == "path_8_1.unsupported_intent"
    assert plan.intent_topic == "unsupported_intent"
    assert plan.source is IntakeSource.PLANNER


def test_direct_path_8_2_planner_emission(factory: ExecutionPlanFactory):
    proposal = _validated_proposal(
        path=PathId.PATH_8_2, intent_topic="anything", confidence=0.9,
        target_candidates=[],
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.finalizer_reason_code == "out_of_scope"
    assert plan.finalizer_template_key == "path_8_2.out_of_scope"


def test_direct_path_8_3_planner_emission_with_multi_intent(
    factory: ExecutionPlanFactory,
):
    proposal = _validated_proposal(
        path=PathId.PATH_8_3,
        intent_topic="anything",
        confidence=0.9,
        target_candidates=[],
        multi_intent_detected=True,
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.finalizer_reason_code == "multi_intent_detected"
    assert plan.finalizer_template_key == "path_8_3.multi_intent"


def test_direct_path_8_3_without_multi_intent_falls_to_f1(
    factory: ExecutionPlanFactory,
):
    """Defense in depth: validator should have caught this, but if it
    slips through, factory rejects via F1."""
    proposal = _validated_proposal(
        path=PathId.PATH_8_3,
        intent_topic="anything",
        confidence=0.9,
        target_candidates=[],
        multi_intent_detected=False,
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.factory_rule == "F1"


# ─────────────────────────────────────────────────────────────────────────
# build_from_escalation
# ─────────────────────────────────────────────────────────────────────────


def test_build_from_escalation_path_8_4_access_denied(factory: ExecutionPlanFactory):
    request = EscalationRequest(
        target_path=PathId.PATH_8_4,
        reason_code=ReasonCode("access_denied_explicit"),
        source_stage="access",
        trigger="access_denied_explicit",
    )
    plan = factory.build_from_escalation(request)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_8_4
    assert plan.source is IntakeSource.ESCALATION
    assert plan.finalizer_reason_code == "access_denied_explicit"
    assert plan.finalizer_template_key == "path_8_4.denied"
    # Path 8.x is template-only.
    assert plan.allowed_evidence_tools == []
    assert plan.judge_policy is None
    assert plan.model_profile is None


def test_build_from_escalation_path_8_5_no_evidence(factory: ExecutionPlanFactory):
    request = EscalationRequest(
        target_path=PathId.PATH_8_5,
        reason_code=ReasonCode("no_evidence"),
        source_stage="evidence_check",
        trigger="evidence_empty",
    )
    plan = factory.build_from_escalation(request)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_8_5
    assert plan.finalizer_reason_code == "no_evidence"
    assert plan.finalizer_template_key == "path_8_5.no_evidence"


def test_build_from_escalation_unknown_reason_code_raises(
    factory: ExecutionPlanFactory,
):
    """Loud failure — never invent a fallback template."""
    request = EscalationRequest(
        target_path=PathId.PATH_8_5,
        reason_code=ReasonCode("not_a_real_reason"),
        source_stage="resolver",
        trigger="bogus",
    )
    with pytest.raises(ValueError, match="not_a_real_reason"):
        factory.build_from_escalation(request)


# ─────────────────────────────────────────────────────────────────────────
# F7 — Path 7 Group C (synthetic registry)
# ─────────────────────────────────────────────────────────────────────────


def _synthetic_path_7_registry() -> PathRegistry:
    """Slice 1 PATH_CONFIGS doesn't include Path 7. Inject a minimal
    Path 7 entry so F7 is exercisable today."""
    intent = IntentConfig(
        allowed_intake_sources=[IntakeSource.PLANNER],
        evidence_tools=[],
        allowed_fields=["deadline", "owner"],
        comparable_field_groups=ComparableFieldGroups(
            A=["deadline", "owner"],
            B=[],
            C=["margin", "win_probability"],
        ),
        confidence_threshold=0.7,
    )
    cfg = PathConfig(
        intent_topics={"compare_rfqs": intent},
        resolver_strategy=ResolverStrategy.NONE,
        required_target_policy=TargetPolicy(min_targets=2, max_targets=5),
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        forbidden_fields=["margin", "win_probability"],
        persistence_policy=PersistencePolicy(),
        finalizer_template_key_default="path_7.default",
    )
    return {PathId.PATH_7: cfg}


def test_f7_group_c_field_rejected_with_synthetic_path_7():
    factory = ExecutionPlanFactory(registry=_synthetic_path_7_registry())
    proposal = _validated_proposal(
        path=PathId.PATH_7,
        intent_topic="compare_rfqs",
        confidence=0.9,
        requested_fields=["margin"],
        target_candidates=[
            ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code"),
            ProposedTarget(raw_reference="IF-0042", proposed_kind="rfq_code"),
        ],
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    # 'margin' is in BOTH forbidden_fields AND comparable_field_groups.C.
    # F5 fires before F7 in the factory's rule order, so the trigger is
    # forbidden_field_requested. This is the architecturally-correct
    # cascade: F5 catches all forbidden requests; F7 is the Path-7-
    # specific deeper check for fields that were aliased into Group C
    # via comparable_field_groups but NOT also in forbidden_fields.
    assert result.factory_rule in ("F5", "F7"), (
        f"Expected F5 or F7 for Group C field; got {result.factory_rule}"
    )


def test_f7_group_c_field_only_in_C_not_in_forbidden():
    """Force the F7-only path: a field in Group C but not in
    forbidden_fields. F4 will reject it as 'unknown' (not in allowed
    ∪ forbidden), unless we also put it in allowed_fields. So we put
    'ranking' in allowed_fields AND in C — F5 won't fire (not in
    forbidden); F7 must fire."""
    intent = IntentConfig(
        allowed_intake_sources=[IntakeSource.PLANNER],
        evidence_tools=[],
        allowed_fields=["deadline", "ranking"],
        comparable_field_groups=ComparableFieldGroups(
            A=["deadline"],
            B=[],
            C=["ranking"],
        ),
        confidence_threshold=0.7,
    )
    cfg = PathConfig(
        intent_topics={"compare_rfqs": intent},
        resolver_strategy=ResolverStrategy.NONE,
        required_target_policy=TargetPolicy(min_targets=2, max_targets=5),
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        forbidden_fields=[],
        persistence_policy=PersistencePolicy(),
        finalizer_template_key_default="path_7.default",
    )
    registry: PathRegistry = {PathId.PATH_7: cfg}
    factory = ExecutionPlanFactory(registry=registry)

    proposal = _validated_proposal(
        path=PathId.PATH_7,
        intent_topic="compare_rfqs",
        confidence=0.9,
        requested_fields=["ranking"],
        target_candidates=[
            ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code"),
            ProposedTarget(raw_reference="IF-0042", proposed_kind="rfq_code"),
        ],
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.factory_rule == "F7"
    assert result.trigger == "group_C_field_requested"


# ─────────────────────────────────────────────────────────────────────────
# F8 — Path 3 required query slots (synthetic registry)
# ─────────────────────────────────────────────────────────────────────────


def _synthetic_path_3_registry() -> PathRegistry:
    intent = IntentConfig(
        allowed_intake_sources=[IntakeSource.PLANNER],
        evidence_tools=[],
        required_query_slots=["filters", "output_shape"],
        allowed_fields=["rfq_code", "name"],
        confidence_threshold=0.7,
    )
    cfg = PathConfig(
        intent_topics={"portfolio_search": intent},
        resolver_strategy=ResolverStrategy.NONE,
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        persistence_policy=PersistencePolicy(),
        finalizer_template_key_default="path_3.default",
    )
    return {PathId.PATH_3: cfg}


def test_f8_required_query_slots_missing():
    factory = ExecutionPlanFactory(registry=_synthetic_path_3_registry())
    proposal = _validated_proposal(
        path=PathId.PATH_3,
        intent_topic="portfolio_search",
        confidence=0.9,
        requested_fields=["rfq_code"],
        target_candidates=[],
        # filters + output_shape required but not provided
        filters=None,
        output_shape=None,
    )
    result = factory.build_from_planner(proposal)
    assert isinstance(result, FactoryRejection)
    assert result.factory_rule == "F8"
    assert result.trigger == "pre_search_query_underspecified"


def test_f8_required_query_slots_present_passes():
    factory = ExecutionPlanFactory(registry=_synthetic_path_3_registry())
    proposal = _validated_proposal(
        path=PathId.PATH_3,
        intent_topic="portfolio_search",
        confidence=0.9,
        requested_fields=["rfq_code"],
        target_candidates=[],
        filters={"status": "in_progress"},
        output_shape="list",
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    assert plan.path is PathId.PATH_3


# ─────────────────────────────────────────────────────────────────────────
# Plan integrity — no runtime outcomes; self-contained
# ─────────────────────────────────────────────────────────────────────────


def test_produced_plan_has_no_runtime_outcome_fields(factory: ExecutionPlanFactory):
    """TurnExecutionPlan = strategy + policy ONLY. The plan model itself
    rejects runtime fields via extra='forbid' (Batch 1 contract); this
    test verifies the factory doesn't try to add them and verifies the
    plan structure has only the strategy/policy fields we expect."""
    proposal = _validated_proposal(
        path=PathId.PATH_4, intent_topic="deadline", confidence=0.9
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)

    # The Pydantic model enforces no runtime fields. Inspect the dump
    # to verify none of the forbidden runtime field names exist.
    dumped = plan.model_dump()
    forbidden_runtime = {
        "resolved_targets", "access_decisions", "tool_invocations",
        "tool_results", "evidence_packets", "draft_text", "final_text",
        "judge_verdict", "guardrail_strips", "escalations",
    }
    leaked = forbidden_runtime & dumped.keys()
    assert not leaked, (
        f"Plan contains runtime outcome field(s): {leaked}. These "
        f"belong in ExecutionState, not TurnExecutionPlan."
    )


def test_plan_carries_all_policy_for_self_containment(
    factory: ExecutionPlanFactory,
):
    """The plan must be self-contained — no downstream stage should need
    to read PATH_CONFIGS again. Spot-check the key policy slots."""
    proposal = _validated_proposal(
        path=PathId.PATH_4, intent_topic="deadline", confidence=0.9,
    )
    plan = factory.build_from_planner(proposal)
    assert isinstance(plan, TurnExecutionPlan)
    # Tool list copied from registry (intent-level evidence_tools).
    expected_tools = list(
        PATH_CONFIGS[PathId.PATH_4].intent_topics["deadline"].evidence_tools
    )
    assert plan.allowed_evidence_tools == expected_tools
    # Forbidden fields copied (path-level).
    assert plan.forbidden_fields == list(
        PATH_CONFIGS[PathId.PATH_4].forbidden_fields
    )
    # Memory + persistence policies copied.
    assert plan.memory_policy == PATH_CONFIGS[PathId.PATH_4].memory_policy
    assert plan.persistence_policy == PATH_CONFIGS[PathId.PATH_4].persistence_policy
    # Guardrails copied.
    assert plan.active_guardrails == list(
        PATH_CONFIGS[PathId.PATH_4].active_guardrails
    )
    # Judge policy copied.
    assert plan.judge_policy == PATH_CONFIGS[PathId.PATH_4].judge_policy
    # Model profile copied.
    assert plan.model_profile == PATH_CONFIGS[PathId.PATH_4].model_profile


# ─────────────────────────────────────────────────────────────────────────
# Anti-drift cross-checks (re-asserted in the factory's own test file)
# ─────────────────────────────────────────────────────────────────────────


def test_factory_remains_only_turn_execution_plan_constructor():
    """Re-run the §11.5.1 spirit: AST-grep src/ for TurnExecutionPlan(...)
    calls outside the factory module. Anti-drift guard does the same;
    here we duplicate to fail-fast at the per-module level."""
    import ast as _ast
    from pathlib import Path as _P

    src_dir = _P(__file__).resolve().parents[2] / "src"
    allowed = (src_dir / "pipeline" / "execution_plan_factory.py").resolve()
    offenders: list[tuple[str, int]] = []
    for py in src_dir.rglob("*.py"):
        if py.resolve() == allowed:
            continue
        tree = _ast.parse(py.read_text(encoding="utf-8"))
        for node in _ast.walk(tree):
            if (
                isinstance(node, _ast.Call)
                and isinstance(node.func, _ast.Name)
                and node.func.id == "TurnExecutionPlan"
            ):
                offenders.append((str(py.relative_to(src_dir.parent)), node.lineno))
    assert not offenders, (
        f"TurnExecutionPlan instantiated outside the factory: {offenders}"
    )


def test_registry_config_still_only_imported_by_factory_and_gate():
    """Re-run the §11.5.2 spirit. The Batch 0 anti-drift guard does the
    same; this is a fast-feedback duplicate."""
    import ast as _ast
    from pathlib import Path as _P

    pipeline_dir = _P(__file__).resolve().parents[2] / "src" / "pipeline"
    allowed = {
        (pipeline_dir / "execution_plan_factory.py").resolve(),
        (pipeline_dir / "escalation_gate.py").resolve(),
    }
    offenders: list[tuple[str, int]] = []
    for py in pipeline_dir.rglob("*.py"):
        if py.resolve() in allowed:
            continue
        tree = _ast.parse(py.read_text(encoding="utf-8"))
        for node in _ast.walk(tree):
            if (
                isinstance(node, _ast.ImportFrom)
                and node.module == "src.config.path_registry"
            ):
                offenders.append((py.name, node.lineno))
    assert not offenders, (
        f"src.config.path_registry imported outside factory + gate: {offenders}"
    )
