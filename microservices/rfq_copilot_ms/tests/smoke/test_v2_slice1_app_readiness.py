"""Slice 1 app-readiness smoke (Batch 9).

End-to-end smoke focused on the *frontend-facing contract* and on
operational fallbacks. No new pipeline behavior is exercised — only
the stable response shape, the safety of failure modes, the readiness
endpoint, and the per-turn log line.

Conventions:
* All upstreams are faked via ``dependency_overrides``. No real Azure
  calls. No real manager calls.
* Each test asserts the response shape directly so the frontend can
  rely on the documented contract.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.app_context import (
    get_planner,
    get_session,
    get_v2_turn_controller,
)
from src.controllers.v2_turn_controller import V2TurnController
from src.database import Base
from src.models.db import (  # noqa: F401 — register tables
    AuditLogRow,
    ExecutionRecordRow,
    ThreadRow,
    TurnRow,
)
from src.models.v2_turn import V2TurnResponse
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner import Planner
from src.pipeline.planner_validator import PlannerValidator
from tests.conftest import (
    FakeLlmConnector,
    FakeManagerConnector,
    planner_proposal_json,
)


# ── Documented stable response keys (frontend contract — Batch 9) ───────


_REQUIRED_RESPONSE_KEYS: frozenset[str] = frozenset({
    "lane",
    "status",
    "thread_id",
    "turn_id",
    "answer",
    "path",
    "intent_topic",
    "reason_code",
    "target_rfq_code",
    "execution_record_id",
})


def _assert_stable_contract(body: dict) -> None:
    """Hard contract assertion — keys, no surprise additions."""
    assert set(body.keys()) == _REQUIRED_RESPONSE_KEYS, (
        f"Response keys drifted from documented contract. "
        f"Got: {sorted(body.keys())}, expected: {sorted(_REQUIRED_RESPONSE_KEYS)}"
    )
    assert body["lane"] == "v2"
    assert body["status"] == "answered"
    assert isinstance(body["answer"], str) and body["answer"]
    # Required keys may be None but must exist.
    assert "path" in body


# ── Fixture ──────────────────────────────────────────────────────────────


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
            llm_connector=fake_llm, session=s,
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_v2_turn_controller] = _override_controller

    try:
        client = TestClient(app)
        yield client, fake_llm, fake_manager
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_v2_turn_controller, None)
        engine.dispose()


# ── 1. Stable contract — FastIntake ─────────────────────────────────────


def test_response_contract_fastintake(smoke):
    client, fake_llm, fake_manager = smoke
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 200
    body = r.json()
    _assert_stable_contract(body)
    assert body["path"] == "path_1"
    # turn_id is populated on every turn.
    assert body["turn_id"]
    # FastIntake never resolves a target.
    assert body["target_rfq_code"] is None
    # Persistence wired in this fixture; record id should be populated.
    assert body["execution_record_id"]


# ── 2. Stable contract — Path 4 ─────────────────────────────────────────


def test_response_contract_path_4(smoke):
    client, fake_llm, fake_manager = smoke
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
    _assert_stable_contract(body)
    assert body["path"] == "path_4"
    assert body["intent_topic"] == "deadline"
    assert body["target_rfq_code"] == "IF-0001"
    assert "2026-06-15" in body["answer"]


# ── 3. Stable contract — Path 8 ─────────────────────────────────────────


def test_response_contract_path_8(smoke):
    client, fake_llm, fake_manager = smoke
    fake_llm.set_response(planner_proposal_json(
        path="path_8_2", intent_topic="out_of_scope",
        target_candidates=[],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "write me a recipe"},
    )
    assert r.status_code == 200
    body = r.json()
    _assert_stable_contract(body)
    assert body["path"] == "path_8_2"
    # Path 8.x has no resolved target.
    assert body["target_rfq_code"] is None


# ── 4. No unsafe draft text in any response (Compose+Judge) ─────────────


def test_no_unsafe_draft_text_in_judge_fail_response(smoke):
    """Judge rejects the draft. The user must NOT see the draft body
    OR any of its content — only the safe template."""
    client, fake_llm, fake_manager = smoke
    fake_manager.set_rfq_detail(
        "IF-0001", name="Refinery", client="ACME",
    )
    fake_llm.set_responses([
        planner_proposal_json(
            path="path_4", intent_topic="summary",
            target_candidates=[
                {"raw_reference": "IF-0001", "proposed_kind": "rfq_code"},
            ],
        ),
        # Compose draft is benign-looking (deterministic guardrails see
        # nothing wrong); only the Judge fails it.
        '{"draft_text": "IF-0001 (Refinery) for ACME, due 2026-08-01.", '
        '"used_source_refs": ["s1"]}',
        # Judge says fabrication.
        '{"verdict":"fail","violations":'
        '[{"trigger":"fabrication","excerpt":"some claim"}],'
        '"rationale":"x"}',
    ])
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "summary of IF-0001"},
    )
    body = r.json()
    _assert_stable_contract(body)
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == "judge_verdict_fabrication"
    # Substantive content from the rejected draft must be absent.
    assert "Refinery" not in body["answer"]
    assert "ACME" not in body["answer"]
    assert "2026-08-01" not in body["answer"]


# ── 5. No planner rationale leaks into responses ────────────────────────


def test_no_planner_rationale_in_response(smoke):
    """The planner's classification_rationale is forensic; never goes
    to the user."""
    client, fake_llm, fake_manager = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        classification_rationale=(
            "SECRET_CHAIN_OF_THOUGHT: I think the user means..."
        ),
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "deadline of IF-0001?"},
    )
    body = r.json()
    assert "SECRET_CHAIN_OF_THOUGHT" not in body["answer"]
    assert "rationale" not in body  # not part of the contract


# ── 6. No stack traces in normal responses ──────────────────────────────


def test_no_stack_trace_in_response(smoke):
    """Generic guardrail — even if something goes sideways, the user
    response body must be clean of debugging artefacts."""
    client, fake_llm, fake_manager = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "deadline of IF-0001?"},
    )
    body = r.json()
    text = body["answer"]
    assert "Traceback" not in text
    assert "File \"" not in text
    assert not re.search(r"<[\w\.]+ object at 0x[0-9a-fA-F]+>", text)


# ── 7. current_rfq_code allows page-default Path 4 ──────────────────────


def test_current_rfq_code_enables_page_default_question(smoke):
    client, fake_llm, fake_manager = smoke
    fake_manager.set_rfq_detail("IF-0042", deadline=date(2026, 9, 1))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "", "proposed_kind": "page_default"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline?", "current_rfq_code": "IF-0042"},
    )
    body = r.json()
    assert body["path"] == "path_4"
    assert body["target_rfq_code"] == "IF-0042"
    assert "2026-09-01" in body["answer"]


# ── 8. No current_rfq_code -> clarification ─────────────────────────────


def test_page_default_without_context_routes_to_clarification(smoke):
    client, fake_llm, fake_manager = smoke
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "", "proposed_kind": "page_default"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline?"},
    )
    body = r.json()
    assert body["path"] == "path_8_3"
    assert body["target_rfq_code"] is None


# ── 9. Unknown RFQ -> Path 8.4 ──────────────────────────────────────────


def test_unknown_rfq_routes_to_path_8_4(smoke):
    client, fake_llm, fake_manager = smoke
    fake_manager.mark_not_found("IF-9999")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "IF-9999", "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-9999?"},
    )
    body = r.json()
    assert body["path"] == "path_8_4"


# ── 10. Manager unavailable -> Path 8.5 ─────────────────────────────────


def test_manager_unavailable_routes_to_path_8_5(smoke):
    client, fake_llm, fake_manager = smoke
    fake_manager.set_unreachable()
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-0001?"},
    )
    body = r.json()
    assert body["path"] == "path_8_5"


# ── 11. Planner unavailable -> Path 8.5 ─────────────────────────────────


def test_planner_unavailable_routes_non_fastintake_to_path_8_5():
    """When no Planner is wired (Slice 1 deployment without Azure),
    non-FastIntake messages route to Path 8.5 llm_unavailable."""
    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    fake_manager = FakeManagerConnector()

    def _override_controller():
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=None,  # explicit — Azure not configured
            manager=fake_manager,
        )

    app.dependency_overrides[get_v2_turn_controller] = _override_controller
    try:
        client = TestClient(app)
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "What is the deadline for IF-0001?"},
        )
        body = r.json()
        assert body["path"] == "path_8_5"
        assert body["reason_code"] == "llm_unavailable"
        # FastIntake-only deployment still answers FastIntake messages.
        r2 = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "hello"},
        )
        assert r2.json()["path"] == "path_1"
    finally:
        app.dependency_overrides.pop(get_v2_turn_controller, None)


# ── 12. Persistence failure still returns answer + null record id ───────


def test_persistence_failure_returns_answer_with_null_record_id():
    """If the DB session is None (or a failing session), the user must
    still get a complete answer — execution_record_id is just None."""
    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    fake_manager = FakeManagerConnector()
    fake_llm = FakeLlmConnector()

    def _override_controller():
        # session=None mimics persistence-unavailable.
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=Planner(llm_connector=fake_llm),
            manager=fake_manager,
            llm_connector=fake_llm,
            session=None,
        )

    app.dependency_overrides[get_v2_turn_controller] = _override_controller
    try:
        client = TestClient(app)
        # FastIntake — no LLM call, persistence skipped, answer must
        # still be the safe template.
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "hello"},
        )
        body = r.json()
        _assert_stable_contract(body)
        assert body["path"] == "path_1"
        assert body["answer"]
        assert body["execution_record_id"] is None
    finally:
        app.dependency_overrides.pop(get_v2_turn_controller, None)


# ── 13. /v1 functional smoke still passes (regression) ──────────────────


def test_v1_threads_new_still_works():
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
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

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


# ── 14. /health and /health/readiness ───────────────────────────────────


def test_health_endpoint_returns_ok():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok", "service": "rfq_copilot_ms"}


def test_readiness_endpoint_returns_passive_config_status():
    """Passive readiness: configuration presence only, no live calls.

    Whether each flag is True/False depends on the test env — this
    asserts only the *shape* and that no secrets are leaked.
    """
    client = TestClient(app)
    r = client.get("/health/readiness")
    assert r.status_code == 200
    body = r.json()
    # Shape contract.
    assert set(body.keys()) == {
        "service",
        "azure_planner_configured",
        "manager_base_url_configured",
        "manager_base_url",
        "persistence_configured",
    }
    assert body["service"] == "rfq_copilot_ms"
    # Booleans are real booleans (not truthy strings or counts).
    assert isinstance(body["azure_planner_configured"], bool)
    assert isinstance(body["manager_base_url_configured"], bool)
    assert isinstance(body["persistence_configured"], bool)
    # No secret keys leak through.
    forbidden = ("api_key", "API_KEY", "password", "secret", "token")
    serialized = str(body)
    for needle in forbidden:
        assert needle not in serialized, (
            f"Readiness response must not contain {needle!r}"
        )


# ── 15. Per-turn safe log line (Batch 9 operational diagnostic) ─────────


def test_per_turn_log_contains_only_safe_fields(smoke, caplog):
    client, fake_llm, fake_manager = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))
    with caplog.at_level(
        logging.INFO,
        logger="src.controllers.v2_turn_controller",
    ):
        client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "What is the deadline for IF-0001?"},
        )

    turn_lines = [r.message for r in caplog.records if "v2.turn" in r.message]
    assert turn_lines, (
        "Expected one info log line per turn from "
        "src.controllers.v2_turn_controller"
    )
    line = turn_lines[-1]
    # Approved fields present.
    assert "path=path_4" in line
    assert "intent=deadline" in line
    assert "target=IF-0001" in line
    assert "duration_ms=" in line
    assert "execution_record_id=" in line
    assert "status=" in line
    # Forbidden content absent.
    assert "Traceback" not in line
    assert "draft_text" not in line
    assert "api_key" not in line.lower()
    assert "secret" not in line.lower()
    # User message body must NOT be echoed.
    assert "What is the deadline" not in line


# ── 16. V2TurnResponse model contract (defense in depth) ────────────────


def test_v2_turn_response_model_has_required_fields():
    """Pydantic model contract — guards against accidental field
    rename / removal that the JSON-shape test above might miss
    if a default change happens silently."""
    fields = set(V2TurnResponse.model_fields.keys())
    assert _REQUIRED_RESPONSE_KEYS.issubset(fields)
    # extra="forbid" preserved on the model.
    assert V2TurnResponse.model_config.get("extra") == "forbid"
