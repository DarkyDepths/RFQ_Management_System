"""V2ThreadController — Batch 10.

Pins the controller-level behavior of the four /v2 thread-management
flows (``new`` / ``open`` / ``list`` / ``GET``). Datasource-level
ownership and NULL-safe filtering are exercised in
``tests/datasources/test_v2_thread_datasource.py``; this file covers
the higher-level decisions: open-or-resume vs always-create, freshness,
and ThreadNotFoundError mapping for unknown / not-owned ids.

No HTTP, no FastAPI test client — direct controller calls keep the
assertions tight and the failure messages legible.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.controllers.v2_thread_controller import V2ThreadController
from src.datasources.v2_history_datasource import V2HistoryDatasource
from src.datasources.v2_thread_datasource import V2ThreadDatasource
from src.models.actor import Actor
from src.models.db import ExecutionRecordRow, V2ThreadRow
from src.models.execution_record import ExecutionRecordStatus
from src.models.v2_thread import V2GeneralMode, V2RfqBoundMode
from src.utils.errors import ThreadNotFoundError


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def alice() -> Actor:
    return Actor(user_id="alice", display_name="Alice", role="estimator")


@pytest.fixture
def bob() -> Actor:
    return Actor(user_id="bob", display_name="Bob", role="estimator")


@pytest.fixture
def controller(db_session) -> V2ThreadController:
    return V2ThreadController(
        thread_ds=V2ThreadDatasource(db_session),
        history_ds=V2HistoryDatasource(db_session),
        session=db_session,
    )


# ── /v2/threads/new ─────────────────────────────────────────────────────


def test_create_new_returns_thread_id_and_persists_owner(
    controller, alice, db_session,
):
    response = controller.create_new(alice, V2GeneralMode(kind="general"))
    assert response.thread_id

    row = db_session.query(V2ThreadRow).filter_by(id=response.thread_id).first()
    assert row is not None
    assert row.owner_actor_id == "alice"
    assert row.mode_kind == "general"
    assert row.title is None  # title only lands after first turn


def test_create_new_always_creates_new_id(controller, alice):
    """Two consecutive ``new`` calls must produce two different threads
    even in the same mode — ``new`` is always create, never resume."""
    a = controller.create_new(alice, V2GeneralMode(kind="general"))
    b = controller.create_new(alice, V2GeneralMode(kind="general"))
    assert a.thread_id != b.thread_id


# ── /v2/threads/open ────────────────────────────────────────────────────


def test_open_or_resume_creates_when_no_thread_exists(controller, alice):
    response = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    assert response.thread_id
    assert response.created_new is True
    assert response.is_stale is False
    assert response.messages == []


def test_open_or_resume_returns_same_thread_when_fresh(controller, alice):
    """A fresh ``general`` thread already exists -> resume it (same id)."""
    first = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    second = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    assert first.thread_id == second.thread_id
    assert second.created_new is False


def test_open_or_resume_creates_fresh_when_stale(
    controller, alice, db_session,
):
    """General mode threshold is 3 days — a 4-day-stale thread must
    not be resumed; open creates a fresh one. The stale thread itself
    is left in the DB (the user can find it via /list)."""
    first = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    # Force the existing thread well past the general staleness window.
    row = db_session.query(V2ThreadRow).filter_by(id=first.thread_id).first()
    row.last_activity_at = datetime.utcnow() - timedelta(days=4)
    db_session.commit()

    second = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    assert second.thread_id != first.thread_id
    assert second.created_new is True


def test_open_or_resume_includes_reconstructed_messages(
    controller, alice, db_session,
):
    """When resuming, the response surfaces all execution_records for
    the thread (lenient — includes user-only mid-flight failures)."""
    first = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    base = datetime.utcnow() - timedelta(minutes=5)
    db_session.add(ExecutionRecordRow(
        id="rec-1",
        thread_id=first.thread_id,
        turn_id="T1",
        lane="v2",
        status=ExecutionRecordStatus.ANSWERED,
        user_message="hi",
        final_answer="hello",
        created_at=base,
    ))
    db_session.add(ExecutionRecordRow(
        id="rec-2",
        thread_id=first.thread_id,
        turn_id="T2",
        lane="v2",
        status=ExecutionRecordStatus.FAILED,
        user_message="and you?",
        final_answer=None,  # mid-flight failure -> user-only in messages
        created_at=base + timedelta(seconds=1),
    ))
    db_session.commit()

    second = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    # T1 contributes user+assistant; T2 contributes user-only.
    assert len(second.messages) == 3
    assert [m.role for m in second.messages] == [
        "user", "assistant", "user",
    ]


def test_open_or_resume_filters_by_actor(controller, alice, bob):
    """Two actors with their own ``general`` threads must each resume
    their own — never each other's."""
    a = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    b = controller.open_or_resume(bob, V2GeneralMode(kind="general"))
    assert a.thread_id != b.thread_id

    # Bob opens again -> his own; not alice's.
    b2 = controller.open_or_resume(bob, V2GeneralMode(kind="general"))
    assert b2.thread_id == b.thread_id
    assert b2.thread_id != a.thread_id


def test_open_or_resume_distinguishes_general_from_rfq_bound(
    controller, alice,
):
    """Same actor, different modes -> different threads."""
    g = controller.open_or_resume(alice, V2GeneralMode(kind="general"))
    r = controller.open_or_resume(
        alice,
        V2RfqBoundMode(
            kind="rfq_bound", rfq_id="uuid-1",
            rfq_code="IF-0001", rfq_label="IF-0001 — X",
        ),
    )
    assert g.thread_id != r.thread_id


# ── /v2/threads/list ────────────────────────────────────────────────────


def test_list_filters_by_actor_and_mode(controller, alice, bob, db_session):
    a1 = controller.create_new(alice, V2GeneralMode(kind="general"))
    a2 = controller.create_new(alice, V2GeneralMode(kind="general"))
    controller.create_new(bob, V2GeneralMode(kind="general"))
    controller.create_new(
        alice,
        V2RfqBoundMode(kind="rfq_bound", rfq_id="uuid-1", rfq_code="IF-1"),
    )

    listing = controller.list_threads(alice, V2GeneralMode(kind="general"))
    ids = {t.thread_id for t in listing.threads}
    assert ids == {a1.thread_id, a2.thread_id}


def test_list_marks_stale_threads(controller, alice, db_session):
    """A thread with last_activity_at older than the per-mode threshold
    surfaces with ``is_stale=True`` in the listing — but it's still
    returned (the UI may grey it; we do not hide it)."""
    fresh = controller.create_new(alice, V2GeneralMode(kind="general"))
    old = controller.create_new(alice, V2GeneralMode(kind="general"))
    db_session.query(V2ThreadRow).filter_by(id=old.thread_id).update(
        {"last_activity_at": datetime.utcnow() - timedelta(days=4)}
    )
    db_session.commit()

    summaries = {
        s.thread_id: s
        for s in controller.list_threads(
            alice, V2GeneralMode(kind="general"),
        ).threads
    }
    assert summaries[fresh.thread_id].is_stale is False
    assert summaries[old.thread_id].is_stale is True


def test_list_includes_preview_from_last_assistant_message(
    controller, alice, db_session,
):
    """Preview is the most recent assistant answer, truncated to 80
    chars. Threads with no completed turn yet have ``preview=None``."""
    long_answer = (
        "IF-0001 deadline is 2026-06-15 and it is currently in "
        "Cost estimation stage owned by Mohamed and the priority is critical."
    )
    completed = controller.create_new(alice, V2GeneralMode(kind="general"))
    empty = controller.create_new(alice, V2GeneralMode(kind="general"))
    db_session.add(ExecutionRecordRow(
        id="rec-A",
        thread_id=completed.thread_id,
        turn_id="T1",
        lane="v2",
        status=ExecutionRecordStatus.ANSWERED,
        user_message="deadline?",
        final_answer=long_answer,
        created_at=datetime.utcnow(),
    ))
    db_session.commit()

    summaries = {
        s.thread_id: s
        for s in controller.list_threads(
            alice, V2GeneralMode(kind="general"),
        ).threads
    }
    preview = summaries[completed.thread_id].preview
    assert preview is not None
    assert preview.startswith("IF-0001 deadline")
    # Truncated to <=80 chars; ellipsis appended.
    assert len(preview) <= 81  # 80 + ellipsis char
    assert preview.endswith("…")
    # The empty thread has no preview.
    assert summaries[empty.thread_id].preview is None


# ── GET /v2/threads/{id} ────────────────────────────────────────────────


def test_load_thread_returns_detail_for_owner(controller, alice):
    created = controller.create_new(alice, V2GeneralMode(kind="general"))
    detail = controller.load_thread(alice, created.thread_id)
    assert detail.thread_id == created.thread_id
    assert detail.messages == []  # no turns yet


def test_load_thread_raises_not_found_for_other_actor(
    controller, alice, bob,
):
    """Owner mismatch must raise ``ThreadNotFoundError`` (-> 404), not
    a 403. Same error class as missing thread to prevent enumeration
    of other actors' thread ids by status-code differentiation."""
    created = controller.create_new(alice, V2GeneralMode(kind="general"))
    with pytest.raises(ThreadNotFoundError):
        controller.load_thread(bob, created.thread_id)


def test_load_thread_raises_not_found_for_missing(controller, alice):
    with pytest.raises(ThreadNotFoundError):
        controller.load_thread(
            alice, "00000000-0000-0000-0000-000000000000",
        )
