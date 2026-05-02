"""Smoke — /v2 placeholder is mounted and returns 501 Not Implemented.

Per Batch 0 acceptance criteria: the /v2 placeholder route must be
reachable and return HTTP 501.

The body must clearly say the v4 pipeline is scaffolded but not
implemented yet, so a calling client can distinguish "endpoint missing"
(404) from "endpoint exists but Slice 1 hasn't wired the pipeline" (501).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import app


_V2_TURN_PATH = "/rfq-copilot/v2/threads/{thread_id}/turn"


def test_v2_route_is_registered():
    """The /v2 turn placeholder must be mounted on the FastAPI app."""
    registered = {
        (method, getattr(route, "path", ""))
        for route in app.routes
        for method in (getattr(route, "methods", None) or set())
    }
    assert ("POST", _V2_TURN_PATH) in registered, (
        f"/v2 turn placeholder not registered. Found routes: "
        f"{sorted(p for _, p in registered if 'v2' in p)}"
    )


def test_v2_placeholder_returns_501():
    client = TestClient(app)
    response = client.post(
        "/rfq-copilot/v2/threads/some-thread-id/turn",
        json={"user_message": "anything"},
    )
    assert response.status_code == 501, (
        f"/v2 placeholder returned {response.status_code}, expected 501. "
        f"Body: {response.text}"
    )


def test_v2_placeholder_body_indicates_scaffolded_state():
    client = TestClient(app)
    response = client.post(
        "/rfq-copilot/v2/threads/whatever/turn",
        json={"user_message": "x"},
    )
    body = response.json()
    assert body.get("error") == "NotImplemented"
    assert body.get("lane") == "v2"
    assert body.get("status") == "scaffolded"
    # Message must point operators at the canonical spec.
    assert "11-Architecture_Frozen_v2.md" in body.get("message", "")
