"""Turn datasource — reads/writes for the turns table."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.db import TurnRow


class TurnDatasource:
    def __init__(self, session: Session):
        self.session = session

    def list_for_thread(self, thread_id: str) -> list[TurnRow]:
        return (
            self.session.query(TurnRow)
            .filter(TurnRow.thread_id == thread_id)
            .order_by(TurnRow.created_at.asc())
            .all()
        )

    def append(self, thread_id: str, role: str, content: str) -> TurnRow:
        row = TurnRow(
            id=str(uuid4()),
            thread_id=thread_id,
            role=role,
            content=content,
            created_at=datetime.utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row
