"""Integration smoke — Path 4 by-code resolution end-to-end (Batch 9.1).

Locks the contract that surfaced the original gap during live app
testing (see Batch 9.1 audit P0-1):

  Planner extracts an rfq_code from the user message ("IF-0001")
                    -> Resolver puts the code in ResolvedTarget.rfq_code
                    -> Access detects non-UUID and calls
                       manager.get_rfq_detail_by_code(...)
                    -> Tool Executor likewise dispatches to the
                       by-code endpoint
                    -> Path 4 produces a grounded answer

These tests exercise the COMPLETE chain through the v2 turn route
with the FakeManagerConnector — the same fake that previously hid
the bug because it accepted codes for the by-id method. The new
fake (Batch 9.1) keys storage by UUID with a separate code -> UUID
index, so a regression here would fail loudly.

Plus a focused regression test that 401 / 403 from the manager land
in the right Path 8.x:
  401 -> Path 8.5 manager_auth_failed (deployment misconfig surface)
  403 -> Path 8.4 access_denied_explicit (actor lacks permission)
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.app_context import get_v2_turn_controller
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


# ── Happy path — by-code resolution end-to-end ──────────────────────────


def test_path_4_by_code_deadline_routes_through_by_code_endpoint(
    client_with_overrides,
):
    """The full chain: code in user message -> by-code manager call ->
    grounded Path 4 answer. Asserts the connector method, not just
    the user-visible answer, so a regression to the by-id path
    breaks here."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "IF-0001", "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "What is the deadline for IF-0001?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_4"
    assert body["target_rfq_code"] == "IF-0001"
    assert "2026-06-15" in body["answer"]

    # Connector dispatched to the by-code endpoint, NOT by-id.
    methods_called = [m for m, *_ in fake_manager.calls]
    assert "get_rfq_detail_by_code" in methods_called
    assert "get_rfq_detail" not in methods_called, (
        "Regression: code-form target should never hit the by-id endpoint "
        "(would produce a 422 against the real manager)."
    )


def test_path_4_by_uuid_still_uses_by_id_endpoint(client_with_overrides):
    """Sanity: the dispatch is shape-aware. /v1 callers + any future
    UUID-passing flow still goes through the by-id route."""
    from uuid import uuid4

    client, fake_llm, fake_manager = client_with_overrides
    rfq_uuid = uuid4()
    fake_manager.set_rfq_detail(
        "IF-0001", rfq_id=rfq_uuid, deadline=date(2026, 7, 1),
    )
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": str(rfq_uuid), "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": f"What is the deadline for {rfq_uuid}?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_4"
    assert "2026-07-01" in body["answer"]

    methods_called = [m for m, *_ in fake_manager.calls]
    assert "get_rfq_detail" in methods_called
    assert "get_rfq_detail_by_code" not in methods_called


def test_path_4_by_code_blockers_routes_through_by_code_stages(
    client_with_overrides,
):
    """Blockers intent uses get_rfq_stages (not detail). Verify the
    by-code stages endpoint is hit."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0001")
    fake_manager.set_rfq_stages("IF-0001", [
        {"name": "Cost estimation", "order": 1, "status": "Active",
         "blocker_status": "Blocked", "blocker_reason_code": "missing_quotes"},
    ])
    # Compose+Judge intents need an LLM connector wired -- this
    # smoke uses no llm_connector on the controller, so we route the
    # blockers intent through... wait, blockers IS COMPOSE_ELIGIBLE
    # under Batch 8. Without an llm_connector, the controller falls
    # back to deterministic. Either way the by-code stages call must fire.
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="blockers",
        target_candidates=[
            {"raw_reference": "IF-0001", "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Is IF-0001 blocked?"},
    )
    body = r.json()
    assert body["path"] == "path_4", r.text
    methods_called = [m for m, *_ in fake_manager.calls]
    assert "get_rfq_stages_by_code" in methods_called


# ── Resolved-blocker regression (Batch 9.1 fix P1-1) ────────────────────


def test_resolved_blocker_does_not_show_as_active(client_with_overrides):
    """The Tool Executor previously used a truthy check on
    ``stage.blocker_status``, which matched ``"Resolved"`` and
    surfaced past blockers as active. Lock the fix: only
    ``stage.blocker_status == "Blocked"`` counts as an active blocker."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0050")
    fake_manager.set_rfq_stages("IF-0050", [
        # Earlier stage HAD a blocker, now resolved.
        {"name": "Discovery", "order": 1, "status": "Done",
         "blocker_status": "Resolved",
         "blocker_reason_code": "missing_quotes"},
        # Current stage has no blocker.
        {"name": "Cost estimation", "order": 2, "status": "Active"},
    ])
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="blockers",
        target_candidates=[
            {"raw_reference": "IF-0050", "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Is IF-0050 blocked?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    answer = body["answer"].lower()
    # The user must NOT be told there is an active blocker, AND must
    # NOT see the stale reason_code from the resolved blocker.
    assert "missing_quotes" not in body["answer"], (
        "Regression: surfaced a Resolved blocker's reason_code as if active."
    )
    # The deterministic renderer's "no active blocker" wording.
    assert "don't see" in answer or "no" in answer


# ── 401 / 403 mapping regressions (Batch 9.1 audit P2-2) ────────────────


def test_manager_403_routes_to_path_8_4(client_with_overrides):
    """Manager 403 means the actor authenticated but isn't permitted
    to read this RFQ. Must land on Path 8.4 (inaccessible), not
    Path 8.5 (source down)."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0700")
    fake_manager.mark_access_denied("IF-0700")
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "IF-0700", "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Deadline for IF-0700?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_8_4"
    assert body["reason_code"] == "access_denied_explicit"


def test_manager_401_routes_to_path_8_5_with_distinct_reason(
    client_with_overrides,
):
    """Manager 401 means the copilot's auth is misconfigured at the
    deployment level. Must use a distinct reason_code from
    "source_unavailable" so operators can spot the misconfig."""
    client, fake_llm, fake_manager = client_with_overrides
    fake_manager.set_rfq_detail("IF-0800")
    fake_manager.set_auth_failed()
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
        target_candidates=[
            {"raw_reference": "IF-0800", "proposed_kind": "rfq_code"},
        ],
    ))
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "Deadline for IF-0800?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == "manager_auth_failed", (
        "Manager 401 must surface as a distinct reason_code -- not the "
        "generic source_unavailable -- so the deployment misconfig is "
        "visible in the execution_record."
    )
    # Generic safe template, no auth details leaked to user.
    assert "configuration" in body["answer"].lower() or "team" in body["answer"].lower()
