"""
Subtask datasource — database queries for the `subtask` table.

Methods:
- create(rfq_stage_id, data)                   — INSERT new subtask
- list_by_stage(rfq_stage_id)                  — SELECT WHERE deleted_at IS NULL
- update(subtask_id, data)                     — partial UPDATE
- soft_delete(subtask_id)                      — SET deleted_at = NOW()
"""

from __future__ import annotations


from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.models.subtask import Subtask


class SubtaskDatasource:

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: dict) -> Subtask:
        subtask = Subtask(**data)
        self.session.add(subtask)
        self.session.flush()
        self.session.refresh(subtask)
        return subtask

    def get_by_id(self, subtask_id) -> Subtask | None:
        return (
            self.session.query(Subtask)
            .filter(Subtask.id == subtask_id, Subtask.deleted_at.is_(None))
            .first()
        )

    def list_by_stage(self, stage_id) -> list[Subtask]:
        return (
            self.session.query(Subtask)
            .filter(Subtask.rfq_stage_id == stage_id, Subtask.deleted_at.is_(None))
            .order_by(Subtask.created_at)
            .all()
        )

    def update(self, subtask: Subtask, data: dict) -> Subtask:
        for key, value in data.items():
            if hasattr(subtask, key):
                setattr(subtask, key, value)
        self.session.flush()
        self.session.refresh(subtask)
        return subtask

    def soft_delete(self, subtask: Subtask):
        subtask.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
