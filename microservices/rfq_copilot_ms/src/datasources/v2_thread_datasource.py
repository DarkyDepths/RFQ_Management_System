"""/v2 thread metadata datasource (Batch 10).

CRUD against ``v2_threads``. Mirrors ``ThreadDatasource`` (the /v1
sibling) with two important differences:

1. **Ownership-gated reads.** ``get_by_id`` requires ``actor_id`` and
   filters by ``owner_actor_id``. Owner mismatch returns ``None`` ---
   the caller maps this to ``ThreadNotFoundError`` (404). Same error
   class for "doesn't exist" and "not yours" so an attacker can't
   enumerate other actors' thread ids by 403/404 differentiation.

2. **NULL-safe rfq_id filter.** SQL ``column = NULL`` never matches;
   must use ``IS NULL``. We use ``rfq_id.is_(None)`` for the general-
   mode case (mirrors the /v1 datasource pattern).

No turn content lives here. Turn content stays in ``execution_records``
(see ``v2_history_datasource.py`` for reconstruction).
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.db import V2ThreadRow


class V2ThreadDatasource:
    def __init__(self, session: Session):
        self.session = session

    # ── Create ──────────────────────────────────────────────────────────

    def create(
        self,
        *,
        actor_id: str,
        mode_kind: str,
        rfq_id: str | None,
        rfq_code: str | None,
        rfq_label: str | None,
    ) -> V2ThreadRow:
        """Create a new v2 thread row. Title starts NULL --
        :meth:`set_title_if_unset` populates it on the first turn.
        """
        now = datetime.utcnow()
        row = V2ThreadRow(
            id=str(uuid4()),
            owner_actor_id=actor_id,
            mode_kind=mode_kind,
            rfq_id=rfq_id,
            rfq_code=rfq_code,
            rfq_label=rfq_label,
            title=None,
            created_at=now,
            last_activity_at=now,
        )
        self.session.add(row)
        self.session.flush()
        return row

    # ── Reads (all ownership-gated) ─────────────────────────────────────

    def get_by_id(self, thread_id: str, actor_id: str) -> V2ThreadRow | None:
        """Fetch by id, gated by owner. Returns ``None`` for missing OR
        not-owned (caller maps both to ThreadNotFoundError so the
        signal is collapsed)."""
        return (
            self.session.query(V2ThreadRow)
            .filter(V2ThreadRow.id == thread_id)
            .filter(V2ThreadRow.owner_actor_id == actor_id)
            .first()
        )

    def get_latest_by_mode(
        self,
        actor_id: str,
        mode_kind: str,
        rfq_id: str | None,
    ) -> V2ThreadRow | None:
        """Find the latest thread for ``(actor, mode, rfq_id)``.

        For general-mode threads ``rfq_id IS NULL`` (the SQL semantics --
        ``rfq_id == None`` would translate to ``column = NULL`` which
        never matches anything). We use ``is_(None)`` per the same
        pattern as the /v1 datasource.
        """
        query = (
            self.session.query(V2ThreadRow)
            .filter(V2ThreadRow.owner_actor_id == actor_id)
            .filter(V2ThreadRow.mode_kind == mode_kind)
        )
        if rfq_id is None:
            query = query.filter(V2ThreadRow.rfq_id.is_(None))
        else:
            query = query.filter(V2ThreadRow.rfq_id == rfq_id)
        return query.order_by(V2ThreadRow.last_activity_at.desc()).first()

    def list_by_actor_and_mode(
        self,
        actor_id: str,
        mode_kind: str,
        rfq_id: str | None,
    ) -> list[V2ThreadRow]:
        """List all threads for ``(actor, mode, rfq_id)``, newest first.

        Same NULL-safe rfq_id filtering as :meth:`get_latest_by_mode`.
        Stale threads are still included; callers compute is_stale at
        read time and the UI may grey them.
        """
        query = (
            self.session.query(V2ThreadRow)
            .filter(V2ThreadRow.owner_actor_id == actor_id)
            .filter(V2ThreadRow.mode_kind == mode_kind)
        )
        if rfq_id is None:
            query = query.filter(V2ThreadRow.rfq_id.is_(None))
        else:
            query = query.filter(V2ThreadRow.rfq_id == rfq_id)
        return query.order_by(V2ThreadRow.last_activity_at.desc()).all()

    # ── Mutations (all ownership-gated, idempotent / best-effort) ───────

    def touch_activity(
        self, thread_id: str, actor_id: str
    ) -> V2ThreadRow | None:
        """Update ``last_activity_at = now()``. Ownership-gated.
        Returns the updated row, or ``None`` if missing/not-owned.

        Called after every successful ``/v2/turn`` to drive the
        freshness clock. Best-effort; the controller treats
        a ``None`` return as "thread vanished mid-turn" and does
        not raise (the user already got an answer)."""
        row = self.get_by_id(thread_id, actor_id)
        if row is None:
            return None
        row.last_activity_at = datetime.utcnow()
        self.session.flush()
        return row

    def set_title_if_unset(
        self,
        thread_id: str,
        actor_id: str,
        title: str,
    ) -> V2ThreadRow | None:
        """Set the thread's title only if it's currently NULL. No-op
        otherwise. Lets us safely call this on every turn -- only the
        first turn (with a NULL title) actually writes.

        Future-proofs against manual title editing: when an edit
        endpoint ships, this will not clobber the user's title.

        Best-effort: returns ``None`` if missing/not-owned.
        """
        row = self.get_by_id(thread_id, actor_id)
        if row is None:
            return None
        if row.title is None:
            row.title = title
            self.session.flush()
        return row
