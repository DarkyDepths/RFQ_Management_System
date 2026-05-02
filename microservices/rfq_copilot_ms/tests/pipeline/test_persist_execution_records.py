"""Persist stage tests (Batch 6)."""

from __future__ import annotations

import ast
import inspect
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.datasources.execution_record_datasource import (
    ExecutionRecordDatasource,
)
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_record import ExecutionRecordStatus
from src.models.execution_state import (
    EscalationEvent,
    EvidencePacket,
    ExecutionState,
    ResolvedTarget,
    SourceRef,
    ToolInvocation,
)
from src.models.intake_decision import IntakeDecision
from src.models.path_registry import (
    AccessPolicyName,
    IntakePatternId,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
    ToolId,
)
from src.pipeline import persist as persist_module
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.persist import persist_execution_record


# ── Plan fixtures ────────────────────────────────────────────────────────


def _path_4_plan() -> TurnExecutionPlan:
    factory = ExecutionPlanFactory()
    from src.models.planner_proposal import (
        PlannerProposal, ProposedTarget, ValidatedPlannerProposal,
    )
    proposal = PlannerProposal(
        path=PathId.PATH_4, intent_topic="deadline", confidence=0.9,
        classification_rationale="x",
        target_candidates=[ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code")],
    )
    validated = ValidatedPlannerProposal(
        proposal=proposal, validated_at=datetime.now(timezone.utc),
    )
    plan = factory.build_from_planner(validated)
    assert isinstance(plan, TurnExecutionPlan)
    return plan


def _path_8_5_plan() -> TurnExecutionPlan:
    from src.models.execution_plan import EscalationRequest
    factory = ExecutionPlanFactory()
    return factory.build_from_escalation(
        EscalationRequest(
            target_path=PathId.PATH_8_5,
            reason_code=ReasonCode("source_unavailable"),
            source_stage="tool_executor",
            trigger="manager_unreachable",
        )
    )


def _path_8_3_plan() -> TurnExecutionPlan:
    from src.models.execution_plan import EscalationRequest
    factory = ExecutionPlanFactory()
    return factory.build_from_escalation(
        EscalationRequest(
            target_path=PathId.PATH_8_3,
            reason_code=ReasonCode("no_target_proposed"),
            source_stage="resolver",
            trigger="no_target_proposed",
        )
    )


def _path_8_4_plan() -> TurnExecutionPlan:
    from src.models.execution_plan import EscalationRequest
    factory = ExecutionPlanFactory()
    return factory.build_from_escalation(
        EscalationRequest(
            target_path=PathId.PATH_8_4,
            reason_code=ReasonCode("access_denied_explicit"),
            source_stage="access",
            trigger="access_denied_explicit",
        )
    )


def _path_1_plan() -> TurnExecutionPlan:
    factory = ExecutionPlanFactory()
    decision = IntakeDecision(
        pattern_id=IntakePatternId("greeting_v1"),
        pattern_version="1.0.0-batch4",
        path=PathId.PATH_1,
        intent_topic="greeting",
        matched_at=datetime.now(timezone.utc),
        raw_message="hi",
    )
    return factory.build_from_intake(decision)


def _state(plan, actor, **state_kwargs) -> ExecutionState:
    return ExecutionState(
        turn_id=str(uuid4()),
        actor=actor,
        plan=plan,
        user_message="x",
        intake_path=state_kwargs.get("intake_path", "planner"),
        registry_version="0.1.0-slice1",
        **{k: v for k, v in state_kwargs.items() if k != "intake_path"},
    )


# ── 1. Path 1 FastIntake answer persists ────────────────────────────────


def test_persists_path_1_fast_intake_answer(db_session, actor):
    plan = _path_1_plan()
    state = _state(plan, actor, intake_path="fast_intake")
    state.final_text = "Hi — I can help."
    state.final_path = PathId.PATH_1
    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="hi", final_answer="Hi — I can help.",
        status=ExecutionRecordStatus.ANSWERED,
    )
    assert record is not None
    assert record.path == "path_1"
    assert record.intent_topic == "greeting"
    assert record.intake_source == "fast_intake"
    assert record.final_answer == "Hi — I can help."
    assert record.status == ExecutionRecordStatus.ANSWERED


# ── 2. Path 4 manager-grounded answer with tools + evidence ─────────────


def test_persists_path_4_with_tools_and_evidence(db_session, actor):
    plan = _path_4_plan()
    target = ResolvedTarget(
        rfq_id=uuid4(), rfq_code="IF-0001", rfq_label="IF-0001",
        resolution_method="search_by_code",
    )
    state = _state(plan, actor)
    state.resolved_targets.append(target)
    state.tool_invocations.append(ToolInvocation(
        tool_name=ToolId("get_rfq_profile"),
        args={"rfq_code": "IF-0001"},
        result_summary="ok",
        latency_ms=12,
        status="ok",
    ))
    state.evidence_packets.append(EvidencePacket(
        target_id=target.rfq_id, target_label="IF-0001",
        fields={"deadline": date(2026, 6, 15)},  # date that needs JSON conversion
        source_refs=[SourceRef(
            source_type="manager", source_id="get_rfq_profile:IF-0001",
            fetched_at=datetime.now(timezone.utc),
        )],
    ))
    state.final_text = "IF-0001 deadline is 2026-06-15."
    state.final_path = PathId.PATH_4

    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="when due IF-0001?",
        final_answer="IF-0001 deadline is 2026-06-15.",
        status=ExecutionRecordStatus.ANSWERED,
        duration_ms=120,
    )
    assert record is not None
    assert record.path == "path_4"
    assert record.intent_topic == "deadline"
    assert record.target_rfq_code == "IF-0001"
    assert record.tool_invocations_json[0]["tool_name"] == "get_rfq_profile"
    # Evidence ref should NOT contain raw field values (just keys + source_refs).
    ref = record.evidence_refs_json[0]
    assert ref["target_label"] == "IF-0001"
    assert "deadline" in ref["field_keys"]
    assert ref["source_refs"][0]["source_type"] == "manager"


# ── 3. Path 8.3 clarification with reason_code ──────────────────────────


def test_persists_path_8_3_with_reason_code(db_session, actor):
    plan = _path_8_3_plan()
    state = _state(plan, actor)
    state.final_text = "Which RFQ are you asking about?"
    state.final_path = PathId.PATH_8_3
    state.escalations.append(EscalationEvent(
        trigger="no_target_proposed",
        reason_code=ReasonCode("no_target_proposed"),
        source_stage="resolver",
        fired_at=datetime.now(timezone.utc),
    ))
    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="what's the deadline?",
        final_answer=state.final_text,
        status=ExecutionRecordStatus.ESCALATED,
    )
    assert record is not None
    assert record.path == "path_8_3"
    assert record.reason_code == "no_target_proposed"
    assert record.status == ExecutionRecordStatus.ESCALATED
    assert len(record.escalations_json) == 1
    assert record.escalations_json[0]["source_stage"] == "resolver"


# ── 4. Path 8.4 inaccessible with escalation ────────────────────────────


def test_persists_path_8_4_with_escalation(db_session, actor):
    plan = _path_8_4_plan()
    state = _state(plan, actor)
    state.final_text = "I can't access that RFQ."
    state.final_path = PathId.PATH_8_4
    state.escalations.append(EscalationEvent(
        trigger="access_denied_explicit",
        reason_code=ReasonCode("access_denied_explicit"),
        source_stage="access",
        fired_at=datetime.now(timezone.utc),
    ))
    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="what is IF-9999 status?",
        final_answer=state.final_text,
        status=ExecutionRecordStatus.ESCALATED,
    )
    assert record is not None
    assert record.path == "path_8_4"
    assert record.reason_code == "access_denied_explicit"
    assert record.escalations_json[0]["trigger"] == "access_denied_explicit"


# ── 5. Path 8.5 source unavailable with error_payload ────────────────────


def test_persists_path_8_5_with_error_payload(db_session, actor):
    plan = _path_8_5_plan()
    state = _state(plan, actor)
    state.final_text = "Try again shortly."
    state.final_path = PathId.PATH_8_5
    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="x", final_answer=state.final_text,
        status=ExecutionRecordStatus.ESCALATED,
        error_payload={"type": "ManagerUnreachable", "message": "503"},
    )
    assert record is not None
    assert record.path == "path_8_5"
    assert record.reason_code == "source_unavailable"
    assert record.error_json["type"] == "ManagerUnreachable"


# ── 6. Pydantic models serialize safely ──────────────────────────────────


def test_pydantic_models_serialize_safely(db_session, actor):
    """Plan + tool_invocations + evidence_packets contain Pydantic
    models, dates, UUIDs, enums. All must serialize cleanly to JSON."""
    plan = _path_4_plan()
    target = ResolvedTarget(
        rfq_id=uuid4(), rfq_code="IF-0001", rfq_label="IF-0001",
        resolution_method="search_by_code",
    )
    state = _state(plan, actor)
    state.resolved_targets.append(target)
    state.evidence_packets.append(EvidencePacket(
        target_id=target.rfq_id, target_label="IF-0001",
        fields={"deadline": date(2026, 6, 15), "id": uuid4()},
        source_refs=[],
    ))
    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="x", final_answer="ok",
        status=ExecutionRecordStatus.ANSWERED,
    )
    assert record is not None
    # plan_json must be a dict with ISO date / enum-as-string.
    assert record.plan_json["path"] == "path_4"
    assert record.plan_json["source"] == "planner"
    # state_json must NOT include duplicated plan/tool_invocations/etc.
    assert "plan" not in record.state_json
    assert "tool_invocations" not in record.state_json


# ── 7. No secrets in persisted output ────────────────────────────────────


def test_does_not_persist_environment_secrets(db_session, actor, monkeypatch):
    """Set a fake AZURE_OPENAI_API_KEY in env and verify it never
    appears in the persisted JSON."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-secret-DO-NOT-LOG")
    plan = _path_1_plan()
    state = _state(plan, actor, intake_path="fast_intake")
    state.final_text = "hi"
    state.final_path = PathId.PATH_1
    record = persist_execution_record(
        session=db_session, state=state, thread_id="t1",
        user_message="hi", final_answer="hi",
        status=ExecutionRecordStatus.ANSWERED,
    )
    assert record is not None
    serialized = str(record.model_dump())
    assert "test-secret-DO-NOT-LOG" not in serialized
    assert "AZURE_OPENAI_API_KEY" not in serialized


# ── 8. Persist failure does not raise in non-strict mode ─────────────────


def test_persist_failure_returns_none_when_strict_false(actor):
    """Pass a closed/broken session — persist_execution_record returns
    None (and logs); does not raise."""
    plan = _path_1_plan()
    state = _state(plan, actor, intake_path="fast_intake")
    state.final_text = "hi"
    state.final_path = PathId.PATH_1

    class _BrokenSession:
        def add(self, _): raise RuntimeError("broken")
        def commit(self): raise RuntimeError("broken")
        def refresh(self, _): raise RuntimeError("broken")

    record = persist_execution_record(
        session=_BrokenSession(),  # type: ignore[arg-type]
        state=state, thread_id="t1",
        user_message="hi", final_answer="hi",
        status=ExecutionRecordStatus.ANSWERED,
        strict=False,
    )
    assert record is None  # graceful failure


# ── 9. Persist failure raises in strict mode ─────────────────────────────


def test_persist_failure_raises_when_strict_true(actor):
    plan = _path_1_plan()
    state = _state(plan, actor, intake_path="fast_intake")
    state.final_text = "hi"
    state.final_path = PathId.PATH_1

    class _BrokenSession:
        def add(self, _): raise RuntimeError("broken db")
        def commit(self): raise RuntimeError("broken db")
        def refresh(self, _): raise RuntimeError("broken db")

    with pytest.raises(RuntimeError, match="broken db"):
        persist_execution_record(
            session=_BrokenSession(),  # type: ignore[arg-type]
            state=state, thread_id="t1",
            user_message="hi", final_answer="hi",
            status=ExecutionRecordStatus.ANSWERED,
            strict=True,
        )


# ── 10. Anti-drift: no registry config import ────────────────────────────


def test_persist_does_not_import_registry_config():
    src_path = Path(inspect.getfile(persist_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.config.path_registry":
            pytest.fail(
                f"Persist must not import src.config.path_registry "
                f"(line {node.lineno})."
            )


# ── 11. Anti-drift: no TurnExecutionPlan instantiation ───────────────────


def test_persist_does_not_construct_turn_execution_plan():
    src_path = Path(inspect.getfile(persist_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "TurnExecutionPlan"
        ):
            pytest.fail(
                f"Persist constructs TurnExecutionPlan at line "
                f"{node.lineno}. Only the factory may do that."
            )


# ── 12. Anti-drift: no manager / LLM imports ─────────────────────────────


def test_persist_does_not_import_manager_or_llm():
    src_path = Path(inspect.getfile(persist_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    forbidden = {
        "src.connectors.llm_connector",
        "src.connectors.manager_ms_connector",
        "openai", "anthropic", "httpx", "requests",
    }
    leaked = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top_level = node.module.split(".")[0]
            if node.module in forbidden or top_level in forbidden:
                leaked.append(node.module)
    assert not leaked, (
        f"Persist imports forbidden modules: {leaked}. "
        f"It must be a pure DB sink."
    )
