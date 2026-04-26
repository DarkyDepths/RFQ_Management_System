"""Thread datasource — reads/writes for the threads table."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.db import ThreadRow


class ThreadDatasource:
    def __init__(self, session: Session):
        self.session = session

    def get_latest(
        self,
        actor_id: str,
        mode_kind: str,
        rfq_id: str | None,
    ) -> ThreadRow | None:
        query = (
            self.session.query(ThreadRow)
            .filter(ThreadRow.owner_actor_id == actor_id)
            .filter(ThreadRow.mode_kind == mode_kind)
        )
        if rfq_id is None:
            query = query.filter(ThreadRow.rfq_id.is_(None))
        else:
            query = query.filter(ThreadRow.rfq_id == rfq_id)
        return query.order_by(ThreadRow.last_activity_at.desc()).first()

    def get_by_id(self, thread_id: str) -> ThreadRow | None:
        return (
            self.session.query(ThreadRow)
            .filter(ThreadRow.id == thread_id)
            .first()
        )

    def create(
        self,
        actor_id: str,
        mode_kind: str,
        rfq_id: str | None,
        rfq_label: str | None,
    ) -> ThreadRow:
        now = datetime.utcnow()
        row = ThreadRow(
            id=str(uuid4()),
            owner_actor_id=actor_id,
            mode_kind=mode_kind,
            rfq_id=rfq_id,
            rfq_label=rfq_label,
            created_at=now,
            last_activity_at=now,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def touch_activity(self, thread: ThreadRow) -> ThreadRow:
        thread.last_activity_at = datetime.utcnow()
        self.session.flush()
        return thread
