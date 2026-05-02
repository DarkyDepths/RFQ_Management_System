"""Smoke — /v2 still returns 501 for non-FastIntake messages.

Updated for Batch 4. Previously this file asserted /v2 ALWAYS returns
501 (Batch 0 placeholder behavior). Batch 4 wires the FastIntake →
Factory → Finalizer slice, so trivial messages (greetings, thanks,
farewells, empty, nonsense) now return 200 with templated answers.

The narrowed contract this file enforces today:

* The /v2 turn route is still registered.
* Messages that miss FastIntake patterns (e.g. operational queries,
  out-of-scope prose) still return 501 because the Planner is not
  implemented yet.
* The 501 body shape signals "PlannerNotImplemented" — distinct from
  the Batch 0 "scaffolded" placeholder shape.

The 200-path tests for FastIntake-supported messages live in
``test_v2_template_slice.py``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import app


_V2_TURN_PATH = "/rfq-copilot/v2/threads/{thread_id}/turn"


def test_v2_route_is_registered():
    """The /v2 turn route must be mounted on the FastAPI app."""
    registered = {
        (method, getattr(route, "path", ""))
        for route in app.routes
        for method in (getattr(route, "methods", None) or set())
    }
    assert ("POST", _V2_TURN_PATH) in registered, (
        f"/v2 turn route not registered. Found routes: "
        f"{sorted(p for _, p in registered if 'v2' in p)}"
    )


def test_v2_returns_501_for_non_fast_intake_message():
    """Operational query — Planner not implemented in Batch 4 → 501."""
    client = TestClient(app)
    response = client.post(
        "/rfq-copilot/v2/threads/some-thread-id/turn",
        json={"message": "what is the deadline for IF-0001"},
    )
    assert response.status_code == 501, (
        f"/v2 should return 501 for non-FastIntake messages, got "
        f"{response.status_code}. Body: {response.text}"
    )


def test_v2_501_body_indicates_planner_not_implemented():
    client = TestClient(app)
    response = client.post(
        "/rfq-copilot/v2/threads/whatever/turn",
        json={"message": "show me the blockers on IF-0001"},
    )
    body = response.json()
    assert body.get("error") == "PlannerNotImplemented"
    assert body.get("lane") == "v2"
    assert body.get("status") == "planner_not_implemented"
    # Message must point operators at the canonical spec.
    assert "11-Architecture_Frozen_v2.md" in body.get("message", "")
    # Echoes thread_id for client correlation.
    assert body.get("thread_id") == "whatever"
