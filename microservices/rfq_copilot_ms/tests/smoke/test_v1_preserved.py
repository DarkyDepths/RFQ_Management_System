"""Smoke — /v1 lane is still wired AND functionally working after Batch 0.

Two layers of confidence:

1. **Structural**: every /v1 route declared in prior batches is still
   mounted on the FastAPI app under the ``/rfq-copilot/v1`` prefix, and
   ``GET /health`` returns 200.

2. **Functional**: at least one /v1 endpoint actually executes its
   controller end-to-end (request -> route -> controller -> datasource
   -> DB -> response). We use ``POST /rfq-copilot/v1/threads/new`` for
   this — it's the cheapest /v1 endpoint with real behavior (a DB write
   + an audit log entry) and has no external dependencies (no
   manager_ms, no LLM). The full /v1 turn pipeline (which DOES need
   manager_ms + Azure OpenAI) is intentionally out of scope here — its
   route registration is asserted structurally above.

If any of these fail, Batch 0 broke /v1 — STOP and fix before merging.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.app import app
from src.database import Base, get_session

# Import every ORM model so Base.metadata.create_all() sees it.
from src.models.db import AuditLogRow, ThreadRow, TurnRow  # noqa: F401


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


# ── Layer 1: structural ────────────────────────────────────────────────────

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


# ── Layer 2: functional (end-to-end on a real /v1 endpoint) ────────────────

def _isolated_session_factory():
    """Build a fresh in-memory SQLite + bootstrap schema + return a sessionmaker.

    Each functional smoke gets a clean DB so tests don't leak into each
    other (and never touch the dev ``rfq_copilot.db`` file).

    ``StaticPool`` is required for ``sqlite:///:memory:``: without it,
    each connection from the default pool gets its own private in-memory
    DB and the schema we just created becomes invisible to subsequent
    sessions opened by the FastAPI request handler. StaticPool pins all
    sessions to a single shared connection.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def test_v1_threads_new_actually_creates_a_thread():
    """End-to-end: POST /v1/threads/new -> writes ThreadRow + AuditLogRow + 200.

    This is the smallest functional smoke that proves the /v1 wiring
    (route -> auth -> controller -> datasource -> DB) is intact after
    Batch 0's deletions and additions. No external services involved.
    """
    SessionFactory = _isolated_session_factory()

    def override_get_session():
        session = SessionFactory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)
        response = client.post(
            "/rfq-copilot/v1/threads/new",
            json={"mode": {"kind": "general"}},
        )

        # Response shape
        assert response.status_code == 200, (
            f"POST /v1/threads/new returned {response.status_code}. "
            f"Body: {response.text}"
        )
        body = response.json()
        assert "thread_id" in body, f"Missing thread_id in body: {body}"
        thread_id = body["thread_id"]
        assert isinstance(thread_id, str) and thread_id, (
            f"thread_id must be a non-empty string, got: {thread_id!r}"
        )

        # Side effects: DB write + audit log
        with SessionFactory() as session:
            threads = session.query(ThreadRow).all()
            assert len(threads) == 1, (
                f"Expected exactly 1 thread row, found {len(threads)}"
            )
            assert threads[0].id == thread_id
            assert threads[0].mode_kind == "general"
            assert threads[0].rfq_id is None  # general mode

            audits = session.query(AuditLogRow).all()
            assert len(audits) >= 1, "Expected at least one audit log row"
            actions = {a.action for a in audits}
            assert "thread.new" in actions, (
                f"Expected 'thread.new' audit action, got: {actions}"
            )
    finally:
        app.dependency_overrides.clear()
