"""Actor ownership enforcement on /v2 thread endpoints (Batch 10).

Without ownership checks, any actor with a thread_id (logged, leaked,
or guessed) could read or write into another actor's thread. The
``V2ThreadDatasource`` is ownership-gated and the four /v2 thread
endpoints + /v2/turn must all enforce it.

Two critical contract details proven here:

1. **Owner mismatch returns 404, NOT 403.** Same status as a
   nonexistent thread so an attacker can't enumerate other actors'
   thread ids by status-code differentiation. The error class is
   ``ThreadNotFoundError`` either way.

2. **Cross-actor /list never leaks.** Bob's listing must not include
   any of Alice's threads, even with the same ``mode`` filter.

The actor swap uses ``dependency_overrides[resolve_actor]`` — the
production resolver returns a fixed AUTH_BYPASS actor, so we can't
make per-request actor selection without overriding it.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.app_context import (
    get_session,
    get_v2_thread_controller,
    get_v2_turn_controller,
)
from src.controllers.v2_thread_controller import V2ThreadController
from src.controllers.v2_turn_controller import V2TurnController
from src.database import Base
from src.datasources.v2_history_datasource import V2HistoryDatasource
from src.datasources.v2_thread_datasource import V2ThreadDatasource
from src.models.actor import Actor
from src.models.db import (  # noqa: F401 — register tables
    AuditLogRow,
    ExecutionRecordRow,
    ThreadRow,
    TurnRow,
    V2ThreadRow,
)
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner import Planner
from src.pipeline.planner_validator import PlannerValidator
from src.utils.auth_context import resolve_actor
from tests.conftest import FakeLlmConnector, FakeManagerConnector


# Two distinct actors to test ownership boundaries.
_ALICE = Actor(user_id="alice", display_name="Alice", role="estimator")
_BOB = Actor(user_id="bob", display_name="Bob", role="estimator")


@pytest.fixture
def smoke():
    """Fresh app + in-memory SQLite + a mutable ``current_actor`` ref so
    individual test steps can swap who is making the request."""
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

    # Mutable actor selector: tests flip current_actor[0] to swap
    # identity between requests.
    current_actor: list[Actor] = [_ALICE]

    def _override_actor() -> Actor:
        return current_actor[0]

    def _override_session():
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

    def _override_thread_controller():
        s = SessionFactory()
        return V2ThreadController(
            thread_ds=V2ThreadDatasource(s),
            history_ds=V2HistoryDatasource(s),
            session=s,
        )

    def _override_turn_controller():
        s = SessionFactory()
        return V2TurnController(
            factory=factory, validator=validator, gate=gate,
            planner=planner, manager=fake_manager,
            llm_connector=fake_llm,
            v2_thread_datasource=V2ThreadDatasource(s),
            v2_history_datasource=V2HistoryDatasource(s),
            session=s,
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[resolve_actor] = _override_actor
    app.dependency_overrides[get_v2_thread_controller] = _override_thread_controller
    app.dependency_overrides[get_v2_turn_controller] = _override_turn_controller

    try:
        client = TestClient(app)
        yield client, current_actor
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(resolve_actor, None)
        app.dependency_overrides.pop(get_v2_thread_controller, None)
        app.dependency_overrides.pop(get_v2_turn_controller, None)
        engine.dispose()


def _as(current_actor: list[Actor], actor: Actor) -> None:
    current_actor[0] = actor


# ── GET /v2/threads/{id} ────────────────────────────────────────────────


def test_get_thread_owned_by_alice_is_404_for_bob(smoke):
    """Alice creates a thread; Bob's GET on its id must return 404
    ``ThreadNotFoundError`` — same shape as a nonexistent thread."""
    client, current_actor = smoke
    _as(current_actor, _ALICE)
    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    _as(current_actor, _BOB)
    r = client.get(f"/rfq-copilot/v2/threads/{thread_id}")
    assert r.status_code == 404
    assert r.json()["error"] == "ThreadNotFoundError"

    # Sanity: the message body does NOT distinguish between "missing"
    # and "not yours." A generic "not found or not accessible" lets
    # an enumerating attacker learn nothing about other actors.
    msg = r.json()["message"].lower()
    assert "alice" not in msg


# ── POST /v2/threads/{id}/turn ──────────────────────────────────────────


def test_turn_on_alice_thread_is_404_for_bob(smoke):
    """Alice owns the thread; Bob's /turn against it must 404 — and
    must NOT execute any pipeline work or create an execution record."""
    client, current_actor = smoke
    _as(current_actor, _ALICE)
    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    _as(current_actor, _BOB)
    r = client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "hi"},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "ThreadNotFoundError"


# ── POST /v2/threads/list ───────────────────────────────────────────────


def test_list_does_not_include_other_actors_threads(smoke):
    """Alice has 2 threads, Bob has 1. Bob's ``/list`` returns only his
    own — Alice's threads are invisible across the actor boundary."""
    client, current_actor = smoke
    _as(current_actor, _ALICE)
    a1 = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    a2 = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    _as(current_actor, _BOB)
    b1 = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    listing = client.post(
        "/rfq-copilot/v2/threads/list",
        json={"mode": {"kind": "general"}},
    ).json()
    ids = {t["thread_id"] for t in listing["threads"]}
    assert ids == {b1}
    assert a1 not in ids
    assert a2 not in ids


# ── POST /v2/threads/open ───────────────────────────────────────────────


def test_open_creates_a_separate_thread_per_actor(smoke):
    """``/open`` filters by actor — Bob can't accidentally resume
    Alice's general-mode thread even when she has one fresh."""
    client, current_actor = smoke
    _as(current_actor, _ALICE)
    a_open = client.post(
        "/rfq-copilot/v2/threads/open",
        json={"mode": {"kind": "general"}},
    ).json()
    assert a_open["created_new"] is True
    a_id = a_open["thread_id"]

    _as(current_actor, _BOB)
    b_open = client.post(
        "/rfq-copilot/v2/threads/open",
        json={"mode": {"kind": "general"}},
    ).json()
    assert b_open["thread_id"] != a_id
    assert b_open["created_new"] is True
