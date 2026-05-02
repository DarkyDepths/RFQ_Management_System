"""Smoke — /v2 Path 4 manager-grounded operational core (Batch 5).

End-to-end /v2 turns with FakeLlmConnector + FakeManagerConnector
injected via FastAPI ``dependency_overrides``. No real Azure /
manager_ms calls.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.app_context import (
    get_manager_connector,
    get_planner,
    get_v2_turn_controller,
)
from src.controllers.v2_turn_controller import V2TurnController
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
def client_with_overrides():
    """Yield a TestClient with controllable fakes. Use the returned
    helper to set up the fake responses BEFORE making the request."""
    fake_llm = FakeLlmConnector()
    fake_manager = FakeManagerConnector()

    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    planner = Planner(llm_connector=fake_llm)

    def _override_controller():
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=planner, manager=fake_manager,
        )

    app.dependency_overrides[get_v2_turn_controller] = _override_controller

    try:
        client = TestClient(app)
        yield client, fake_llm, fake_manager
    finally:
        app.dependency_overrides.pop(get_v2_turn_controller, None)


def test_v2_deadline_returns_grounded_answer(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[{"raw_reference": "IF-0001", "proposed_kind": "rfq_code"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-0001?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "answered"
    assert body["path"] == "path_4"
    assert body["intent_topic"] == "deadline"
    assert "2026-06-15" in body["answer"]
    assert "IF-0001" in body["answer"]


def test_v2_owner_returns_grounded_answer(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0001", owner="Mohamed")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="owner",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Who owns IF-0001?"},
    )
    assert r.status_code == 200
    assert "Mohamed" in r.json()["answer"]


def test_v2_status_returns_grounded_answer(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0001", status="In preparation")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="status",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the status of IF-0001?"},
    )
    assert r.status_code == 200
    assert "In preparation" in r.json()["answer"]


def test_v2_current_stage_with_page_context(client_with_overrides):
    """User on the IF-0042 page asks 'what is the current stage?' —
    Planner emits page_default; Resolver picks up current_rfq_code."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0042", current_stage_name="Cost estimation")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="current_stage",
        target_candidates=[{"raw_reference": "", "proposed_kind": "page_default"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the current stage?", "current_rfq_code": "IF-0042"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "IF-0042" in body["answer"]
    assert "Cost estimation" in body["answer"]


def test_v2_blockers_with_page_context(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0042")
    fake_manager.set_rfq_stages("IF-0042", [
        {"name": "Cost estimation", "order": 1, "status": "Active",
         "blocker_status": "blocked", "blocker_reason_code": "missing_quotes"},
    ])
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="blockers",
        target_candidates=[{"raw_reference": "", "proposed_kind": "page_default"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Is it blocked?", "current_rfq_code": "IF-0042"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "blocker" in body["answer"].lower()
    assert "missing_quotes" in body["answer"]


def test_v2_stages_returns_grounded_ordered_answer(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0001")
    fake_manager.set_rfq_stages("IF-0001", [
        {"name": "Discovery", "order": 1, "status": "Done"},
        {"name": "Cost estimation", "order": 2, "status": "Active"},
        {"name": "Submission", "order": 3, "status": "Pending"},
    ])
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="stages",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Show stages for IF-0001"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    assert "Discovery" in answer
    assert "Cost estimation" in answer
    # Ordering check
    assert answer.find("Discovery") < answer.find("Cost estimation")


def test_v2_summary_returns_grounded_answer(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail(
        "IF-0001", name="Refinery Upgrade", client="ACME Energy",
        priority="Critical", deadline=date(2026, 8, 1),
    )
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="summary",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Give summary for IF-0001"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    assert "Refinery Upgrade" in answer
    assert "ACME Energy" in answer


def test_v2_no_target_no_context_routes_to_8_3(client_with_overrides):
    """Planner emits page_default but no current_rfq_code provided."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[{"raw_reference": "", "proposed_kind": "page_default"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "what is the deadline?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_8_3"
    assert body["status"] == "answered"
    # Path 8.3 templates ask the user to clarify — no fake answer.


def test_v2_manager_not_found_routes_to_8_4(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.mark_not_found("IF-9999")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[{"raw_reference": "IF-9999", "proposed_kind": "rfq_code"}],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-9999?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_8_4"
    assert "access" in body["answer"].lower() or "RFQ" in body["answer"]


def test_v2_manager_unavailable_routes_to_8_5(client_with_overrides):
    client, fake_llm, fake_manager = client_with_overrides
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
    assert body["path"] == "path_8_5"
    assert "shortly" in body["answer"].lower() or "unavailable" in body["answer"].lower()


def test_v2_recipe_request_routes_to_8_2(client_with_overrides):
    """Planner direct-emits 8.2 for clearly out-of-scope asks."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_llm.set_response(planner_proposal_json(
        path="path_8_2", intent_topic="out_of_scope",
        target_candidates=[],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "write me a recipe"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_8_2"


def test_v2_fast_intake_messages_still_work(client_with_overrides):
    """FastIntake still wins before the planner runs."""
    client, fake_llm, fake_manager = client_with_overrides
    # Don't queue an LLM response — FastIntake must short-circuit BEFORE
    # the planner is consulted.
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 200
    assert r.json()["path"] == "path_1"
    assert len(fake_llm.calls) == 0  # planner never called


def test_v1_functional_smoke_still_passes():
    """Sanity: /v1 thread create still works alongside /v2 changes."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from src.database import Base, get_session
    from src.models.db import AuditLogRow, ThreadRow, TurnRow  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _override_session():
        session = SessionFactory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_session
    try:
        client = TestClient(app)
        r = client.post(
            "/rfq-copilot/v1/threads/new",
            json={"mode": {"kind": "general"}},
        )
        assert r.status_code == 200
        assert "thread_id" in r.json()
    finally:
        app.dependency_overrides.pop(get_session, None)
