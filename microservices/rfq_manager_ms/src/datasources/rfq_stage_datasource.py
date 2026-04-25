"""
RFQ Stage datasource — database queries for the `rfq_stage` table.

Also handles rfq_note and rfq_file child tables.

Methods:
- list_by_rfq(rfq_id)                       — all stages for an RFQ, ordered
- get_by_id(rfq_id, stage_id)               — single stage with subtasks, notes, files
- update(rfq_id, stage_id, data)            — partial UPDATE (progress, captured_data, blocker, team)
- add_note(rfq_id, stage_id, note_data)     — INSERT into rfq_note
- add_file(rfq_id, stage_id, file_data)     — INSERT into rfq_file
- list_files(rfq_id, stage_id)              — SELECT files WHERE deleted_at IS NULL
- advance(rfq_id, stage_id)                 — mark current completed, start next
"""

from __future__ import annotations


from sqlalchemy.orm import Session

from src.models.rfq_stage import RFQStage
from src.models.rfq_note import RFQNote
from src.models.rfq_file import RFQFile


class RfqStageDatasource:

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: dict) -> RFQStage:
        stage = RFQStage(**data)
        self.session.add(stage)
        self.session.flush()
        self.session.refresh(stage)
        return stage

    def get_by_id(self, stage_id) -> RFQStage | None:
        return self.session.query(RFQStage).filter(RFQStage.id == stage_id).first()

    def get_first_by_rfq(self, rfq_id) -> RFQStage | None:
        return (
            self.session.query(RFQStage)
            .filter(RFQStage.rfq_id == rfq_id)
            .order_by(RFQStage.order.asc())
            .first()
        )

    def list_by_rfq(self, rfq_id) -> list[RFQStage]:
        return (
            self.session.query(RFQStage)
            .filter(RFQStage.rfq_id == rfq_id)
            .order_by(RFQStage.order.asc())
            .all()
        )

    def get_next_stage(self, rfq_id, current_order: int) -> RFQStage | None:
        """Get the stage with the next order number."""
        return (
            self.session.query(RFQStage)
            .filter(RFQStage.rfq_id == rfq_id, RFQStage.order > current_order)
            .order_by(RFQStage.order.asc())
            .first()
        )

    def update(self, stage: RFQStage, data: dict) -> RFQStage:
        for key, value in data.items():
            if hasattr(stage, key):
                setattr(stage, key, value)
        self.session.flush()
        self.session.refresh(stage)
        return stage

    # ── Notes (append-only) ───────────────────────────

    def add_note(self, data: dict) -> RFQNote:
        note = RFQNote(**data)
        self.session.add(note)
        self.session.flush()
        self.session.refresh(note)
        return note

    def get_notes(self, stage_id) -> list[RFQNote]:
        return (
            self.session.query(RFQNote)
            .filter(RFQNote.rfq_stage_id == stage_id)
            .order_by(RFQNote.created_at.desc())
            .all()
        )

    # ── Files ─────────────────────────────────────────

    def add_file(self, data: dict) -> RFQFile:
        f = RFQFile(**data)
        self.session.add(f)
        self.session.flush()
        self.session.refresh(f)
        return f

    def list_files(self, stage_id) -> list[RFQFile]:
        return (
            self.session.query(RFQFile)
            .filter(RFQFile.rfq_stage_id == stage_id, RFQFile.deleted_at.is_(None))
            .order_by(RFQFile.uploaded_at.desc())
            .all()
        )

