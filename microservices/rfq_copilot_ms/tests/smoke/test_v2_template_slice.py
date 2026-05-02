"""Smoke — /v2 FastIntake template slice (Batch 4).

End-to-end smoke through the running FastAPI app. Verifies the first
user-visible /v2 behavior: greetings, thanks, farewells, empty input,
and pure-punctuation nonsense return 200 with templated answers.
Operational queries still return 501 (Planner not implemented).

These tests use FastAPI's TestClient — no live server, no DB writes,
no external deps (Manager / Azure OpenAI not invoked).
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


@pytest.fixture
def client() -> TestClient:
    """TestClient with an injected V2TurnController that has planner=None.

    This guarantees no real Azure / manager calls during these smoke
    tests. Operational queries (non-FastIntake) gracefully degrade to
    Path 8.5 ``llm_unavailable`` 200 responses; FastIntake messages
    short-circuit before the planner anyway.
    """
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


# ── FastIntake hits return 200 with templated answers ────────────────────


def test_v2_greeting_returns_answered(client: TestClient):
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn", json={"message": "hello"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lane"] == "v2"
    assert body["status"] == "answered"
    assert body["answer"]  # non-empty
    assert body["thread_id"] == "abc"
    assert body["path"] == "path_1"
    assert body["intent_topic"] == "greeting"
    # Path 1 is direct (not Path 8.x), no reason_code.
    assert body["reason_code"] is None


def test_v2_thanks_returns_answered(client: TestClient):
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn", json={"message": "thanks"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert "welcome" in body["answer"].lower()
    assert body["path"] == "path_1"
    assert body["intent_topic"] == "thanks"


def test_v2_farewell_returns_answered(client: TestClient):
    r = client.post(
        "/rfq-copilot/v2/threads/xyz/turn", json={"message": "bye"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert "goodbye" in body["answer"].lower()
    assert body["path"] == "path_1"
    assert body["intent_topic"] == "farewell"


def test_v2_empty_message_returns_clarification(client: TestClient):
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn", json={"message": ""}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert body["path"] == "path_8_3"
    assert body["intent_topic"] == "empty_message"
    # Path 8.x carries reason_code for forensics
    assert body["reason_code"] == "empty_message"


def test_v2_whitespace_only_returns_clarification(client: TestClient):
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn", json={"message": "   "}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == "path_8_3"
    assert body["intent_topic"] == "empty_message"


def test_v2_nonsense_returns_safe_couldnt_understand(client: TestClient):
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn", json={"message": "???"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert body["path"] == "path_8_2"
    assert body["intent_topic"] == "out_of_scope_nonsense"
    assert body["reason_code"] == "out_of_scope_nonsense"
    assert "understand" in body["answer"].lower() or "RFQ" in body["answer"]


# ── Non-FastIntake messages: graceful Path 8.5 fallback ─────────────────
#
# Batch 4 returned 501 for non-FastIntake messages because the Planner
# was a hard stub. Batch 5 wires a real Planner — when the test's
# default DI surfaces a real Planner that fails (or no Planner is
# injected), the V2TurnController routes to Path 8.5 ``llm_unavailable``
# with a graceful 200. The detailed Path 8.5-fallback test now lives in
# test_v2_returns_501.py; here we just verify the route doesn't crash
# on operational queries when no DI override is provided (production
# default may or may not have Planner configured).


def test_v2_operational_query_does_not_5xx(client: TestClient):
    """Without a controller DI override the orchestrator either uses a
    configured Planner (real LLM call) or routes to Path 8.5
    llm_unavailable. Either way, no 5xx — the gate handles all
    failure modes."""
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "what is the deadline for IF-0001?"},
    )
    # Any 200 / 4xx is acceptable depending on Planner availability;
    # what we forbid is unrecovered 5xx.
    assert r.status_code < 500, r.text


def test_v2_recipe_request_does_not_5xx(client: TestClient):
    """Same as above — out-of-scope prose handled gracefully."""
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "write me a recipe"},
    )
    assert r.status_code < 500, r.text


# ── User-facing answer is short and free of internal labels ──────────────


@pytest.mark.parametrize(
    "msg",
    ["hello", "thanks", "bye", "", "???"],
)
def test_v2_answer_does_not_leak_internal_labels(client: TestClient, msg: str):
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn", json={"message": msg}
    )
    assert r.status_code == 200
    body = r.json()
    answer: str = body["answer"]
    # Internal architecture trivia must not appear in the user-facing
    # answer — those belong in the structured fields (path,
    # intent_topic, reason_code) for client-side debug, not the prose.
    forbidden = [
        "Path 8", "Path 1", "Path 4",
        "PATH_8", "PATH_1",
        "reason_code", "finalizer_template_key",
        "PlannerValidator", "ExecutionPlanFactory", "FactoryRejection",
    ]
    for term in forbidden:
        assert term not in answer, (
            f"answer for {msg!r} leaked internal label {term!r}: {answer!r}"
        )


# ── Echo of thread_id ────────────────────────────────────────────────────


def test_v2_response_echoes_thread_id(client: TestClient):
    """The thread_id from the URL path is echoed in the response so
    clients can correlate (no DB write happens in Batch 4)."""
    for tid in ["abc", "thread-001", "abc-def-123"]:
        r = client.post(
            f"/rfq-copilot/v2/threads/{tid}/turn",
            json={"message": "hello"},
        )
        assert r.status_code == 200
        assert r.json()["thread_id"] == tid


# ── Request body contract ────────────────────────────────────────────────


def test_v2_missing_message_field_returns_422(client: TestClient):
    """Per /v2 contract: body uses ``message`` (NOT ``user_message`` like
    /v1). Sending /v1's ``user_message`` shape returns 422."""
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"user_message": "hello"},
    )
    assert r.status_code == 422  # Pydantic validation error


def test_v2_message_field_only(client: TestClient):
    """Sanity: ``message`` is the right field name."""
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "hello"},
    )
    assert r.status_code == 200
