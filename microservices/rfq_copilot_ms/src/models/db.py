"""SQLAlchemy ORM tables for the copilot conversation DB.

Batch 3 set: threads, turns, audit_log.
Batch 4+ adds: session_state, episodic_summaries.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class ThreadRow(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True)
    owner_actor_id = Column(String, nullable=False, index=True)
    mode_kind = Column(String, nullable=False)  # 'general' | 'rfq_bound'
    rfq_id = Column(String, nullable=True, index=True)
    rfq_label = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_activity_at = Column(DateTime, nullable=False, server_default=func.now())

    turns = relationship(
        "TurnRow",
        back_populates="thread",
        order_by="TurnRow.created_at",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_threads_owner_mode_rfq_activity",
            "owner_actor_id",
            "mode_kind",
            "rfq_id",
            "last_activity_at",
        ),
    )


class TurnRow(Base):
    __tablename__ = "turns"

    id = Column(String, primary_key=True)
    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    thread = relationship("ThreadRow", back_populates="turns")

    __table_args__ = (
        Index("ix_turns_thread_created", "thread_id", "created_at"),
    )


class AuditLogRow(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    actor_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
