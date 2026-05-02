"""Path 4 ContextBuilder tests (Batch 5)."""

from __future__ import annotations

from datetime import datetime, timezone
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
from src.pipeline.context_builder import build_path_4


def _plan(canonical_requested: list[str], allowed_fields: list[str], forbidden: list[str]):
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic="deadline",
        source=IntakeSource.PLANNER,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[],
        allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=allowed_fields,
        forbidden_fields=forbidden,
        canonical_requested_fields=canonical_requested,
        active_guardrails=[],
        judge_policy=None,
        memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
        model_profile=None,
    )


def _state(plan, actor, packet_fields: dict) -> ExecutionState:
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    state.evidence_packets.append(
        EvidencePacket(
            target_id=uuid4(), target_label="IF-0001",
            fields=packet_fields,
            source_refs=[SourceRef(
                source_type="manager", source_id="x",
                fetched_at=datetime.now(timezone.utc),
            )],
        )
    )
    return state


def test_per_target_packet_preserved(actor):
    plan = _plan(["deadline"], ["deadline"], [])
    state = _state(plan, actor, {"deadline": "2026-06-15"})
    build_path_4(state)
    assert len(state.evidence_packets) == 1
    assert state.evidence_packets[0].target_label == "IF-0001"


def test_filters_out_unrequested_fields(actor):
    """ToolExecutor accidentally surfaced 'extra_field'. ContextBuilder
    drops it from the packet."""
    plan = _plan(["deadline"], ["deadline"], [])
    state = _state(plan, actor, {"deadline": "2026-06-15", "extra_field": "leak"})
    build_path_4(state)
    fields = state.evidence_packets[0].fields
    assert "deadline" in fields
    assert "extra_field" not in fields


def test_includes_source_refs(actor):
    plan = _plan(["deadline"], ["deadline"], [])
    state = _state(plan, actor, {"deadline": "2026-06-15"})
    build_path_4(state)
    refs = state.evidence_packets[0].source_refs
    assert len(refs) == 1
    assert refs[0].source_type == "manager"


def test_does_not_include_forbidden_fields(actor):
    """If somehow a forbidden field surfaced in the packet, ContextBuilder
    strips it (defense in depth — F5 should have rejected upstream)."""
    plan = _plan(["deadline"], ["deadline"], ["margin"])
    state = _state(plan, actor, {
        "deadline": "2026-06-15",
        "margin": 12.5,  # forbidden but somehow leaked
    })
    build_path_4(state)
    assert "margin" not in state.evidence_packets[0].fields


def test_synthetic_keys_pass_through(actor):
    """The synthetic keys 'stages' and 'active_blocker' (Tool Executor
    composites) always pass the whitelist filter."""
    plan = _plan(["name", "order", "status"], ["name", "order", "status"], [])
    state = _state(plan, actor, {
        "stages": [{"name": "Stage 1", "order": 1, "status": "Done"}],
    })
    build_path_4(state)
    assert "stages" in state.evidence_packets[0].fields


def test_active_blocker_synthetic_passes(actor):
    plan = _plan(["blocker_status"], ["blocker_status"], [])
    state = _state(plan, actor, {"active_blocker": None})
    build_path_4(state)
    assert "active_blocker" in state.evidence_packets[0].fields
