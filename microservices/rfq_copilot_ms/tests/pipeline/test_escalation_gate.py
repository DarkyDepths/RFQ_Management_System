"""EscalationGate tests (Batch 5)."""

from __future__ import annotations

import ast
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import ExecutionState
from src.models.path_registry import PathId, ReasonCode
from src.pipeline import escalation_gate as gate_module
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory


def _state_with_placeholder_plan(actor: Actor) -> ExecutionState:
    """Build a minimal ExecutionState with a placeholder Path 8.1 plan
    (the Gate immediately swaps it for the real Path 8.x plan)."""
    factory = ExecutionPlanFactory()
    from src.models.execution_plan import EscalationRequest
    placeholder = factory.build_from_escalation(
        EscalationRequest(
            target_path=PathId.PATH_8_1,
            reason_code=ReasonCode("unsupported_intent"),
            source_stage="orchestrator",
            trigger="placeholder",
        ),
        actor=actor,
    )
    return ExecutionState(
        turn_id="t1",
        actor=actor,
        plan=placeholder,
        user_message="hi",
        intake_path="planner",
    )


@pytest.fixture
def gate() -> EscalationGate:
    return EscalationGate(factory=ExecutionPlanFactory())


def test_unclear_intent_topic_routes_to_path_8_3(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    gate.route(
        state,
        trigger="unclear_intent_topic",
        reason_code=ReasonCode("unclear_intent_topic"),
        source_stage="validator",
    )
    assert state.plan.path is PathId.PATH_8_3
    assert state.plan.finalizer_template_key == "path_8_3.unclear_intent"
    assert len(state.escalations) == 1


def test_forbidden_field_routes_to_path_8_1(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    gate.route(
        state,
        trigger="forbidden_field_requested",
        reason_code=ReasonCode("forbidden_field_requested"),
        source_stage="factory",
    )
    assert state.plan.path is PathId.PATH_8_1
    assert state.plan.finalizer_template_key == "path_8_1.forbidden_field"


def test_manager_unreachable_routes_to_path_8_5(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    gate.route(
        state,
        trigger="manager_unreachable",
        reason_code=ReasonCode("source_unavailable"),
        source_stage="tool_executor",
    )
    assert state.plan.path is PathId.PATH_8_5
    assert state.plan.finalizer_template_key == "path_8_5.source_unavailable"


def test_access_denied_routes_to_path_8_4(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    gate.route(
        state,
        trigger="access_denied_explicit",
        reason_code=ReasonCode("access_denied_explicit"),
        source_stage="access",
    )
    assert state.plan.path is PathId.PATH_8_4
    assert state.plan.finalizer_template_key == "path_8_4.denied"


def test_no_evidence_routes_to_path_8_5(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    gate.route(
        state,
        trigger="evidence_empty",
        reason_code=ReasonCode("no_evidence"),
        source_stage="evidence_check",
    )
    assert state.plan.path is PathId.PATH_8_5
    assert state.plan.finalizer_template_key == "path_8_5.no_evidence"


def test_llm_unavailable_routes_to_path_8_5(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    gate.route(
        state,
        trigger="llm_unavailable",
        reason_code=ReasonCode("llm_unavailable"),
        source_stage="planner",
    )
    assert state.plan.path is PathId.PATH_8_5
    assert state.plan.finalizer_template_key == "path_8_5.llm_unavailable"


def test_unmapped_trigger_raises_value_error(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    with pytest.raises(ValueError, match="no Path 8.x mapping"):
        gate.route(
            state,
            trigger="totally_invented_trigger",
            reason_code=ReasonCode("x"),
            source_stage="resolver",
        )


def test_gate_appends_escalation_event(actor: Actor, gate: EscalationGate):
    state = _state_with_placeholder_plan(actor)
    initial_count = len(state.escalations)
    gate.route(
        state,
        trigger="evidence_empty",
        reason_code=ReasonCode("no_evidence"),
        source_stage="evidence_check",
        details={"missing_field": "deadline"},
    )
    assert len(state.escalations) == initial_count + 1
    event = state.escalations[-1]
    assert event.trigger == "evidence_empty"
    assert event.source_stage == "evidence_check"
    assert event.details == {"missing_field": "deadline"}


def test_gate_resets_partial_final_text(actor: Actor, gate: EscalationGate):
    """If the renderer partially populated final_text before a downstream
    failure, the Gate must reset it so the Finalizer renders the safe
    Path 8.x template instead."""
    state = _state_with_placeholder_plan(actor)
    state.final_text = "leaked partial output"
    state.final_path = PathId.PATH_4
    gate.route(
        state,
        trigger="evidence_empty",
        reason_code=ReasonCode("no_evidence"),
        source_stage="evidence_check",
    )
    assert state.final_text is None
    assert state.final_path is None


def test_gate_does_not_construct_turn_execution_plan_directly():
    """AST guard: EscalationGate source must not contain a
    TurnExecutionPlan(...) call. The Gate uses the factory's
    build_from_escalation() instead."""
    src_path = Path(inspect.getfile(gate_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "TurnExecutionPlan"
        ):
            pytest.fail(
                f"EscalationGate constructs TurnExecutionPlan at line "
                f"{node.lineno}. Must use factory.build_from_escalation."
            )
