"""
SQLAlchemy model for the `rfq_note` table.

Append-only notes attached to an RFQ stage.

Columns:
- id              UUID PK
- rfq_stage_id    UUID FK → rfq_stage.id
- user_name       VARCHAR  — auto-set from auth context
- text            TEXT     — note content
- created_at      TIMESTAMP WITH TZ — auto-set server timestamp
"""

import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.database import Base


class RFQNote(Base):
    __tablename__ = "rfq_note"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Parent stage ──────────────────────────────────
    rfq_stage_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rfq_stage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Fields ────────────────────────────────────────
    user_name = Column(String(200), nullable=False)  # "Sales Eng."
    text = Column(Text, nullable=False)               # the note content

    # ── Timestamp (append-only — no updated_at needed) ─
    created_at = Column(DateTime(timezone=True), server_default=func.now())