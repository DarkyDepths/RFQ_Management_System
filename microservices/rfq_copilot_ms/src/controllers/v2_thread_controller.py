"""V2ThreadController -- thread lifecycle for the /v2 lane (Batch 10).

Mirrors the /v1 ``ThreadController.open_or_resume`` pattern but uses
``V2ThreadDatasource`` for metadata + ``V2HistoryDatasource`` for
turn-content reconstruction (read from ``execution_records``).

Hard discipline:

* Every read/write goes through the datasource which is ownership-
  gated. Owner mismatch -> ``ThreadNotFoundError`` (404).
* Freshness rules (general 3 days, rfq_bound 7 days) computed at
  read time -- no background job, no persisted "stale" flag.
* Reuses ``MessageView`` from /v1's ``src/models/turn.py``.
* No LLM calls. No manager calls. Pure DB.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.datasources.v2_history_datasource import V2HistoryDatasource
from src.datasources.v2_thread_datasource import V2ThreadDatasource
from src.models.actor import Actor
from src.models.db import V2ThreadRow
from src.models.v2_thread import (
    V2GeneralMode,
    V2ListThreadsResponse,
    V2NewThreadResponse,
    V2OpenThreadResponse,
    V2RfqBoundMode,
    V2ThreadDetailResponse,
    V2ThreadMode,
    V2ThreadSummary,
)
from src.utils.errors import ThreadNotFoundError


# ── Freshness ────────────────────────────────────────────────────────────


_STALENESS_THRESHOLDS: dict[str, timedelta] = {
    "general": timedelta(days=3),
    "rfq_bound": timedelta(days=7),
}


def _is_stale(row: V2ThreadRow) -> bool:
    """Compute stale status from ``last_activity_at`` against the per-mode
    threshold. Computed at read time; not persisted."""
    threshold = _STALENESS_THRESHOLDS.get(row.mode_kind, timedelta(days=3))
    last = row.last_activity_at
    if last.tzinfo is None:
        # SQLite returns naive datetimes; treat as UTC since that's how
        # we store them (datetime.utcnow() in the datasource).
        last = last.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last) > threshold


# ── Mode unpacking ───────────────────────────────────────────────────────


def _unpack_mode(
    mode: V2ThreadMode,
) -> tuple[str, str | None, str | None, str | None]:
    """Return (kind, rfq_id, rfq_code, rfq_label)."""
    if isinstance(mode, V2RfqBoundMode):
        return "rfq_bound", mode.rfq_id, mode.rfq_code, mode.rfq_label
    return "general", None, None, None


def _row_to_mode(row: V2ThreadRow) -> V2ThreadMode:
    if row.mode_kind == "rfq_bound":
        return V2RfqBoundMode(
            kind="rfq_bound",
            rfq_id=row.rfq_id or "",
            rfq_code=row.rfq_code,
            rfq_label=row.rfq_label,
        )
    return V2GeneralMode(kind="general")


# ── Preview helper ───────────────────────────────────────────────────────


_PREVIEW_MAX = 80


def _compute_preview(history_ds: V2HistoryDatasource, thread_id: str) -> str | None:
    """Return the most recent assistant answer truncated to
    ``_PREVIEW_MAX`` chars, or None when the thread has no completed
    turn yet. Lenient: pulls from reconstruct_messages and grabs the
    last assistant message."""
    messages = history_ds.reconstruct_messages(thread_id)
    for msg in reversed(messages):
        if msg.role == "assistant":
            text = (msg.content or "").strip()
            if not text:
                return None
            if len(text) > _PREVIEW_MAX:
                return text[:_PREVIEW_MAX].rstrip() + "…"
            return text
    return None


# ── Controller ───────────────────────────────────────────────────────────


class V2ThreadController:
    def __init__(
        self,
        thread_ds: V2ThreadDatasource,
        history_ds: V2HistoryDatasource,
        session: Session,
    ):
        self.thread_ds = thread_ds
        self.history_ds = history_ds
        self.session = session

    # ── /v2/threads/new ─────────────────────────────────────────────────

    def create_new(self, actor: Actor, mode: V2ThreadMode) -> V2NewThreadResponse:
        kind, rfq_id, rfq_code, rfq_label = _unpack_mode(mode)
        row = self.thread_ds.create(
            actor_id=actor.user_id,
            mode_kind=kind,
            rfq_id=rfq_id,
            rfq_code=rfq_code,
            rfq_label=rfq_label,
        )
        self.session.commit()
        return V2NewThreadResponse(thread_id=row.id)

    # ── /v2/threads/open ────────────────────────────────────────────────

    def open_or_resume(
        self, actor: Actor, mode: V2ThreadMode,
    ) -> V2OpenThreadResponse:
        """Find latest matching thread; resume if fresh; otherwise
        create new. Stale threads do NOT auto-archive -- they're left
        in the table for the user to find via /list, but a fresh
        thread is created for the new conversation."""
        kind, rfq_id, rfq_code, rfq_label = _unpack_mode(mode)
        latest = self.thread_ds.get_latest_by_mode(
            actor.user_id, kind, rfq_id,
        )
        created_new = False
        if latest is None or _is_stale(latest):
            row = self.thread_ds.create(
                actor_id=actor.user_id,
                mode_kind=kind,
                rfq_id=rfq_id,
                rfq_code=rfq_code,
                rfq_label=rfq_label,
            )
            created_new = True
        else:
            row = latest

        messages = self.history_ds.reconstruct_messages(row.id)
        self.session.commit()
        return V2OpenThreadResponse(
            thread_id=row.id,
            mode=_row_to_mode(row),
            messages=messages,
            is_stale=_is_stale(row),
            created_new=created_new,
        )

    # ── /v2/threads/list ────────────────────────────────────────────────

    def list_threads(
        self, actor: Actor, mode: V2ThreadMode,
    ) -> V2ListThreadsResponse:
        kind, rfq_id, _rfq_code, _rfq_label = _unpack_mode(mode)
        rows = self.thread_ds.list_by_actor_and_mode(
            actor.user_id, kind, rfq_id,
        )
        summaries = [
            V2ThreadSummary(
                thread_id=row.id,
                title=row.title,
                rfq_code=row.rfq_code,
                rfq_label=row.rfq_label,
                last_activity_at=row.last_activity_at,
                is_stale=_is_stale(row),
                preview=_compute_preview(self.history_ds, row.id),
            )
            for row in rows
        ]
        return V2ListThreadsResponse(threads=summaries)

    # ── GET /v2/threads/{id} ────────────────────────────────────────────

    def load_thread(
        self, actor: Actor, thread_id: str,
    ) -> V2ThreadDetailResponse:
        row = self.thread_ds.get_by_id(thread_id, actor.user_id)
        if row is None:
            # Missing OR not-owned: same error class to prevent
            # thread-id enumeration.
            raise ThreadNotFoundError()
        messages = self.history_ds.reconstruct_messages(row.id)
        return V2ThreadDetailResponse(
            thread_id=row.id,
            mode=_row_to_mode(row),
            messages=messages,
            is_stale=_is_stale(row),
        )
