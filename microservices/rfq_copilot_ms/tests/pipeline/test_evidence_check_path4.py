"""Path 4 EvidenceCheck tests (Batch 5)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

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
from src.pipeline.errors import StageError
from src.pipeline.evidence_check import check_path_4


def _plan(
    intent_topic: str = "deadline",
    canonical_requested_fields: list[str] | None = None,
) -> TurnExecutionPlan:
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic=intent_topic,
        source=IntakeSource.PLANNER,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[],
        allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=["deadline"],
        forbidden_fields=[],
        canonical_requested_fields=canonical_requested_fields or ["deadline"],
        active_guardrails=[],
        judge_policy=None,
        memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
        model_profile=None,
    )


def _state_with_packet(plan, actor, fields: dict) -> ExecutionState:
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    state.evidence_packets.append(
        EvidencePacket(
            target_id=uuid4(), target_label="IF-0001",
            fields=fields,
            source_refs=[SourceRef(
                source_type="manager", source_id="x",
                fetched_at=datetime.now(timezone.utc),
            )],
        )
    )
    return state


def test_deadline_present_passes(actor):
    state = _state_with_packet(
        _plan("deadline", ["deadline"]), actor,
        fields={"deadline": date(2026, 6, 15)},
    )
    check_path_4(state)  # no exception


def test_owner_present_passes(actor):
    state = _state_with_packet(
        _plan("owner", ["owner"]), actor,
        fields={"owner": "Alice"},
    )
    check_path_4(state)


def test_missing_field_routes_to_no_evidence(actor):
    state = _state_with_packet(
        _plan("deadline", ["deadline"]), actor,
        fields={"owner": "Alice"},  # deadline missing
    )
    with pytest.raises(StageError) as exc_info:
        check_path_4(state)
    assert exc_info.value.trigger == "evidence_empty"
    assert exc_info.value.reason_code == "no_evidence"


def test_null_field_routes_to_no_evidence(actor):
    state = _state_with_packet(
        _plan("owner", ["owner"]), actor,
        fields={"owner": None},
    )
    with pytest.raises(StageError):
        check_path_4(state)


def test_empty_string_field_routes_to_no_evidence(actor):
    state = _state_with_packet(
        _plan("owner", ["owner"]), actor,
        fields={"owner": "   "},
    )
    with pytest.raises(StageError):
        check_path_4(state)


def test_blockers_intent_with_active_blocker_passes(actor):
    plan = _plan("blockers", ["blocker_status", "blocker_reason_code"])
    state = _state_with_packet(plan, actor, fields={
        "active_blocker": {
            "stage_name": "Cost estimation",
            "blocker_status": "blocked",
            "blocker_reason_code": "missing_data",
        }
    })
    check_path_4(state)


def test_blockers_intent_with_no_active_blocker_passes(actor):
    """active_blocker=None means 'we checked and there's no blocker' —
    grounded evidence, not missing evidence."""
    plan = _plan("blockers", ["blocker_status"])
    state = _state_with_packet(plan, actor, fields={"active_blocker": None})
    check_path_4(state)


def test_blockers_intent_without_active_blocker_key_routes_to_no_evidence(actor):
    """If the active_blocker key was never written, the stages tool didn't
    run / didn't produce blocker info — escalate."""
    plan = _plan("blockers", ["blocker_status"])
    state = _state_with_packet(plan, actor, fields={"deadline": date(2026, 6, 15)})
    with pytest.raises(StageError):
        check_path_4(state)


def test_stages_intent_with_stage_list_passes(actor):
    plan = _plan("stages", ["name", "order", "status"])
    state = _state_with_packet(plan, actor, fields={
        "stages": [
            {"name": "Stage 1", "order": 1, "status": "Done"},
        ]
    })
    check_path_4(state)


def test_stages_intent_with_empty_list_routes_to_no_evidence(actor):
    plan = _plan("stages", ["name"])
    state = _state_with_packet(plan, actor, fields={"stages": []})
    with pytest.raises(StageError):
        check_path_4(state)


def test_no_evidence_packets_routes_to_no_evidence(actor):
    plan = _plan("deadline", ["deadline"])
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    # No packets appended.
    with pytest.raises(StageError) as exc_info:
        check_path_4(state)
    assert exc_info.value.trigger == "evidence_empty"
