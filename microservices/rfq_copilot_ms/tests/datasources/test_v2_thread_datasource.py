"""V2ThreadDatasource — Batch 10.

Verifies the ownership-gated CRUD against ``v2_threads`` plus the
NULL-safe ``rfq_id`` filter. ThreadNotFoundError mapping is exercised
by the smoke tests; this file pins the datasource behavior in
isolation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from src.datasources.v2_thread_datasource import V2ThreadDatasource
from src.models.db import V2ThreadRow


# ── Create ──────────────────────────────────────────────────────────────


def test_create_returns_row_with_uuid_and_owner(db_session):
    ds = V2ThreadDatasource(db_session)
    row = ds.create(
        actor_id="alice",
        mode_kind="general",
        rfq_id=None,
        rfq_code=None,
        rfq_label=None,
    )
    assert row.id  # uuid generated
    UUID(row.id)  # parses
    assert row.owner_actor_id == "alice"
    assert row.mode_kind == "general"
    assert row.rfq_id is None
    assert row.title is None  # title lands on first turn, not at create
    assert row.created_at is not None
    assert row.last_activity_at is not None


# ── get_by_id (ownership-gated) ─────────────────────────────────────────


def test_get_by_id_returns_row_for_owner(db_session):
    ds = V2ThreadDatasource(db_session)
    created = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    fetched = ds.get_by_id(created.id, "alice")
    assert fetched is not None
    assert fetched.id == created.id


def test_get_by_id_returns_none_for_other_actor(db_session):
    """Owner mismatch must look identical to "doesn't exist" (return
    None). Otherwise an attacker could enumerate other actors' thread
    IDs by 403/404 differentiation."""
    ds = V2ThreadDatasource(db_session)
    created = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    assert ds.get_by_id(created.id, "bob") is None


def test_get_by_id_returns_none_for_missing(db_session):
    ds = V2ThreadDatasource(db_session)
    assert ds.get_by_id("00000000-0000-0000-0000-000000000000", "alice") is None


# ── get_latest_by_mode (NULL-safe rfq_id, the user's correction #1 spec) ─


def test_get_latest_by_mode_general_uses_is_null(db_session):
    """SQL ``rfq_id = NULL`` matches nothing; we use ``IS NULL`` for
    general-mode lookups. Without that, this test would return None
    even though a general-mode thread exists."""
    ds = V2ThreadDatasource(db_session)
    created = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    found = ds.get_latest_by_mode("alice", "general", rfq_id=None)
    assert found is not None
    assert found.id == created.id


def test_get_latest_by_mode_returns_newest_first(db_session):
    ds = V2ThreadDatasource(db_session)
    older = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    older.last_activity_at = datetime.utcnow() - timedelta(hours=1)
    db_session.flush()
    newer = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    found = ds.get_latest_by_mode("alice", "general", rfq_id=None)
    assert found is not None
    assert found.id == newer.id
    assert found.id != older.id


def test_get_latest_by_mode_filters_by_actor(db_session):
    ds = V2ThreadDatasource(db_session)
    ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    bob_thread = ds.create(
        actor_id="bob", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    found = ds.get_latest_by_mode("bob", "general", rfq_id=None)
    assert found.id == bob_thread.id


def test_get_latest_by_mode_rfq_bound(db_session):
    ds = V2ThreadDatasource(db_session)
    ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    rfq_bound = ds.create(
        actor_id="alice", mode_kind="rfq_bound",
        rfq_id="uuid-X", rfq_code="IF-0001", rfq_label="IF-0001 — X",
    )
    db_session.commit()
    found = ds.get_latest_by_mode("alice", "rfq_bound", rfq_id="uuid-X")
    assert found.id == rfq_bound.id


# ── list_by_actor_and_mode ──────────────────────────────────────────────


def test_list_filters_by_owner_only(db_session):
    ds = V2ThreadDatasource(db_session)
    ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    ds.create(
        actor_id="bob", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    alice_threads = ds.list_by_actor_and_mode("alice", "general", rfq_id=None)
    assert len(alice_threads) == 2
    assert all(t.owner_actor_id == "alice" for t in alice_threads)


# ── touch_activity (ownership-gated) ────────────────────────────────────


def test_touch_activity_updates_timestamp_for_owner(db_session):
    ds = V2ThreadDatasource(db_session)
    row = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    original = row.last_activity_at
    db_session.commit()
    # Force a measurable gap before touching, then capture the value
    # so the post-touch comparison sees the gap (touch_activity returns
    # the same ORM instance, so reading row.last_activity_at after the
    # call would see the new value, defeating the assertion).
    backdated = original - timedelta(minutes=5)
    row.last_activity_at = backdated
    db_session.flush()

    updated = ds.touch_activity(row.id, "alice")
    assert updated is not None
    assert updated.last_activity_at > backdated


def test_touch_activity_returns_none_for_other_actor(db_session):
    ds = V2ThreadDatasource(db_session)
    row = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    assert ds.touch_activity(row.id, "bob") is None


# ── set_title_if_unset (ownership-gated; idempotent) ────────────────────


def test_set_title_if_unset_writes_when_null(db_session):
    ds = V2ThreadDatasource(db_session)
    row = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    updated = ds.set_title_if_unset(row.id, "alice", "What is the deadline")
    assert updated.title == "What is the deadline"


def test_set_title_if_unset_does_not_clobber_existing(db_session):
    ds = V2ThreadDatasource(db_session)
    row = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    ds.set_title_if_unset(row.id, "alice", "first")
    db_session.commit()
    ds.set_title_if_unset(row.id, "alice", "second")
    db_session.commit()
    fetched = ds.get_by_id(row.id, "alice")
    assert fetched.title == "first"  # second was a no-op


def test_set_title_if_unset_returns_none_for_other_actor(db_session):
    ds = V2ThreadDatasource(db_session)
    row = ds.create(
        actor_id="alice", mode_kind="general",
        rfq_id=None, rfq_code=None, rfq_label=None,
    )
    db_session.commit()
    assert ds.set_title_if_unset(row.id, "bob", "title") is None
