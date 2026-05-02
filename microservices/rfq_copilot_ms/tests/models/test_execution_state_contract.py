"""Contract tests — ExecutionState + runtime sub-objects (§2.5, §14.4).

Mirror image of the TurnExecutionPlan tests: these assert that runtime
outcome fields are ACCEPTED on ExecutionState (where they belong), that
the container is mutable (so stages can append), and that list defaults
are isolated between instances (the classic Pydantic mutable-default
trap).
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import (
    AccessDecision,
    EscalationEvent,
    EvidencePacket,
    ExecutionState,
    GuardrailAction,
    JudgeVerdict,
    JudgeViolation,
    ResolvedTarget,
    SourceRef,
    ToolInvocation,
)
from src.models.path_registry import (
    AccessPolicyName,
    GuardrailId,
    IntakeSource,
    JudgeTriggerName,
    PathId,
    PersistencePolicy,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
    ToolId,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _actor() -> Actor:
    return Actor(user_id="u1", display_name="User One", role="estimator")


def _minimal_plan() -> TurnExecutionPlan:
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic="deadline",
        source=IntakeSource.PLANNER,
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4_default",
    )


def _minimal_state_kwargs():
    return dict(
        turn_id="turn-001",
        actor=_actor(),
        plan=_minimal_plan(),
        user_message="What's the deadline for IF-0001?",
        intake_path="planner",
    )


# ── Minimal valid construction ─────────────────────────────────────────────


def test_minimal_execution_state_constructs():
    s = ExecutionState(**_minimal_state_kwargs())
    assert s.turn_id == "turn-001"
    assert s.intake_path == "planner"
    # All list/optional fields default to empty/None:
    assert s.resolved_targets == []
    assert s.tool_invocations == []
    assert s.draft_text is None
    assert s.judge_verdict is None
    assert s.final_text is None
    assert s.escalations == []


def test_execution_state_intake_path_is_closed_literal():
    """``intake_path`` must be ``"fast_intake"`` or ``"planner"`` — no
    third value."""
    bad = _minimal_state_kwargs() | {"intake_path": "rogue"}
    with pytest.raises(ValidationError):
        ExecutionState(**bad)


# ── Runtime outcome fields are ACCEPTED here ──────────────────────────────


def test_execution_state_accepts_resolved_targets():
    target = ResolvedTarget(
        rfq_id=uuid4(),
        rfq_label="IF-0001",
        resolution_method="search_by_code",
    )
    s = ExecutionState(
        **_minimal_state_kwargs() | {"resolved_targets": [target]}
    )
    assert len(s.resolved_targets) == 1


def test_execution_state_accepts_tool_invocations():
    inv = ToolInvocation(
        tool_name=ToolId("get_rfq_profile"),
        args={"rfq_id": "IF-0001"},
        result_summary="ok",
        latency_ms=120,
        status="ok",
    )
    s = ExecutionState(**_minimal_state_kwargs() | {"tool_invocations": [inv]})
    assert s.tool_invocations[0].latency_ms == 120


def test_execution_state_accepts_evidence_packets():
    packet = EvidencePacket(
        target_label="IF-0001",
        fields={"deadline": "2026-06-15"},
        source_refs=[
            SourceRef(
                source_type="manager",
                source_id="/rfq-manager/v1/rfqs/IF-0001",
                fetched_at=datetime(2026, 5, 2, 12, 0, 0),
            )
        ],
    )
    s = ExecutionState(**_minimal_state_kwargs() | {"evidence_packets": [packet]})
    assert s.evidence_packets[0].target_label == "IF-0001"


def test_execution_state_accepts_draft_and_final_text():
    s = ExecutionState(
        **_minimal_state_kwargs()
        | {"draft_text": "draft", "final_text": "final", "final_path": PathId.PATH_4}
    )
    assert s.draft_text == "draft"
    assert s.final_text == "final"
    assert s.final_path is PathId.PATH_4


def test_execution_state_accepts_judge_verdict():
    verdict = JudgeVerdict(
        verdict="pass",
        triggers_checked=[JudgeTriggerName("answer_makes_factual_claim")],
        violations=[],
        rationale="grounded in provided fields",
        latency_ms=200,
    )
    s = ExecutionState(**_minimal_state_kwargs() | {"judge_verdict": verdict})
    assert s.judge_verdict.verdict == "pass"


def test_execution_state_accepts_escalation_events():
    ev = EscalationEvent(
        trigger="manager_unreachable",
        reason_code=ReasonCode("source_unavailable"),
        source_stage="tool_executor",
        fired_at=datetime(2026, 5, 2, 12, 0, 0),
    )
    s = ExecutionState(**_minimal_state_kwargs() | {"escalations": [ev]})
    assert s.escalations[0].source_stage == "tool_executor"


def test_execution_state_accepts_guardrail_strips():
    action = GuardrailAction(
        guardrail_id=GuardrailId("evidence"),
        action="strip_claim",
        reason="ungrounded",
        affected_text="some claim",
    )
    s = ExecutionState(**_minimal_state_kwargs() | {"guardrail_strips": [action]})
    assert s.guardrail_strips[0].action == "strip_claim"


# ── Mutability ─────────────────────────────────────────────────────────────


def test_execution_state_is_mutable():
    """Stages MUST be able to append/assign as they run. Freezing would
    defeat the partial-write semantics that execution_records (§4)
    relies on for forensics survivability."""
    s = ExecutionState(**_minimal_state_kwargs())

    s.draft_text = "draft from Compose"
    assert s.draft_text == "draft from Compose"

    s.final_text = "final from Finalizer"
    s.final_path = PathId.PATH_4
    assert s.final_text == "final from Finalizer"
    assert s.final_path is PathId.PATH_4

    s.tool_invocations.append(
        ToolInvocation(
            tool_name=ToolId("get_rfq_profile"),
            args={},
            result_summary="ok",
            latency_ms=1,
            status="ok",
        )
    )
    assert len(s.tool_invocations) == 1


# ── List default isolation (the Pydantic mutable-default trap) ────────────


def test_list_defaults_are_isolated_between_instances():
    """The classic Pydantic mutable-default trap: if list fields used
    ``= []`` instead of ``Field(default_factory=list)``, all instances
    would share the same list object and mutations on one would leak
    into others.

    This test creates two ExecutionState instances, mutates each one's
    list independently, and asserts the lists are separate identities.
    """
    s1 = ExecutionState(**_minimal_state_kwargs() | {"turn_id": "turn-001"})
    s2 = ExecutionState(**_minimal_state_kwargs() | {"turn_id": "turn-002"})

    # Different list identities — not the same Python object.
    assert s1.resolved_targets is not s2.resolved_targets
    assert s1.tool_invocations is not s2.tool_invocations
    assert s1.evidence_packets is not s2.evidence_packets
    assert s1.escalations is not s2.escalations
    assert s1.guardrail_strips is not s2.guardrail_strips
    assert s1.working_memory is not s2.working_memory

    # Mutating one does not affect the other.
    s1.resolved_targets.append(
        ResolvedTarget(
            rfq_id=uuid4(),
            rfq_label="IF-0001",
            resolution_method="search_by_code",
        )
    )
    assert len(s1.resolved_targets) == 1
    assert len(s2.resolved_targets) == 0


# ── extra="forbid" is still on for ExecutionState ─────────────────────────


def test_execution_state_rejects_unknown_fields():
    bad = _minimal_state_kwargs() | {"some_new_unspec_field": True}
    with pytest.raises(ValidationError, match="extra"):
        ExecutionState(**bad)


# ── Frozen sub-records ─────────────────────────────────────────────────────


def test_resolved_target_is_frozen():
    t = ResolvedTarget(
        rfq_id=uuid4(),
        rfq_label="IF-0001",
        resolution_method="search_by_code",
    )
    with pytest.raises(ValidationError):
        t.rfq_label = "different"  # type: ignore[misc]


def test_evidence_packet_is_frozen():
    p = EvidencePacket(target_label="IF-0001")
    with pytest.raises(ValidationError):
        p.target_label = "different"  # type: ignore[misc]


def test_judge_violation_construction():
    v = JudgeViolation(
        trigger=JudgeTriggerName("answer_makes_factual_claim"),
        reason_code=ReasonCode("judge_verdict_fabrication"),
        excerpt="I think the deadline might be...",
    )
    assert v.excerpt is not None
