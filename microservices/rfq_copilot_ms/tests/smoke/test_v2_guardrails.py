"""Smoke — /v2 guardrail integration (Batch 7).

Verifies that when a guardrail catches a leaky/dangerous Path 4 answer:
* The orchestrator routes via the EscalationGate to Path 8.5.
* The user-facing answer is the safe template (no leak).
* The execution_records row records the escalation with the guardrail
  trigger / reason_code.

Uses ``unittest.mock.patch`` to force ``path4_renderer.render_path_4``
to return a leaky string — the production renderer can't naturally
produce one (only renders evidence-packed fields), so we inject it.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

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

    def _override_controller():
        s = SessionFactory()
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=planner, manager=fake_manager, session=s,
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


# ── Happy path: existing Path 4 answers still pass guardrails ───────────


def test_v2_path_4_normal_deadline_passes_guardrails(smoke):
    """Existing Batch 5 happy path — verify guardrails don't break it."""
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
    assert body["path"] == "path_4"
    assert "2026-06-15" in body["answer"]
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.status == ExecutionRecordStatus.ANSWERED


def test_v2_path_4_normal_stages_passes_guardrails(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_manager.set_rfq_stages("IF-0001", [
        {"name": "Discovery", "order": 1, "status": "Done"},
        {"name": "Cost estimation", "order": 2, "status": "Active"},
    ])
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="stages",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Show stages for IF-0001"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == "path_4"
    assert "Discovery" in body["answer"]
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.status == ExecutionRecordStatus.ANSWERED


# ── Guardrail failure -> safe Path 8.5 answer + persisted escalation ───


def _patched_renderer(leaky_text: str):
    """Helper: returns a context manager that patches path4_renderer
    to return the given leaky string instead of the real grounded answer."""
    from src.pipeline import path4_renderer
    return patch.object(path4_renderer, "render_path_4", return_value=leaky_text)


def test_v2_forbidden_field_leak_routes_to_path_8_5(smoke):
    """Renderer leaks 'margin'. Forbidden_field guardrail catches.
    Gate routes to Path 8.5. User gets safe template. Persisted as escalated."""
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    with _patched_renderer("IF-0001 margin is 12.5%"):
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "what is the deadline?"},
        )

    assert r.status_code == 200, r.text
    body = r.json()
    # Routed to Path 8.5 — user got safe template, NOT the leaky answer.
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == "forbidden_inference_detected_deterministic"
    assert "margin" not in body["answer"].lower()
    # Persistence captures the escalation.
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record is not None
    assert record.status == ExecutionRecordStatus.ESCALATED
    assert record.path == "path_8_5"
    assert record.reason_code == "forbidden_inference_detected_deterministic"
    assert len(record.escalations_json) >= 1
    escalation = record.escalations_json[0]
    assert escalation["source_stage"] == "guardrail"
    assert escalation["details"]["guardrail"] == "forbidden_field"


def test_v2_internal_label_leak_routes_to_path_8_5(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    with _patched_renderer("Routing to path_4 with reason_code=ok"):
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "what is the deadline?"},
        )

    body = r.json()
    assert body["path"] == "path_8_5"
    assert "path_4" not in body["answer"]
    assert "reason_code" not in body["answer"]
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.escalations_json[0]["details"]["guardrail"] == "internal_label"


def test_v2_intelligence_claim_leak_routes_to_path_8_5(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    with _patched_renderer("IF-0001 has a high win probability and we should bid"):
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "what is the deadline?"},
        )

    body = r.json()
    assert body["path"] == "path_8_5"
    assert "win probability" not in body["answer"].lower()
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.escalations_json[0]["details"]["guardrail"] == "scope"


def test_v2_raw_json_dump_routes_to_path_8_5(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    with _patched_renderer('{"deadline": "2026-06-15", "raw": true}'):
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "what is the deadline?"},
        )

    body = r.json()
    assert body["path"] == "path_8_5"
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.escalations_json[0]["details"]["guardrail"] == "shape"


def test_v2_traceback_leak_routes_to_path_8_5(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    with _patched_renderer(
        'Traceback (most recent call last):\n  File "x.py", line 1, in <module>\nKeyError: \'deadline\''
    ):
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "what is the deadline?"},
        )

    body = r.json()
    assert body["path"] == "path_8_5"
    assert "Traceback" not in body["answer"]
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.escalations_json[0]["details"]["guardrail"] == "shape"


# ── Safe Path 8.5 wording (no internal labels in user answer) ──────────


def test_safe_path_8_5_answer_does_not_leak_guardrail_internals(smoke):
    """The safe template the user sees must NOT mention which guardrail
    fired or what the original (rejected) answer was."""
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    with _patched_renderer("IF-0001 margin is 12.5%"):
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "what is the deadline?"},
        )

    answer = r.json()["answer"]
    forbidden_in_user_answer = [
        "margin",  # the rejected leak
        "guardrail",  # internal stage name
        "forbidden_field",  # internal guardrail id
        "forbidden_inference_detected_deterministic",  # internal reason_code
        "Path 8.5", "PATH_8_5", "path_8_5",  # internal labels
    ]
    for term in forbidden_in_user_answer:
        assert term not in answer, (
            f"safe template leaked internal {term!r}: {answer!r}"
        )
