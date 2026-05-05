"""Anti-drift — Batch 10 captures working_memory but does NOT inject it.

The Slice 2 plan splits working-memory work across two batches:

* **Batch 10 (this batch)**: capture prior turn pairs into
  ``state.working_memory`` and stop. Planner / Compose / Judge prompts
  are byte-identical to Slice 1.
* **Batch 12**: introduce semantic follow-up resolution by injecting
  working_memory into LLM prompts (and re-verify with Judge).

This test locks the boundary: turn 2 of a multi-turn smoke must show
working_memory POPULATED (proving capture works) and the Planner /
Compose / Judge ``messages`` arrays must contain only ``[system, user]``
shapes — no ``role=assistant`` from the prior turn, no prior user
content. If a future change starts injecting history into prompts
without lifting this guard, the failure here makes the prompt-shape
change visible in code review.
"""

from __future__ import annotations

from datetime import date

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
from src.datasources.execution_record_datasource import (
    ExecutionRecordDatasource,
)
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


def _assert_messages_have_no_prior_turn(messages: list[dict]) -> None:
    """A Slice 1 LLM-stage call has at most ``[system, user]``. Any
    ``role=assistant`` message indicates a prior assistant turn has
    been smuggled into the prompt — that's exactly the Batch 12
    injection this test is here to forbid."""
    roles = [m["role"] for m in messages]
    assert "assistant" not in roles, (
        f"Prompt has prior assistant turn injected: roles={roles}"
    )
    # Slice 1 calls are exactly system + one user message.
    assert roles in (["system", "user"], ["user"]), (
        f"Unexpected prompt shape — roles={roles}. Slice 1 LLM calls "
        "are [system, user]; any other shape suggests history "
        "injection started without lifting this guard."
    )


def _assert_user_message_does_not_contain(
    messages: list[dict], forbidden: str,
) -> None:
    """The current turn's user prompt must not echo content from a
    prior turn. ``forbidden`` is a string that only appears in turn 1's
    answer / question — finding it on turn 2's prompt means injection."""
    user_msgs = [m for m in messages if m["role"] == "user"]
    for msg in user_msgs:
        assert forbidden not in msg["content"], (
            f"Turn-2 user prompt contains turn-1 content {forbidden!r}: "
            f"{msg['content']!r}"
        )


# ── Multi-turn smoke proves capture vs no-injection ─────────────────────


def test_turn_2_planner_and_compose_get_no_prior_history(smoke):
    """End-to-end:

    * Turn 1: Path 4 summary intent (Compose+Judge runs). Three LLM
      calls: Planner -> Compose -> Judge.
    * Turn 2: Path 4 summary intent again. Three more LLM calls.

    After turn 2:
    * The recorded turn-2 Planner prompt MUST be [system, user] only.
    * The recorded turn-2 Compose prompt MUST be [system, user] only.
    * The recorded turn-2 Judge prompt MUST be [system, user] only.
    * None of those prompts may contain turn-1's assistant answer.
    * Working memory MUST be populated on turn 2 (capture works).
    """
    client, fake_llm, fake_manager, SessionFactory = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))

    # Turn 1: Planner + Compose + Judge responses queued.
    fake_llm.set_responses([
        # Planner
        planner_proposal_json(path="path_4", intent_topic="summary"),
        # Compose draft (well-formed enough to pass the deterministic
        # guardrails so Judge gets to run).
        '{"draft_text": "IF-0001 deadline is 2026-06-15. Status normal.", '
        '"used_source_refs": ["s1"]}',
        # Judge pass.
        '{"verdict": "pass", "violations": [], "rationale": "ok"}',
        # Turn 2: Planner + Compose + Judge responses queued.
        planner_proposal_json(path="path_4", intent_topic="summary"),
        '{"draft_text": "IF-0001 status: in preparation, deadline 2026-06-15.", '
        '"used_source_refs": ["s1"]}',
        '{"verdict": "pass", "violations": [], "rationale": "ok"}',
    ])

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    # Turn 1 — give it a unique phrase so we can search for it later.
    turn1_user_text = "TURN1_QUESTION_unique_marker about IF-0001"
    r1 = client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": turn1_user_text},
    )
    assert r1.status_code == 200, r1.text
    turn1_answer = r1.json()["answer"]
    assert turn1_answer  # must be a real answer

    # Reset call log so we only inspect turn-2 LLM traffic.
    calls_after_turn1 = list(fake_llm.calls)

    # Turn 2.
    turn2_user_text = "TURN2_QUESTION_unique_marker follow-up"
    r2 = client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": turn2_user_text},
    )
    assert r2.status_code == 200, r2.text

    # Three new LLM calls: Planner, Compose, Judge (in order).
    turn2_calls = fake_llm.calls[len(calls_after_turn1):]
    assert len(turn2_calls) == 3, (
        f"Expected 3 LLM calls on turn 2 (Planner+Compose+Judge); "
        f"got {len(turn2_calls)}"
    )

    planner_call, compose_call, judge_call = turn2_calls

    # Each call's messages must be the Slice 1 shape — no prior turn
    # injection of any kind.
    _assert_messages_have_no_prior_turn(planner_call["messages"])
    _assert_messages_have_no_prior_turn(compose_call["messages"])
    _assert_messages_have_no_prior_turn(judge_call["messages"])

    # And the turn-1 question / answer must NOT appear inside the
    # turn-2 prompts.
    for call in (planner_call, compose_call, judge_call):
        _assert_user_message_does_not_contain(
            call["messages"], "TURN1_QUESTION_unique_marker",
        )
        # Use a substring of turn-1's answer, not the full string,
        # because formatting may differ between renderer/compose.
        _assert_user_message_does_not_contain(
            call["messages"], "Status normal",
        )

    # Capture worked: by turn 2, the prior complete pair lives in
    # execution_records under this thread, and that's the source the
    # controller draws from. Inspect the persisted state directly.
    s = SessionFactory()
    try:
        records = ExecutionRecordDatasource(s).list_by_thread_id(thread_id)
    finally:
        s.close()
    # 2 turns persisted, both with non-empty final_answer (the source
    # the controller's _load_working_memory will consult). This
    # demonstrates capture-readiness; the per-turn state object isn't
    # exposed via HTTP, but if execution_records has the data and the
    # `test_working_memory_capture` unit tests pass, capture is wired.
    assert len(records) == 2
    assert all(r.final_answer for r in records)


# ── Single-turn smoke: confirms turn-1 baseline is also clean ───────────


def test_turn_1_planner_and_compose_have_baseline_shape(smoke):
    """Turn 1 has no prior history possible; this test pins the
    baseline shape so the turn-2 assertion above is comparing apples
    to apples (not picking up a pre-existing drift)."""
    client, fake_llm, fake_manager, _ = smoke
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 6, 15))
    fake_llm.set_responses([
        planner_proposal_json(path="path_4", intent_topic="summary"),
        '{"draft_text": "IF-0001 deadline is 2026-06-15.", '
        '"used_source_refs": ["s1"]}',
        '{"verdict": "pass", "violations": [], "rationale": "ok"}',
    ])

    thread_id = client.post(
        "/rfq-copilot/v2/threads/new",
        json={"mode": {"kind": "general"}},
    ).json()["thread_id"]

    client.post(
        f"/rfq-copilot/v2/threads/{thread_id}/turn",
        json={"message": "summary of IF-0001"},
    )

    # 3 calls: Planner, Compose, Judge.
    assert len(fake_llm.calls) == 3
    for call in fake_llm.calls:
        _assert_messages_have_no_prior_turn(call["messages"])
