"""/v2 turn history reconstruction (Batch 10).

`execution_records` is the source of truth for /v2 turn content. This
datasource exposes two read patterns over it:

1. :meth:`reconstruct_messages` -- LENIENT. Returns user/assistant
   messages chronologically, including user-only rows when a turn's
   ``final_answer`` is NULL (Persist mid-flight failure). The UI
   shows the partial conversation; the absent assistant turn is a
   visible gap, not a hidden one.

2. :meth:`load_complete_pairs` -- STRICT. Returns
   :class:`WorkingMemoryEntry` objects for working memory loading,
   capped at ``limit`` and ordered chronologically (oldest first --
   downstream stages will use indexes 0..N for "earlier" / "later"
   semantics in Batch 12). NULL-final_answer rows are SKIPPED. The
   asymmetry vs reconstruct_messages is deliberate: Batch 12's
   semantic resolution against an empty assistant answer would be
   meaningless or worse.

No writes -- this reads from a table written by ``persist.py``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.db import ExecutionRecordRow
from src.models.turn import MessageView
from src.models.working_memory import WorkingMemoryEntry


class V2HistoryDatasource:
    def __init__(self, session: Session):
        self.session = session

    # ── LENIENT reconstruction (UI display) ─────────────────────────────

    def reconstruct_messages(self, thread_id: str) -> list[MessageView]:
        """Return all messages for the thread, chronologically.

        Every ``execution_record`` row contributes:
        - Always: a user message (``user_message`` is NOT NULL by schema).
        - Conditionally: an assistant message if ``final_answer`` is
          non-empty.

        Message ids are synthesized from ``turn_id`` (``<turn_id>:u``
        and ``<turn_id>:a``) so the frontend can key off them. /v2
        does not surface separate per-message database ids -- the
        execution_record IS the per-turn record.
        """
        rows = (
            self.session.query(ExecutionRecordRow)
            .filter(ExecutionRecordRow.thread_id == thread_id)
            .order_by(ExecutionRecordRow.created_at.asc())
            .all()
        )
        out: list[MessageView] = []
        for row in rows:
            # User message always present (NOT NULL constraint).
            out.append(
                MessageView(
                    id=f"{row.turn_id}:u",
                    role="user",
                    content=row.user_message,
                    created_at=row.created_at,
                )
            )
            # Assistant message only when the turn completed.
            if row.final_answer:
                out.append(
                    MessageView(
                        id=f"{row.turn_id}:a",
                        role="assistant",
                        content=row.final_answer,
                        created_at=row.created_at,
                    )
                )
        return out

    # ── STRICT working-memory loading ───────────────────────────────────

    def load_complete_pairs(
        self,
        thread_id: str,
        limit: int,
    ) -> list[WorkingMemoryEntry]:
        """Return the most recent ``limit`` complete prior turn pairs,
        chronologically (oldest first).

        Skips rows where ``final_answer`` is NULL or empty -- only
        complete pairs land in working memory. ``limit`` is the
        per-path cap from ``MemoryPolicy.working_pairs``; pass 0 to
        get an empty list (general-degenerate case).

        Why oldest-first ordering: Batch 12's semantic resolution will
        index ``state.working_memory[0]`` as "earliest in the window"
        and ``[-1]`` as "most recent." Aligning with the natural
        chronological direction avoids bugs at the consumer layer.
        """
        if limit <= 0:
            return []
        # Query newest first (so we can LIMIT cheaply at the SQL layer),
        # filter out rows with a missing assistant answer, then reverse
        # to chronological order before returning.
        rows = (
            self.session.query(ExecutionRecordRow)
            .filter(ExecutionRecordRow.thread_id == thread_id)
            .filter(ExecutionRecordRow.final_answer.isnot(None))
            .filter(ExecutionRecordRow.final_answer != "")
            .order_by(ExecutionRecordRow.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        return [
            WorkingMemoryEntry(
                turn_id=row.turn_id,
                user_message=row.user_message,
                assistant_answer=row.final_answer,
                target_rfq_code=row.target_rfq_code,
                intent_topic=row.intent_topic,
                path=row.path,
                created_at=row.created_at,
            )
            for row in rows
        ]
