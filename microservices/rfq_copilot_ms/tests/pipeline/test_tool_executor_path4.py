"""Path 4 ToolExecutor tests (Batch 5)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import ExecutionState, ResolvedTarget
from src.models.path_registry import (
    AccessPolicyName,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ResolverStrategy,
    TargetPolicy,
    ToolId,
)
from src.pipeline.errors import StageError
from src.pipeline.tool_executor import execute_path_4
from tests.conftest import FakeManagerConnector


def _build_path_4_plan(
    intent_topic: str = "deadline",
    allowed_evidence_tools: list[ToolId] | None = None,
    canonical_requested_fields: list[str] | None = None,
) -> TurnExecutionPlan:
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic=intent_topic,
        source=IntakeSource.PLANNER,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=allowed_evidence_tools or [ToolId("get_rfq_profile")],
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


def _state(plan: TurnExecutionPlan, actor, target_code: str = "IF-0001") -> ExecutionState:
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    state.resolved_targets.append(
        ResolvedTarget(
            rfq_id=uuid4(), rfq_code=target_code, rfq_label=target_code,
            resolution_method="search_by_code",
        )
    )
    return state


def test_get_rfq_profile_calls_manager(actor, fake_manager: FakeManagerConnector):
    fake_manager.set_rfq_detail("IF-0001")
    plan = _build_path_4_plan(
        allowed_evidence_tools=[ToolId("get_rfq_profile")],
        canonical_requested_fields=["deadline"],
    )
    state = _state(plan, actor)
    execute_path_4(state=state, actor=actor, manager=fake_manager)
    methods_called = [m for m, *_ in fake_manager.calls]
    assert "get_rfq_detail" in methods_called
    assert state.tool_invocations[0].tool_name == "get_rfq_profile"


def test_get_rfq_stages_calls_manager(actor, fake_manager: FakeManagerConnector):
    fake_manager.set_rfq_detail("IF-0001")
    fake_manager.set_rfq_stages("IF-0001", [
        {"name": "Cost estimation", "order": 1, "status": "Active"},
    ])
    plan = _build_path_4_plan(
        intent_topic="stages",
        allowed_evidence_tools=[ToolId("get_rfq_stages")],
        canonical_requested_fields=["name", "order", "status"],
    )
    plan = plan.model_copy(update={"allowed_fields": ["name", "order", "status"]})
    state = _state(plan, actor)
    execute_path_4(state=state, actor=actor, manager=fake_manager)
    methods_called = [m for m, *_ in fake_manager.calls]
    assert "get_rfq_stages" in methods_called
    # Stages were projected into the packet.
    packet = state.evidence_packets[0]
    assert "stages" in packet.fields
    assert len(packet.fields["stages"]) == 1


def test_unknown_tool_id_raises(actor, fake_manager: FakeManagerConnector):
    plan = _build_path_4_plan(
        allowed_evidence_tools=[ToolId("never_heard_of_this_tool")],
    )
    state = _state(plan, actor)
    with pytest.raises(StageError) as exc_info:
        execute_path_4(state=state, actor=actor, manager=fake_manager)
    assert exc_info.value.trigger == "unknown_tool"


def test_tool_not_in_plan_is_not_executed(actor, fake_manager: FakeManagerConnector):
    """Plan declares only get_rfq_profile; get_rfq_stages must not be called."""
    fake_manager.set_rfq_detail("IF-0001")
    plan = _build_path_4_plan(
        allowed_evidence_tools=[ToolId("get_rfq_profile")],
    )
    state = _state(plan, actor)
    execute_path_4(state=state, actor=actor, manager=fake_manager)
    methods_called = [m for m, *_ in fake_manager.calls]
    assert "get_rfq_stages" not in methods_called


def test_tool_results_stored_in_state(actor, fake_manager: FakeManagerConnector):
    fake_manager.set_rfq_detail("IF-0001")
    plan = _build_path_4_plan()
    state = _state(plan, actor)
    execute_path_4(state=state, actor=actor, manager=fake_manager)
    assert len(state.tool_invocations) == 1
    assert len(state.evidence_packets) == 1


def test_manager_unavailable_routes_to_8_5(actor, fake_manager: FakeManagerConnector):
    fake_manager.set_unreachable()
    plan = _build_path_4_plan()
    state = _state(plan, actor)
    with pytest.raises(StageError) as exc_info:
        execute_path_4(state=state, actor=actor, manager=fake_manager)
    assert exc_info.value.trigger == "manager_unreachable"


def test_cached_rfq_detail_avoids_redundant_call(actor, fake_manager: FakeManagerConnector):
    """Access stage cached the detail; ToolExecutor should reuse, not refetch."""
    detail = fake_manager.set_rfq_detail("IF-0001")
    plan = _build_path_4_plan()
    state = _state(plan, actor)
    execute_path_4(
        state=state, actor=actor, manager=fake_manager, cached_rfq_detail=detail,
    )
    # No manager calls should have happened (cache hit).
    methods_called = [m for m, *_ in fake_manager.calls]
    assert methods_called == []
    # But the tool invocation was still recorded.
    assert state.tool_invocations[0].latency_ms == 0  # cached marker
