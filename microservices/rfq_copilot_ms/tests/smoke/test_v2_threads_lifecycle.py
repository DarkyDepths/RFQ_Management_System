"""End-to-end /v2 thread lifecycle smoke (Batch 10).

Exercises the complete user flow against the real FastAPI app with
in-memory SQLite + faked LLM/manager:

  POST /v2/threads/new                  -> thread_id, title=NULL
  POST /v2/threads/{id}/turn (turn 1)   -> answer; title set; activity touched
  POST /v2/threads/{id}/turn (turn 2)   -> answer; title unchanged
  POST /v2/threads/open                 -> resumes the same thread (+ messages)
  POST /v2/threads/list                 -> includes the thread + preview
  POST /v2/threads/new (same mode)      -> fresh thread, different id
  GET  /v2/threads/{id}                 -> reconstructed messages
  Stale -> open creates a fresh thread

All against the documented HTTP contracts the future PR-D frontend will
hit. The intermediate datasource/controller behaviors have their own
unit tests; this file pins the end-to-end shapes.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

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
from tests.conftest import (
    FakeLlmConnector,
    FakeManagerConnector,
    planner_proposal_json,
)


@pytest.fixture
def smoke():
    """Wire a fresh in-memory app, a real V2ThreadController and a
    V2TurnController bound to the same SQLite, with FakeLlm + FakeManager."""
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
    app.dependency_overrides[get_v2_thread_controller] = _override_thread_controller
    app.dependency_overrides[get_v2_turn_controller] = _override_turn_controller

    try:
        client = TestClient(app)
        yield client, fake_llm, fake_manager, SessionFactory
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_v2_thread_controller, None)
        app.dependency_overrides.pop(get_v2_turn_controller, None)
        engine.dispose()


# ── /v2/threads/new ─────────────────────────────────────────────────────


def test_new_thread_returns_id_with_null_title(smoke):
    client, _llm, _mgr, SessionFactory = smoke
    r = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "thread_id" in body and body["thread_id"]

    # DB row exists, title is NULL until the first turn lands.
    s = SessionFactory()
    try:
        row = s.query(V2ThreadRow).filter_by(id=body["thread_id"]).first()
        assert row is not None
        assert row.title is None
        assert row.owner_actor_id == "v1-demo-user"
    finally:
        s.close()


def test_new_threads_have_distinct_ids(smoke):
    """Two consecutive ``new`` calls in the same mode -> two threads."""
    client, _, _, _ = smoke
    a = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    b = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    assert a != b


# ── First turn sets title + touches activity ────────────────────────────


def test_first_turn_sets_title_and_touches_activity(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    create_resp = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    )
    thread_id = create_resp.json()["thread_id"]

    s = SessionFactory()
    try:
        before = s.query(V2ThreadRow).filter_by(id=thread_id).first().last_activity_at
    finally:
        s.close()

    user_message = "What is the deadline for IF-0001?"
    turn_resp = client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": user_message},
    )
    assert turn_resp.status_code == 200, turn_resp.text
    assert "2026-06-15" in turn_resp.json()["answer"]

    s = SessionFactory()
    try:
        row = s.query(V2ThreadRow).filter_by(id=thread_id).first()
        # Title set deterministically from the first user message.
        assert row.title == user_message
        # Activity touched (>= since clocks may collide on fast in-mem).
        assert row.last_activity_at >= before
    finally:
        s.close()


def test_long_first_message_is_truncated_with_ellipsis(smoke):
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    long_message = (
        "What is the deadline for IF-0001 and please tell me about "
        "the entire project lifecycle in significant detail right now"
    )
    assert len(long_message) > 60
    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": long_message},
    )

    s = SessionFactory()
    try:
        title = s.query(V2ThreadRow).filter_by(id=thread_id).first().title
    finally:
        s.close()
    # Truncated to 60 chars (post-rstrip) + ellipsis.
    assert title.endswith("…")
    assert len(title) <= 61
    assert title.startswith(long_message[:50])


def test_subsequent_turn_does_not_clobber_title(smoke):
    """Once title is set on turn 1, turn 2 must not overwrite it."""
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_responses([
        planner_proposal_json(path="path_4", intent_topic="deadline"),
        planner_proposal_json(path="path_4", intent_topic="deadline"),
    ])

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "first message wins title"},
    )
    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "second message must not change title"},
    )

    s = SessionFactory()
    try:
        title = s.query(V2ThreadRow).filter_by(id=thread_id).first().title
    finally:
        s.close()
    assert title == "first message wins title"


# ── /v2/threads/open: resume vs create ──────────────────────────────────


def test_open_resumes_same_thread_with_messages(smoke):
    """After a turn, /open returns the existing thread + reconstructed
    messages (not a brand-new id)."""
    client, fake_llm, fake_manager, _ = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "When is IF-0001 due?"},
    )

    open_resp = client.post(
        "/rfq-copilot/v2/threads/open",
        json={"mode": {"kind": "general"}},
    )
    assert open_resp.status_code == 200
    body = open_resp.json()
    assert body["thread_id"] == thread_id
    assert body["created_new"] is False
    assert body["is_stale"] is False
    # User + assistant message reconstructed.
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
    assert "2026-06-15" in body["messages"][1]["content"]


def test_open_creates_when_no_thread_exists(smoke):
    client, _, _, _ = smoke
    r = client.post(
        "/rfq-copilot/v2/threads/open",
        json={"mode": {"kind": "general"}},
    )
    body = r.json()
    assert body["thread_id"]
    assert body["created_new"] is True
    assert body["messages"] == []


def test_open_creates_fresh_when_existing_thread_is_stale(smoke):
    """A 4-day-stale general-mode thread must NOT be resumed by /open
    (general staleness threshold is 3 days). The stale thread stays
    in the DB; /open hands back a new thread id."""
    client, _, _, SessionFactory = smoke
    first_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    # Backdate the existing thread well past the staleness threshold.
    s = SessionFactory()
    try:
        s.query(V2ThreadRow).filter_by(id=first_id).update(
            {"last_activity_at": datetime.utcnow() - timedelta(days=4)}
        )
        s.commit()
    finally:
        s.close()

    second = client.post(
        "/rfq-copilot/v2/threads/open",
        json={"mode": {"kind": "general"}},
    ).json()
    assert second["thread_id"] != first_id
    assert second["created_new"] is True


# ── /v2/threads/list ────────────────────────────────────────────────────


def test_list_returns_threads_with_title_and_preview(smoke):
    client, fake_llm, fake_manager, _ = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline",
    ))

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    user_message = "What is the deadline for IF-0001?"
    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": user_message},
    )

    listing = client.post(
        "/rfq-copilot/v2/threads/list",
        json={"mode": {"kind": "general"}},
    )
    body = listing.json()
    summaries = {t["thread_id"]: t for t in body["threads"]}
    assert thread_id in summaries
    summary = summaries[thread_id]
    assert summary["title"] == user_message
    assert summary["preview"]
    assert "2026-06-15" in summary["preview"]
    assert summary["is_stale"] is False


# ── GET /v2/threads/{id} ────────────────────────────────────────────────


def test_get_thread_returns_reconstructed_messages(smoke):
    client, fake_llm, fake_manager, _ = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_responses([
        planner_proposal_json(path="path_4", intent_topic="deadline"),
        planner_proposal_json(path="path_4", intent_topic="deadline"),
    ])

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]
    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "first?"},
    )
    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "second?"},
    )

    detail = client.get(f"/rfq-copilot/v2/threads/{thread_id}").json()
    assert detail["thread_id"] == thread_id
    # Two complete turns -> 4 messages (2 user + 2 assistant), in order.
    roles = [m["role"] for m in detail["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
    assert detail["messages"][0]["content"] == "first?"
    assert detail["messages"][2]["content"] == "second?"


def test_get_unknown_thread_returns_404_thread_not_found(smoke):
    """GET on a missing thread -> 404 ThreadNotFoundError."""
    client, _, _, _ = smoke
    r = client.get(
        "/rfq-copilot/v2/threads/00000000-0000-0000-0000-000000000000"
    )
    assert r.status_code == 404
    assert r.json()["error"] == "ThreadNotFoundError"
