"""Smoke — /v1 lane is still wired and reachable after Batch 0 cleanup.

We do NOT exercise the full /v1 turn pipeline here (that needs a real
DB, a live manager_ms, and Azure OpenAI credentials). We assert the
lower bar relevant to Batch 0: every /v1 route declared in the previous
batches is still mounted on the FastAPI app and ``GET /health`` still
returns 200.

If any of these fail, Batch 0 broke /v1 — STOP and fix before merging.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import app


_EXPECTED_V1_ROUTES = {
    ("POST", "/rfq-copilot/v1/threads/open"),
    ("POST", "/rfq-copilot/v1/threads/new"),
    ("POST", "/rfq-copilot/v1/threads/{thread_id}/turn"),
}


def _registered_routes(app_) -> set[tuple[str, str]]:
    """Return the set of (method, path) tuples for all registered routes."""
    out: set[tuple[str, str]] = set()
    for route in app_.routes:
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", "")
        for method in methods:
            out.add((method, path))
    return out


def test_health_endpoint_returns_200():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200, (
        f"GET /health returned {response.status_code}, expected 200. "
        f"Body: {response.text}"
    )
    body = response.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "rfq_copilot_ms"


def test_all_v1_routes_still_registered():
    registered = _registered_routes(app)
    missing = _EXPECTED_V1_ROUTES - registered
    assert not missing, (
        f"Batch 0 dropped /v1 routes: {missing}. "
        f"Spec says /v1 must be preserved exactly."
    )


def test_v1_lane_under_correct_prefix():
    """Every /v1 route lives under /rfq-copilot/v1/, never bare /threads."""
    registered = _registered_routes(app)
    bare_threads = {(m, p) for (m, p) in registered if p.startswith("/threads")}
    assert not bare_threads, (
        f"Routes are mounted at bare /threads/* without the /rfq-copilot/v1 "
        f"prefix: {bare_threads}. The /v1 prefix is part of the lane contract."
    )
