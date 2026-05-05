"""POST /v2/threads/{id}/turn requires a registered thread (Batch 10).

Pins the option-(b) contract from the Batch 10 plan: any /turn against
a thread_id that doesn't exist in ``v2_threads`` returns 404
``ThreadNotFoundError``. No 200, no 500, no invisible auto-create.

Why this is its own test file separate from the ownership smoke:
documents the option-(b) contract explicitly so a future maintainer
considering "let's auto-create unknown thread ids to fix UI breakage"
sees one test that exists specifically to forbid it.
"""

from __future__ import annotations

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
from src.datasources.v2_history_datasource import V2HistoryDatasource
from src.datasources.v2_thread_datasource import V2ThreadDatasource
from src.models.db import (  # noqa: F401 — register tables
    AuditLogRow,
    ExecutionRecordRow,
    ThreadRow,
    TurnRow,
    V2ThreadRow,
)
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner import Planner
from src.pipeline.planner_validator import PlannerValidator
from tests.conftest import FakeLlmConnector, FakeManagerConnector


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
            planner=planner, manager=fake_manager,
            llm_connector=fake_llm,
            v2_thread_datasource=V2ThreadDatasource(s),
            v2_history_datasource=V2HistoryDatasource(s),
            session=s,
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_v2_turn_controller] = _override_controller

    try:
        client = TestClient(app)
        yield client, fake_llm, SessionFactory
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_v2_turn_controller, None)
        engine.dispose()


def test_turn_with_unknown_thread_returns_404(smoke):
    client, _, _ = smoke
    r = client.post(
        "/rfq-copilot/v2/threads/unknown-id-not-in-db/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "ThreadNotFoundError"


def test_turn_with_unknown_thread_does_not_persist_execution_record(smoke):
    """Reject early: no pipeline work and no execution_record insert
    for an unknown thread. Otherwise a probing client could pollute
    the forensics table with junk rows keyed by attacker-chosen ids."""
    client, _, SessionFactory = smoke
    client.post(
        "/rfq-copilot/v2/threads/junk-id/turn",
        json={"message": "hello"},
    )
    s = SessionFactory()
    try:
        ds = ExecutionRecordDatasource(s)
        assert ds.list_by_thread_id("junk-id") == []
    finally:
        s.close()


def test_turn_with_uuid_shaped_unknown_thread_still_404(smoke):
    """An attacker who guesses a well-formed UUID still gets 404 — not
    a 5xx. Protects against shape-based dispatch ambiguity."""
    client, _, _ = smoke
    r = client.post(
        "/rfq-copilot/v2/threads/00000000-0000-0000-0000-000000000000/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "ThreadNotFoundError"


def test_turn_with_known_thread_succeeds(smoke):
    """Sanity inverse: a freshly-created thread immediately accepts
    turns — the gate is the *only* extra requirement, not a new general
    failure mode."""
    client, _, _ = smoke
    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    r = client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 200
    assert r.json()["path"] == "path_1"
