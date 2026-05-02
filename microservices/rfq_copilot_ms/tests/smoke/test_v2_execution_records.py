"""Smoke — /v2 execution_records persistence (Batch 6).

End-to-end /v2 turns with FakeLlmConnector + FakeManagerConnector +
in-memory SQLite session. Verifies the controller persists every
turn and the response carries ``execution_record_id``.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.app_context import get_session, get_v2_turn_controller
from src.controllers.v2_turn_controller import V2TurnController
from src.database import Base
from src.datasources.execution_record_datasource import (
    ExecutionRecordDatasource,
)
from src.models.db import (  # noqa: F401 — register tables
    AuditLogRow,
    ExecutionRecordRow,
    ThreadRow,
    TurnRow,
)
from src.models.execution_record import ExecutionRecordStatus
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner import Planner
from src.pipeline.planner_validator import PlannerValidator
from tests.conftest import (
    FakeLlmConnector,
    FakeManagerConnector,
    planner_proposal_json,
)


@pytest.fixture
def smoke():
    """Yield (client, fake_llm, fake_manager, session_factory). The
    controller is wired with a fresh in-memory SQLite + fakes so the
    full /v2 flow including persistence runs in isolation."""
    fake_llm = FakeLlmConnector()
    fake_manager = FakeManagerConnector()

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionFactory = sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )

    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    planner = Planner(llm_connector=fake_llm)

    def _override_session():
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

    def _override_controller(db=None):
        # FastAPI calls this with the overridden session via Depends —
        # but pytest passes nothing. Build a fresh session inside.
        s = SessionFactory()
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=planner, manager=fake_manager,
            session=s, registry_version="0.1.0-slice1-test",
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_v2_turn_controller] = _override_controller

    try:
        client = TestClient(app)
        yield client, fake_llm, fake_manager, SessionFactory
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_v2_turn_controller, None)
        engine.dispose()


def _ds(SessionFactory) -> ExecutionRecordDatasource:
    return ExecutionRecordDatasource(SessionFactory())


# ── 1. /v2 greeting persists ────────────────────────────────────────────


def test_v2_greeting_persists_with_execution_record_id(smoke):
    client, _fake_llm, _fake_manager, SessionFactory = smoke
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn", json={"message": "hello"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["execution_record_id"] is not None
    # Verify the row exists in DB.
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record is not None
    assert record.path == "path_1"
    assert record.intent_topic == "greeting"
    assert record.intake_source == "fast_intake"
    assert record.status == ExecutionRecordStatus.ANSWERED
    assert record.user_message == "hello"
    assert record.final_answer  # non-empty


# ── 2. /v2 deadline persists with manager evidence ──────────────────────


def test_v2_path_4_deadline_persists_full_forensics(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-0001?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["execution_record_id"] is not None

    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record is not None
    # 3. Forensic checks
    assert record.path == "path_4"
    assert record.intent_topic == "deadline"
    assert record.target_rfq_code == "IF-0001"
    assert record.intake_source == "planner"
    assert "2026-06-15" in record.final_answer
    # Tool invocations recorded
    assert len(record.tool_invocations_json) >= 1
    tool_names = [inv["tool_name"] for inv in record.tool_invocations_json]
    assert "get_rfq_profile" in tool_names
    # Evidence refs recorded with manager source
    assert record.evidence_refs_json
    ref = record.evidence_refs_json[0]
    assert ref["target_label"] == "IF-0001"
    assert ref["source_refs"][0]["source_type"] == "manager"
    # Plan + planner proposal captured
    assert record.plan_json["path"] == "path_4"
    assert record.planner_proposal_json["intent_topic"] == "deadline"


# ── 4. /v2 missing target persists Path 8.3 reason_code ─────────────────


def test_v2_missing_target_persists_path_8_3(smoke):
    client, fake_llm, _fake_manager, SessionFactory = smoke
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[{"raw_reference": "", "proposed_kind": "page_default"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "what is the deadline?"},
    )
    assert r.status_code == 200
    body = r.json()
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record is not None
    assert record.path == "path_8_3"
    assert record.reason_code == "no_target_proposed"
    assert record.status == ExecutionRecordStatus.ESCALATED
    assert len(record.escalations_json) >= 1


# ── 5. /v2 manager not found persists Path 8.4 reason_code ──────────────


def test_v2_manager_not_found_persists_path_8_4(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.mark_not_found("IF-9999")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[{"raw_reference": "IF-9999", "proposed_kind": "rfq_code"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-9999?"},
    )
    assert r.status_code == 200
    body = r.json()
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record is not None
    assert record.path == "path_8_4"
    assert record.reason_code == "access_denied_explicit"
    assert record.status == ExecutionRecordStatus.ESCALATED


# ── 6. /v2 manager unavailable persists Path 8.5 reason_code ────────────


def test_v2_manager_unavailable_persists_path_8_5(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_unreachable()
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-0001?"},
    )
    assert r.status_code == 200
    body = r.json()
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record is not None
    assert record.path == "path_8_5"
    assert record.reason_code == "source_unavailable"
    assert record.status == ExecutionRecordStatus.ESCALATED


# ── 7. /v2 persistence failure still returns answer (no record_id) ──────


def test_v2_persistence_failure_returns_answer_with_null_record_id():
    """If the session is broken, the controller still returns the safe
    answer; execution_record_id is None."""
    fake_llm = FakeLlmConnector()
    fake_manager = FakeManagerConnector()
    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    planner = Planner(llm_connector=fake_llm)

    class _BrokenSession:
        def add(self, _): raise RuntimeError("db down")
        def commit(self): raise RuntimeError("db down")
        def refresh(self, _): raise RuntimeError("db down")

    def _override_controller():
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=planner, manager=fake_manager,
            session=_BrokenSession(),  # type: ignore[arg-type]
        )

    app.dependency_overrides[get_v2_turn_controller] = _override_controller
    try:
        client = TestClient(app)
        # FastIntake hit — answer should still come through.
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn", json={"message": "hello"}
        )
        assert r.status_code == 200
        body = r.json()
        assert body["answer"]  # non-empty
        assert body["execution_record_id"] is None
    finally:
        app.dependency_overrides.pop(get_v2_turn_controller, None)


# ── 8 / 9 / 10. Existing capabilities still work ────────────────────────


def test_v1_functional_smoke_still_passes_with_persist_wired():
    """Sanity: /v1 thread create still works; Persist only added to /v2."""
    from src.database import Base, get_session as v1_get_session
    from src.models.db import (  # noqa: F401
        AuditLogRow, ExecutionRecordRow, ThreadRow, TurnRow,
    )

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _override():
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[v1_get_session] = _override
    try:
        client = TestClient(app)
        r = client.post(
            "/rfq-copilot/v1/threads/new",
            json={"mode": {"kind": "general"}},
        )
        assert r.status_code == 200
        assert "thread_id" in r.json()
    finally:
        app.dependency_overrides.pop(v1_get_session, None)


def test_v2_records_are_distinct_per_turn(smoke):
    """Two turns on the same thread produce two distinct execution
    records, ordered newest first."""
    client, fake_llm, _fake_manager, SessionFactory = smoke
    # Turn 1: greeting
    r1 = client.post(
        "/rfq-copilot/v2/threads/multi/turn", json={"message": "hello"}
    )
    # Turn 2: another greeting (uses no LLM)
    r2 = client.post(
        "/rfq-copilot/v2/threads/multi/turn", json={"message": "thanks"}
    )
    assert r1.status_code == 200 and r2.status_code == 200
    id1 = r1.json()["execution_record_id"]
    id2 = r2.json()["execution_record_id"]
    assert id1 and id2 and id1 != id2

    rows = _ds(SessionFactory).list_by_thread_id("multi")
    assert len(rows) == 2
    # Newest first.
    assert rows[0].id == id2
    assert rows[1].id == id1
