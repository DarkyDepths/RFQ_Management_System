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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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


# ── Non-FastIntake messages: 501 PlannerNotImplemented ───────────────────


def test_v2_operational_query_returns_501(client: TestClient):
    """A real operational query — Planner is not implemented in Batch 4,
    so /v2 returns 501 explicitly. Must NOT fake an unsupported answer."""
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "what is the deadline for IF-0001?"},
    )
    assert r.status_code == 501
    body = r.json()
    assert body["error"] == "PlannerNotImplemented"
    assert body["lane"] == "v2"
    assert body["status"] == "planner_not_implemented"


def test_v2_recipe_request_returns_501_not_fake_out_of_scope(
    client: TestClient,
):
    """Out-of-scope prose like 'write me a recipe' is the Planner's
    direct PATH_8_2 emission territory — not FastIntake's. Until the
    Planner ships, /v2 must return 501, NOT a fake 200 'out of scope'
    answer that pretends FastIntake handled it."""
    r = client.post(
        "/rfq-copilot/v2/threads/abc/turn",
        json={"message": "write me a recipe"},
    )
    assert r.status_code == 501
    body = r.json()
    assert body["error"] == "PlannerNotImplemented"


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
