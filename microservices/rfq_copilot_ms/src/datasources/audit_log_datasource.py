"""Audit log datasource — append-only log of thread + turn events."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.db import AuditLogRow


class AuditLogDatasource:
    def __init__(self, session: Session):
        self.session = session

    def record(
        self,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        payload: dict | None = None,
    ) -> AuditLogRow:
        row = AuditLogRow(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload=payload,
            created_at=datetime.utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row
