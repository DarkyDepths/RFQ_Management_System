"""SQLAlchemy ORM tables for the copilot conversation DB.

Batch 3 set: threads, turns, audit_log.
Batch 6 adds: execution_records (v2 forensics — every /v2 turn writes
              one row; supports partial writes per §4 freeze schema).
Future: session_state, episodic_summaries.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
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


class ExecutionRecordRow(Base):
    """v2 execution forensics — one row per /v2 turn (§4 freeze schema).

    Captures every decision in a turn for post-hoc audit, debugging,
    and regression-test data harvesting. Supports partial writes —
    nullable JSON columns mean a Persist failure mid-flight still
    leaves the populated slices behind.

    Owned by ``src/pipeline/persist.py`` (writes) and
    ``src/datasources/execution_record_datasource.py`` (reads/writes).
    """

    __tablename__ = "execution_records"

    # ── Primary identity ──
    id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=False, index=True)
    turn_id = Column(String, nullable=False, index=True)
    lane = Column(String, nullable=False, default="v2")  # /v2 only for now

    # ── Lifecycle ──
    status = Column(String, nullable=False, index=True)  # answered | escalated | failed
    duration_ms = Column(Integer, nullable=True)

    # ── Top-level classification (denormalized for cheap queries) ──
    path = Column(String, nullable=True, index=True)              # path_4 / path_8_3 / etc.
    intent_topic = Column(String, nullable=True)
    intake_source = Column(String, nullable=True, index=True)     # fast_intake | planner | escalation
    reason_code = Column(String, nullable=True, index=True)       # for Path 8.x
    target_rfq_code = Column(String, nullable=True, index=True)
    registry_version = Column(String, nullable=True)

    # ── User-facing content (small) ──
    user_message = Column(Text, nullable=False)
    final_answer = Column(Text, nullable=True)

    # ── JSON forensics slices (nullable so partial writes survive) ──
    planner_proposal_json = Column(JSON, nullable=True)
    validated_proposal_json = Column(JSON, nullable=True)
    plan_json = Column(JSON, nullable=True)
    state_json = Column(JSON, nullable=True)
    tool_invocations_json = Column(JSON, nullable=True)
    evidence_refs_json = Column(JSON, nullable=True)
    escalations_json = Column(JSON, nullable=True)
    error_json = Column(JSON, nullable=True)

    # ── Timestamps ──
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_execution_records_thread_created", "thread_id", "created_at"),
        Index("ix_execution_records_path_status", "path", "status"),
    )
