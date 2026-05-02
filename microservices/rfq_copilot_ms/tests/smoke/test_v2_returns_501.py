"""Smoke — /v2 graceful Planner-unavailable behavior.

History: in Batch 4 the route returned 501 PlannerNotImplemented for
non-FastIntake messages because the Planner was a hard stub. Batch 5
wires the Planner properly — when it raises ``LlmUnreachable`` (or is
not configured at all), the V2TurnController routes to Path 8.5
``llm_unavailable`` and returns a graceful 200 with the safe template.

This file now tests that graceful-degradation path. The Batch 5 v2
template slice + path4 smoke test files cover the 200-grounded-answer
path and the FastIntake hits.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.app_context import get_v2_turn_controller
from src.controllers.v2_turn_controller import V2TurnController
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner_validator import PlannerValidator


_V2_TURN_PATH = "/rfq-copilot/v2/threads/{thread_id}/turn"


def test_v2_route_is_registered():
    """The /v2 turn route must be mounted on the FastAPI app."""
    registered = {
        (method, getattr(route, "path", ""))
        for route in app.routes
        for method in (getattr(route, "methods", None) or set())
    }
    assert ("POST", _V2_TURN_PATH) in registered


@pytest.fixture
def client_no_planner():
    """TestClient with V2TurnController set up with planner=None
    (simulates production deployment without Azure config)."""
    factory = ExecutionPlanFactory()
    validator = PlannerValidator()
    gate = EscalationGate(factory=factory)

    def _override():
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=None, manager=None,
        )

    app.dependency_overrides[get_v2_turn_controller] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_v2_turn_controller, None)


def test_non_fast_intake_message_routes_to_path_8_5_when_planner_unavailable(
    client_no_planner,
):
    """When Planner is not configured (Azure credentials missing), any
    non-FastIntake message gets a graceful Path 8.5 ``llm_unavailable``
    answer — NOT a 501. This is better UX than the Batch 4 stub."""
    r = client_no_planner.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "what is the deadline for IF-0001?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lane"] == "v2"
    assert body["status"] == "answered"
    assert body["path"] == "path_8_5"
    assert body["reason_code"] == "llm_unavailable"
    # User-facing answer mentions unavailability without leaking internals.
    assert "shortly" in body["answer"].lower() or "unavailable" in body["answer"].lower()


def test_fast_intake_messages_still_work_when_planner_unavailable(client_no_planner):
    """FastIntake doesn't need the Planner. Greetings/thanks/farewell
    still return 200 even when planner=None."""
    r = client_no_planner.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 200
    assert r.json()["path"] == "path_1"
