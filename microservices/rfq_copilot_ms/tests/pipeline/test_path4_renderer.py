"""Path 4 grounded renderer tests (Batch 5)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import (
    EvidencePacket,
    ExecutionState,
    SourceRef,
)
from src.models.path_registry import (
    AccessPolicyName,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ResolverStrategy,
    TargetPolicy,
)
from src.pipeline.path4_renderer import render_path_4


def _state(intent_topic: str, actor, fields: dict, label: str = "IF-0001") -> ExecutionState:
    plan = TurnExecutionPlan(
        path=PathId.PATH_4, intent_topic=intent_topic,
        source=IntakeSource.PLANNER, target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[], allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=[], forbidden_fields=[],
        canonical_requested_fields=[], active_guardrails=[],
        judge_policy=None, memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
    )
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    state.evidence_packets.append(EvidencePacket(
        target_id=uuid4(), target_label=label, fields=fields,
        source_refs=[SourceRef(
            source_type="manager", source_id="x",
            fetched_at=datetime.now(timezone.utc),
        )],
    ))
    return state


def test_deadline_grounded(actor):
    text = render_path_4(_state("deadline", actor, {"deadline": date(2026, 6, 15)}))
    assert text == "IF-0001 deadline is 2026-06-15."


def test_owner_grounded(actor):
    text = render_path_4(_state("owner", actor, {"owner": "Mohamed"}))
    assert text == "IF-0001 is owned by Mohamed."


def test_status_grounded(actor):
    text = render_path_4(_state("status", actor, {"status": "In preparation"}))
    assert text == "IF-0001 status is In preparation."


def test_current_stage_grounded(actor):
    text = render_path_4(_state("current_stage", actor, {"current_stage_name": "Cost estimation"}))
    assert text == "IF-0001 is currently in Cost estimation."


def test_priority_grounded(actor):
    text = render_path_4(_state("priority", actor, {"priority": "Critical"}))
    assert text == "IF-0001 priority is Critical."


def test_blockers_with_active_blocker(actor):
    text = render_path_4(_state("blockers", actor, {
        "active_blocker": {
            "stage_name": "Cost estimation",
            "blocker_status": "blocked",
            "blocker_reason_code": "missing supplier quotes",
        }
    }))
    assert "blocker" in text.lower()
    assert "Cost estimation" in text
    assert "missing supplier quotes" in text


def test_blockers_with_no_active_blocker(actor):
    text = render_path_4(_state("blockers", actor, {"active_blocker": None}))
    assert "don't see" in text.lower() or "no" in text.lower()
    assert "IF-0001" in text


def test_stages_grounded_and_ordered(actor):
    text = render_path_4(_state("stages", actor, {
        "stages": [
            {"name": "Cost estimation", "order": 2, "status": "Active"},
            {"name": "Submission", "order": 3, "status": "Pending"},
            {"name": "Discovery", "order": 1, "status": "Done"},
        ]
    }))
    assert "stages:" in text
    # Ordered by 'order' field — Discovery (1) first, then Cost estimation (2), then Submission (3)
    pos_disc = text.find("Discovery")
    pos_cost = text.find("Cost estimation")
    pos_sub = text.find("Submission")
    assert 0 < pos_disc < pos_cost < pos_sub


def test_summary_uses_only_allowed_fields(actor):
    text = render_path_4(_state("summary", actor, {
        "name": "Refinery Upgrade",
        "client": "ACME Energy",
        "status": "In preparation",
        "priority": "Critical",
        "deadline": date(2026, 7, 1),
        "current_stage_name": "Cost estimation",
    }))
    assert "summary" in text.lower()
    assert "Refinery Upgrade" in text
    assert "ACME Energy" in text
    assert "Critical" in text


def test_missing_evidence_returns_none(actor):
    text = render_path_4(_state("deadline", actor, {}))
    assert text is None


def test_no_evidence_packet_returns_none(actor):
    plan = TurnExecutionPlan(
        path=PathId.PATH_4, intent_topic="deadline",
        source=IntakeSource.PLANNER, target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[], allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=[], forbidden_fields=[],
        canonical_requested_fields=[], active_guardrails=[],
        judge_policy=None, memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
    )
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    assert render_path_4(state) is None


def test_no_internal_path_labels_in_output(actor):
    text = render_path_4(_state("deadline", actor, {"deadline": date(2026, 6, 15)}))
    forbidden = ["Path 4", "PATH_4", "reason_code", "ExecutionPlanFactory", "IntakeSource"]
    for term in forbidden:
        assert term not in text
