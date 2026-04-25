"""
SQLAlchemy model for the `subtask` table.

Work items assigned within a specific RFQ stage.

Columns:
- id              UUID PK
- rfq_stage_id    UUID FK → rfq_stage.id
- name            VARCHAR  — subtask description
- assigned_to     VARCHAR  (nullable) — person or team
- due_date        DATE     (nullable)
- progress        INTEGER  — 0-100, default 0
- status          VARCHAR  — Open | In progress | Done
- created_at      TIMESTAMP WITH TZ
- deleted_at      TIMESTAMP WITH TZ (nullable) — soft delete
"""

import uuid

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.database import Base


class Subtask(Base):
    __tablename__ = "subtask"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Parent stage ──────────────────────────────────
    rfq_stage_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rfq_stage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Fields ────────────────────────────────────────
    name = Column(String(300), nullable=False)
    assigned_to = Column(String(100), nullable=True)
    due_date = Column(Date, nullable=True)
    progress = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="Open")  # Open | In progress | Done

    # ── Soft delete ───────────────────────────────────
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # ── Timestamps ────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
