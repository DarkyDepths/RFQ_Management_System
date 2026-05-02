"""Smoke — /v2 Path 4 LLM Compose + Judge integration (Batch 8).

End-to-end /v2 turns where ``intent_topic`` ∈ {summary, blockers}
exercise the new Compose+Judge pipeline (instead of the deterministic
path4_renderer). Single-field intents (deadline, owner, status, etc.)
continue to use the deterministic renderer — verified with a regression
test below.

Each smoke turn queues TWO LLM responses on the FakeLlmConnector:

  1. Planner classification JSON.
  2. Compose draft JSON.
  3. (For non-skipped Judge runs) Judge verdict JSON.

The fake serves them in order — Planner runs first, then Compose, then
Judge. If a stage doesn't run (e.g. Compose short-circuits), the queued
response is simply not consumed.
"""

from __future__ import annotations

import json
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
    """Wire a fresh in-memory app with FakeLlmConnector injected as the
    LLM connector for *both* the Planner and Compose+Judge stages.

    Same FakeLlmConnector serves all three call sites — tests must
    queue responses in pipeline order: planner -> compose -> judge.
    """
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
            session=s,
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


def _planner(intent_topic: str) -> str:
    return planner_proposal_json(
        path="path_4", intent_topic=intent_topic,
        target_candidates=[{"raw_reference": "IF-0001", "proposed_kind": "rfq_code"}],
    )


def _compose(draft: str) -> str:
    return json.dumps({"draft_text": draft, "used_source_refs": ["s1"]})


def _judge_pass() -> str:
    return json.dumps({
        "verdict": "pass", "violations": [],
        "rationale": "draft is grounded",
    })


def _judge_fail(trigger: str, excerpt: str = "bad phrase") -> str:
    return json.dumps({
        "verdict": "fail",
        "violations": [{"trigger": trigger, "excerpt": excerpt}],
        "rationale": f"violation: {trigger}",
    })


# ── Happy paths — Compose + Judge ───────────────────────────────────────


def test_v2_summary_compose_judge_happy_path(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail(
        "IF-0001", name="Refinery Upgrade", client="ACME Energy",
        priority="Critical", deadline=date(2026, 8, 1),
    )
    fake_llm.set_responses([
        _planner("summary"),
        _compose("IF-0001 (Refinery Upgrade) for ACME Energy is Critical, due 2026-08-01."),
        _judge_pass(),
    ])
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Give a summary of IF-0001"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_4"
    assert body["status"] == "answered"
    assert body["intent_topic"] == "summary"
    # The user got the composed draft (not a template).
    assert "Refinery Upgrade" in body["answer"]
    assert "ACME Energy" in body["answer"]
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.status == ExecutionRecordStatus.ANSWERED
    # state_json must NOT contain the raw draft_text (Batch 8 redaction).
    assert "draft_text" not in (record.state_json or {})


def test_v2_blockers_compose_judge_happy_path(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001")
    fake_manager.set_rfq_stages("IF-0001", [
        {"name": "Cost estimation", "order": 1, "status": "Active",
         "blocker_status": "blocked", "blocker_reason_code": "missing_quotes"},
    ])
    fake_llm.set_responses([
        _planner("blockers"),
        _compose("IF-0001 is blocked at Cost estimation: missing_quotes."),
        _judge_pass(),
    ])
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Is IF-0001 blocked?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_4"
    assert body["intent_topic"] == "blockers"
    assert "blocked" in body["answer"].lower()


# ── Judge fail paths — each violation routes to its template ────────────


@pytest.mark.parametrize("trigger,reason_code,answer_snippet", [
    ("fabrication", "judge_verdict_fabrication", "ask about a specific field"),
    ("forbidden_inference", "judge_verdict_forbidden_inference", "grounded operational"),
    ("unsourced_citation", "judge_verdict_unsourced_citation", "cite that without source"),
    ("comparison_violation", "judge_verdict_comparison_violation", "one RFQ at a time"),
])
def test_v2_summary_judge_fail_routes_to_path_8_5_template(
    smoke, trigger: str, reason_code: str, answer_snippet: str,
):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", name="Refinery", client="ACME")
    # Draft is *benign-looking* (deterministic guardrails see nothing
    # wrong). Only the Judge's verdict drives the escalation here.
    benign_draft = (
        "IF-0001 (Refinery) for ACME, due 2026-08-01. "
        "The submission window is on schedule."
    )
    fake_llm.set_responses([
        _planner("summary"),
        _compose(benign_draft),
        _judge_fail(trigger),
    ])
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Summary of IF-0001"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == reason_code
    # User must see the safe template, not the rejected draft body.
    assert "Refinery" not in body["answer"]
    assert "submission window" not in body["answer"]
    assert answer_snippet.lower() in body["answer"].lower()
    # Persistence captures the escalation + judge_verdict for forensics.
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.status == ExecutionRecordStatus.ESCALATED
    assert record.path == "path_8_5"
    assert record.reason_code == reason_code
    assert len(record.escalations_json) >= 1
    assert record.escalations_json[0]["source_stage"] == "judge"
    # state_json should redact draft_text (Batch 8) — even on Judge fail
    # we never persist the unsafe draft body.
    assert "draft_text" not in (record.state_json or {})
    # judge_verdict.violations recorded for forensics.
    judge_dump = (record.state_json or {}).get("judge_verdict")
    assert judge_dump is not None
    assert judge_dump["verdict"] == "fail"
    assert len(judge_dump["violations"]) == 1


# ── Compose-time guardrail interaction (deterministic safety floor) ─────


def test_v2_compose_draft_with_forbidden_field_caught_by_guardrail(smoke):
    """Compose drafts something that mentions 'margin'. The deterministic
    forbidden_field guardrail catches it BEFORE the Judge runs (the
    safety floor is the deterministic gate, not the LLM Judge)."""
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", name="X", client="Y")
    fake_llm.set_responses([
        _planner("summary"),
        _compose("IF-0001 X for Y. Margin is roughly 12.5%."),
        # Judge response queued but should never be consumed.
        _judge_pass(),
    ])
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Summary of IF-0001"},
    )
    body = r.json()
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == "forbidden_inference_detected_deterministic"
    assert "margin" not in body["answer"].lower()
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.escalations_json[0]["source_stage"] == "guardrail"
    assert record.escalations_json[0]["details"]["guardrail"] == "forbidden_field"


# ── Compose-time LLM unavailable ────────────────────────────────────────


def test_v2_compose_llm_unreachable_routes_to_path_8_5(smoke):
    """Planner succeeds, but Compose's LLM call hits LlmUnreachable.
    The orchestrator routes to Path 8.5 llm_unavailable."""
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", name="X", client="Y")
    # Queue planner only, then mark unreachable. The next .complete()
    # (Compose's call) will raise.
    fake_llm.set_response(_planner("summary"))
    # First turn the response gets consumed by Planner; mark unreachable
    # for subsequent calls.
    # Trick: queue planner response, then arm unreachable AFTER planner
    # has consumed it. Easier: set both via responses + monkeypatch.
    # Cleanest: pre-set unreachable on a fresh sub-fake. Use:
    fake_llm._unreachable = False  # planner call OK
    # Use call counter via a patch wrapper.
    original_complete = fake_llm.complete
    state = {"calls": 0}

    def wrapped(messages, max_tokens=500):
        state["calls"] += 1
        if state["calls"] >= 2:
            from src.utils.errors import LlmUnreachable
            raise LlmUnreachable("compose call simulated down")
        return original_complete(messages, max_tokens=max_tokens)

    fake_llm.complete = wrapped  # type: ignore[method-assign]

    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Summary of IF-0001"},
    )
    body = r.json()
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == "llm_unavailable"
    record = _ds(SessionFactory).get_by_id(body["execution_record_id"])
    assert record.escalations_json[0]["source_stage"] == "compose"


# ── Single-field intent regression — deterministic still wins ───────────


def test_v2_deadline_still_uses_deterministic_renderer(smoke):
    """Single-field intent (deadline) is NOT in COMPOSE_ELIGIBLE.
    Compose+Judge are skipped; the deterministic path4_renderer runs.
    The fake LLM should only be called once (planner)."""
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(_planner("deadline"))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Deadline for IF-0001?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_4"
    assert "2026-06-15" in body["answer"]
    # Exactly one LLM call (the Planner) — Compose + Judge skipped.
    assert len(fake_llm.calls) == 1


def test_v2_owner_still_uses_deterministic_renderer(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", owner="Mohamed")
    fake_llm.set_response(_planner("owner"))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Owner of IF-0001?"},
    )
    body = r.json()
    assert body["path"] == "path_4"
    assert "Mohamed" in body["answer"]
    assert len(fake_llm.calls) == 1


# ── Fallback when no LLM connector wired ────────────────────────────────


def test_v2_summary_falls_back_to_deterministic_when_llm_connector_none():
    """When the controller is constructed without an LLM connector
    (Slice 1 deployments without Azure creds for Compose/Judge), the
    summary intent falls back to the deterministic path4_renderer."""
    fake_llm = FakeLlmConnector()
    fake_manager = FakeManagerConnector()
    fake_manager.set_rfq_detail(
        "IF-0001", name="Refinery", client="ACME",
        priority="Critical", deadline=date(2026, 8, 1),
    )
    fake_llm.set_response(_planner("summary"))

    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)
    planner = Planner(llm_connector=fake_llm)

    def _override_controller():
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=planner, manager=fake_manager,
            llm_connector=None,  # Compose/Judge disabled
        )

    app.dependency_overrides[get_v2_turn_controller] = _override_controller
    try:
        client = TestClient(app)
        r = client.post(
            "/rfq-copilot/v2/threads/t1/turn",
            json={"message": "Summary of IF-0001"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # Deterministic renderer produced this — the user still gets a
        # grounded answer; Compose just isn't consulted.
        assert body["path"] == "path_4"
        assert "Refinery" in body["answer"]
        assert "ACME" in body["answer"]
        # Only the planner call happened.
        assert len(fake_llm.calls) == 1
    finally:
        app.dependency_overrides.pop(get_v2_turn_controller, None)
