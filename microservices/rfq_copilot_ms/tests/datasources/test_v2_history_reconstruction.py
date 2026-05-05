"""V2HistoryDatasource — Batch 10.

Verifies the LENIENT (reconstruct_messages, for UI) vs STRICT
(load_complete_pairs, for working_memory) read patterns over
``execution_records``.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.datasources.v2_history_datasource import V2HistoryDatasource
from src.models.db import ExecutionRecordRow
from src.models.execution_record import ExecutionRecordStatus
from src.models.working_memory import WorkingMemoryEntry


def _insert_record(
    db_session,
    *,
    thread_id: str,
    turn_id: str,
    user_message: str,
    final_answer: str | None,
    created_at: datetime,
    path: str | None = "path_4",
    intent_topic: str | None = "deadline",
    target_rfq_code: str | None = "IF-0001",
) -> ExecutionRecordRow:
    row = ExecutionRecordRow(
        id=f"rec-{turn_id}",
        thread_id=thread_id,
        turn_id=turn_id,
        lane="v2",
        status=(
            ExecutionRecordStatus.ANSWERED
            if final_answer
            else ExecutionRecordStatus.FAILED
        ),
        path=path,
        intent_topic=intent_topic,
        target_rfq_code=target_rfq_code,
        user_message=user_message,
        final_answer=final_answer,
        created_at=created_at,
    )
    db_session.add(row)
    db_session.flush()
    return row


# ── reconstruct_messages: LENIENT ───────────────────────────────────────


def test_reconstruct_empty_thread(db_session):
    ds = V2HistoryDatasource(db_session)
    assert ds.reconstruct_messages("nope") == []


def test_reconstruct_one_complete_turn(db_session):
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="T1",
        user_message="hi", final_answer="hello",
        created_at=base,
    )
    db_session.commit()
    msgs = V2HistoryDatasource(db_session).reconstruct_messages("t1")
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[0].content == "hi"
    assert msgs[1].role == "assistant"
    assert msgs[1].content == "hello"


def test_reconstruct_includes_user_only_for_mid_flight_failure(db_session):
    """A turn where Persist captured the user message but the assistant
    answer never landed (NULL final_answer) shows the user message in
    the history. UI sees the partial conversation, not a hidden gap."""
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="T1",
        user_message="ok", final_answer="fine",
        created_at=base,
    )
    _insert_record(
        db_session, thread_id="t1", turn_id="T2",
        user_message="next", final_answer=None,  # crashed
        created_at=base + timedelta(seconds=1),
    )
    db_session.commit()
    msgs = V2HistoryDatasource(db_session).reconstruct_messages("t1")
    # T1 contributes user+assistant; T2 contributes user-only.
    assert len(msgs) == 3
    assert msgs[0].role == "user" and msgs[0].content == "ok"
    assert msgs[1].role == "assistant" and msgs[1].content == "fine"
    assert msgs[2].role == "user" and msgs[2].content == "next"


def test_reconstruct_orders_chronologically(db_session):
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="LATER",
        user_message="L", final_answer="LA",
        created_at=base + timedelta(minutes=10),
    )
    _insert_record(
        db_session, thread_id="t1", turn_id="EARLIER",
        user_message="E", final_answer="EA",
        created_at=base,
    )
    db_session.commit()
    msgs = V2HistoryDatasource(db_session).reconstruct_messages("t1")
    assert msgs[0].content == "E"
    assert msgs[1].content == "EA"
    assert msgs[2].content == "L"
    assert msgs[3].content == "LA"


# ── load_complete_pairs: STRICT ─────────────────────────────────────────


def test_load_complete_pairs_skips_null_final_answer(db_session):
    """Working memory must not contain entries with empty assistant
    answers — Batch 12's semantic resolution against an empty answer
    would be meaningless or worse. Reconstruction is lenient; working
    memory is strict (the user's correction #4)."""
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="GOOD",
        user_message="g", final_answer="GA",
        created_at=base,
    )
    _insert_record(
        db_session, thread_id="t1", turn_id="HALF",
        user_message="h", final_answer=None,  # mid-flight failure
        created_at=base + timedelta(seconds=1),
    )
    _insert_record(
        db_session, thread_id="t1", turn_id="EMPTY",
        user_message="e", final_answer="",  # empty string also skipped
        created_at=base + timedelta(seconds=2),
    )
    db_session.commit()
    entries = V2HistoryDatasource(db_session).load_complete_pairs(
        thread_id="t1", limit=10,
    )
    assert len(entries) == 1
    assert entries[0].turn_id == "GOOD"
    assert entries[0].assistant_answer == "GA"


def test_load_complete_pairs_respects_limit(db_session):
    base = datetime(2026, 5, 5, 10, 0, 0)
    for i in range(8):
        _insert_record(
            db_session, thread_id="t1", turn_id=f"T{i}",
            user_message=f"u{i}", final_answer=f"a{i}",
            created_at=base + timedelta(seconds=i),
        )
    db_session.commit()
    entries = V2HistoryDatasource(db_session).load_complete_pairs(
        thread_id="t1", limit=5,
    )
    assert len(entries) == 5
    # Most recent 5; ordered chronologically (oldest of the 5 first).
    assert [e.turn_id for e in entries] == ["T3", "T4", "T5", "T6", "T7"]


def test_load_complete_pairs_zero_limit_returns_empty(db_session):
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="X",
        user_message="x", final_answer="xa",
        created_at=base,
    )
    db_session.commit()
    entries = V2HistoryDatasource(db_session).load_complete_pairs(
        thread_id="t1", limit=0,
    )
    assert entries == []


def test_load_complete_pairs_populates_all_fields(db_session):
    """All fields Batch 12 will need must be captured by Batch 10:
    turn_id, user_message, assistant_answer, target_rfq_code,
    intent_topic, path, created_at."""
    base = datetime(2026, 5, 5, 10, 0, 0)
    _insert_record(
        db_session, thread_id="t1", turn_id="T1",
        user_message="What is the deadline for IF-0001?",
        final_answer="IF-0001 deadline is 2026-05-17.",
        path="path_4",
        intent_topic="deadline",
        target_rfq_code="IF-0001",
        created_at=base,
    )
    db_session.commit()
    entries = V2HistoryDatasource(db_session).load_complete_pairs(
        thread_id="t1", limit=5,
    )
    assert len(entries) == 1
    e = entries[0]
    assert isinstance(e, WorkingMemoryEntry)
    assert e.turn_id == "T1"
    assert e.user_message == "What is the deadline for IF-0001?"
    assert e.assistant_answer == "IF-0001 deadline is 2026-05-17."
    assert e.target_rfq_code == "IF-0001"
    assert e.intent_topic == "deadline"
    assert e.path == "path_4"
    assert e.created_at == base
