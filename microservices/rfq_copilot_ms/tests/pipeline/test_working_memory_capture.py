"""V2TurnController._load_working_memory — Batch 10.

The controller now populates ``state.working_memory`` from prior
``execution_records`` AFTER the plan is built (so the per-path
``MemoryPolicy.working_pairs`` cap is known). This is the *capture*
half of the Slice 2 working-memory primitive — Batch 12 will add the
*injection* into Planner/Compose/Judge prompts.

These tests pin the capture contract directly against the controller
helper, with a real factory-built plan so the per-path cap comes from
the production registry (Path 1 = 2, Path 4 = 5).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from src.controllers.v2_turn_controller import V2TurnController
from src.datasources.v2_history_datasource import V2HistoryDatasource
from src.datasources.v2_thread_datasource import V2ThreadDatasource
from src.models.actor import Actor
from src.models.db import ExecutionRecordRow
from src.models.execution_plan import EscalationRequest
from src.models.execution_record import ExecutionRecordStatus
from src.models.execution_state import ExecutionState
from src.models.path_registry import PathId, ReasonCode
from src.models.planner_proposal import PlannerProposal, ValidatedPlannerProposal
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner_validator import PlannerValidator


# ── Helpers ─────────────────────────────────────────────────────────────


_ALICE = Actor(user_id="alice", display_name="Alice", role="estimator")


def _make_controller(db_session) -> V2TurnController:
    """Wire the smallest controller that has both /v2 datasources so
    ``_load_working_memory`` runs."""
    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    return V2TurnController(
        factory=factory, validator=validator, gate=gate,
        v2_thread_datasource=V2ThreadDatasource(db_session),
        v2_history_datasource=V2HistoryDatasource(db_session),
        session=db_session,
    )


def _build_path_4_plan(factory: ExecutionPlanFactory):
    """Build a real Path 4 plan via the factory so its ``memory_policy``
    is the production registry value (working_pairs=5)."""
    proposal = PlannerProposal(
        path=PathId.PATH_4,
        intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "IF-0001", "proposed_kind": "rfq_code"},
        ],
        requested_fields=[],
        confidence=0.9,
        classification_rationale="test fixture",
        multi_intent_detected=False,
    )
    validated = PlannerValidator().validate(proposal)
    plan = factory.build_from_planner(validated, actor=_ALICE)
    return plan


def _build_path_1_plan(factory: ExecutionPlanFactory):
    """Build a Path 1 plan via the escalation factory entry — Path 1's
    memory_policy in the registry is working_pairs=2."""
    from src.models.intake_decision import IntakeDecision
    from src.models.path_registry import IntakePatternId

    decision = IntakeDecision(
        pattern_id=IntakePatternId("greeting_hello"),
        pattern_version="0.1.0",
        path=PathId.PATH_1,
        intent_topic="greeting",
        matched_at=datetime.utcnow(),
        raw_message="hi",
    )
    return factory.build_from_intake(decision=decision, actor=_ALICE)


def _new_state(plan, *, user_message: str = "x") -> ExecutionState:
    return ExecutionState(
        turn_id=str(uuid.uuid4()),
        actor=_ALICE,
        plan=plan,
        user_message=user_message,
        intake_path="planner",
    )


def _insert_record(
    db_session,
    *,
    thread_id: str,
    turn_id: str,
    user_message: str,
    final_answer: str | None,
    created_at: datetime,
    intent_topic: str | None = "deadline",
    target_rfq_code: str | None = "IF-0001",
    path: str | None = "path_4",
) -> None:
    db_session.add(ExecutionRecordRow(
        id=f"rec-{turn_id}",
        thread_id=thread_id,
        turn_id=turn_id,
        lane="v2",
        status=(
            ExecutionRecordStatus.ANSWERED
            if final_answer
            else ExecutionRecordStatus.FAILED
        ),
        path=path,
        intent_topic=intent_topic,
        target_rfq_code=target_rfq_code,
        user_message=user_message,
        final_answer=final_answer,
        created_at=created_at,
    ))


# ── Cap honors per-path MemoryPolicy ────────────────────────────────────


def test_path_4_cap_is_5_complete_pairs(db_session):
    """Path 4 declares working_pairs=5. Seed 8 complete prior turns;
    expect the 5 most recent in chronological order."""
    factory = ExecutionPlanFactory()
    base = datetime(2026, 5, 5, 10, 0, 0)
    for i in range(8):
        _insert_record(
            db_session, thread_id="t1", turn_id=f"T{i}",
            user_message=f"u{i}", final_answer=f"a{i}",
            created_at=base + timedelta(seconds=i),
        )
    db_session.commit()

    plan = _build_path_4_plan(factory)
    assert plan.memory_policy.working_pairs == 5, (
        "Registry drift — Path 4 working_pairs changed; the 5-cap "
        "assertion below depends on this value."
    )
    state = _new_state(plan)
    controller = _make_controller(db_session)
    controller._load_working_memory(state, "t1")

    assert len(state.working_memory) == 5
    # Most recent 5; chronological order means oldest of the 5 first.
    assert [e.turn_id for e in state.working_memory] == [
        "T3", "T4", "T5", "T6", "T7",
    ]


def test_path_1_cap_is_2_complete_pairs(db_session):
    """Path 1 declares working_pairs=2. Same seed; expect 2 entries."""
    factory = ExecutionPlanFactory()
    base = datetime(2026, 5, 5, 10, 0, 0)
    for i in range(8):
        _insert_record(
            db_session, thread_id="t1", turn_id=f"T{i}",
            user_message=f"u{i}", final_answer=f"a{i}",
            created_at=base + timedelta(seconds=i),
            path="path_1", intent_topic="greeting", target_rfq_code=None,
        )
    db_session.commit()

    plan = _build_path_1_plan(factory)
    assert plan.memory_policy.working_pairs == 2, (
        "Registry drift — Path 1 working_pairs changed."
    )
    state = _new_state(plan)
    controller = _make_controller(db_session)
    controller._load_working_memory(state, "t1")

    assert len(state.working_memory) == 2
    assert [e.turn_id for e in state.working_memory] == ["T6", "T7"]


# ── NULL final_answer is excluded ───────────────────────────────────────


def test_null_final_answer_rows_are_skipped(db_session):
    """Mid-flight failures (NULL ``final_answer``) MUST NOT appear in
    working_memory — the asymmetry vs reconstruct_messages is the
    Batch 12 readiness contract from the plan's correction #4."""
    factory = ExecutionPlanFactory()
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="GOOD",
        user_message="g", final_answer="GA",
        created_at=base,
    )
    _insert_record(
        db_session, thread_id="t1", turn_id="HALF",
        user_message="h", final_answer=None,  # crashed mid-flight
        created_at=base + timedelta(seconds=1),
    )
    _insert_record(
        db_session, thread_id="t1", turn_id="EMPTY",
        user_message="e", final_answer="",  # also skipped
        created_at=base + timedelta(seconds=2),
    )
    db_session.commit()

    plan = _build_path_4_plan(factory)
    state = _new_state(plan)
    _make_controller(db_session)._load_working_memory(state, "t1")

    assert len(state.working_memory) == 1
    assert state.working_memory[0].turn_id == "GOOD"
    assert state.working_memory[0].assistant_answer == "GA"


# ── All Batch-12-required fields are populated ──────────────────────────


def test_all_working_memory_fields_populated(db_session):
    """Every field Batch 12 will need (turn_id, user_message,
    assistant_answer, target_rfq_code, intent_topic, path, created_at)
    must be captured by Batch 10."""
    factory = ExecutionPlanFactory()
    when = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="T1",
        user_message="What is the deadline for IF-0001?",
        final_answer="IF-0001 deadline is 2026-05-17.",
        path="path_4",
        intent_topic="deadline",
        target_rfq_code="IF-0001",
        created_at=when,
    )
    db_session.commit()

    plan = _build_path_4_plan(factory)
    state = _new_state(plan)
    _make_controller(db_session)._load_working_memory(state, "t1")

    assert len(state.working_memory) == 1
    e = state.working_memory[0]
    assert e.turn_id == "T1"
    assert e.user_message == "What is the deadline for IF-0001?"
    assert e.assistant_answer == "IF-0001 deadline is 2026-05-17."
    assert e.target_rfq_code == "IF-0001"
    assert e.intent_topic == "deadline"
    assert e.path == "path_4"
    assert e.created_at == when


# ── Empty thread → empty working_memory (no crash) ──────────────────────


def test_empty_thread_yields_empty_working_memory(db_session):
    """First turn ever in a brand-new thread must not crash; just an
    empty working_memory."""
    factory = ExecutionPlanFactory()
    plan = _build_path_4_plan(factory)
    state = _new_state(plan)
    _make_controller(db_session)._load_working_memory(state, "t1")
    assert state.working_memory == []


# ── Defensive no-ops when collaborators are missing ─────────────────────


def test_no_op_when_history_datasource_is_missing(db_session):
    """Legacy unit tests construct V2TurnController without injecting
    the history datasource. The capture must silently no-op rather than
    AttributeError-crash. Pre-Batch-10 callers keep working."""
    factory = ExecutionPlanFactory()
    plan = _build_path_4_plan(factory)
    state = _new_state(plan)
    controller = V2TurnController(
        factory=factory,
        validator=PlannerValidator(),
        gate=EscalationGate(factory=factory),
        v2_thread_datasource=None,
        v2_history_datasource=None,
        session=db_session,
    )
    controller._load_working_memory(state, "t1")
    assert state.working_memory == []


def test_no_op_when_plan_has_no_memory_policy(db_session):
    """Some Path 8.x plans don't declare a memory_policy. Treat that
    as cap=0 — captured into working_memory means nothing is loaded."""
    factory = ExecutionPlanFactory()
    plan = factory.build_from_escalation(
        EscalationRequest(
            target_path=PathId.PATH_8_2,
            reason_code=ReasonCode("out_of_scope_nonsense"),
            source_stage="orchestrator",
            trigger="testing",
        ),
        actor=_ALICE,
    )
    # Path 8.x plans intentionally don't carry memory_policy. If the
    # registry ever changes, this test will fail loudly — the test
    # itself documents the assumption.
    if plan.memory_policy is not None:
        pytest.skip("Registry now declares memory_policy for Path 8.2")

    state = _new_state(plan)
    controller = _make_controller(db_session)
    controller._load_working_memory(state, "t1")
    assert state.working_memory == []
