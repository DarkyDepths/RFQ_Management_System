"""
File datasource — database queries for the `rfq_file` table.

Methods:
- list_by_stage(rfq_stage_id)  — SELECT WHERE deleted_at IS NULL, ordered by uploaded_at
- get_by_id(file_id)           — SELECT single file by PK (WHERE deleted_at IS NULL)
- soft_delete(file_id)         — SET deleted_at = NOW()
"""

from __future__ import annotations


from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.models.rfq_file import RFQFile


class FileDatasource:

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, file_id) -> RFQFile | None:
        return (
            self.session.query(RFQFile)
            .filter(RFQFile.id == file_id, RFQFile.deleted_at.is_(None))
            .first()
        )

    def list_by_stage(self, stage_id) -> list[RFQFile]:
        return (
            self.session.query(RFQFile)
            .filter(RFQFile.rfq_stage_id == stage_id, RFQFile.deleted_at.is_(None))
            .order_by(RFQFile.uploaded_at.desc())
            .all()
        )

    def soft_delete(self, file: RFQFile):
        file.deleted_at = datetime.now(timezone.utc)
        self.session.flush()