"""Datasource for v2 execution_records — pure DB access.

Owned by ``src/pipeline/persist.py`` (write path) and any future read
endpoint. Follows the /v1 datasource convention:
``ExecutionRecordDatasource(session)`` injected via FastAPI Depends.

No business logic. No pipeline decisions. No manager / LLM calls.
Just write + read on the ``execution_records`` table.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.models.db import ExecutionRecordRow
from src.models.execution_record import ExecutionRecordCreate, ExecutionRecordRead


class ExecutionRecordDatasource:
    """Thin SQLAlchemy wrapper over the ``execution_records`` table."""

    def __init__(self, session: Session):
        self._session = session

    # ── Write ─────────────────────────────────────────────────────────────

    def create(self, payload: ExecutionRecordCreate) -> ExecutionRecordRead:
        """Insert one row, commit, return the read DTO."""
        row = ExecutionRecordRow(
            id=str(uuid.uuid4()),
            thread_id=payload.thread_id,
            turn_id=payload.turn_id,
            lane=payload.lane,
            status=payload.status.value,
            duration_ms=payload.duration_ms,
            path=payload.path,
            intent_topic=payload.intent_topic,
            intake_source=payload.intake_source,
            reason_code=payload.reason_code,
            target_rfq_code=payload.target_rfq_code,
            registry_version=payload.registry_version,
            user_message=payload.user_message,
            final_answer=payload.final_answer,
            planner_proposal_json=payload.planner_proposal_json,
            validated_proposal_json=payload.validated_proposal_json,
            plan_json=payload.plan_json,
            state_json=payload.state_json,
            tool_invocations_json=payload.tool_invocations_json,
            evidence_refs_json=payload.evidence_refs_json,
            escalations_json=payload.escalations_json,
            error_json=payload.error_json,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _row_to_read(row)

    # ── Read ──────────────────────────────────────────────────────────────

    def get_by_turn_id(self, turn_id: str) -> Optional[ExecutionRecordRead]:
        """Return the record for a turn, or None if no row exists.

        ``turn_id`` is unique per turn — at most one row should ever
        exist for a given value.
        """
        row = (
            self._session.query(ExecutionRecordRow)
            .filter(ExecutionRecordRow.turn_id == turn_id)
            .first()
        )
        return _row_to_read(row) if row is not None else None

    def get_by_id(self, record_id: str) -> Optional[ExecutionRecordRead]:
        """Return the record by its primary key, or None."""
        row = self._session.get(ExecutionRecordRow, record_id)
        return _row_to_read(row) if row is not None else None

    def list_by_thread_id(
        self, thread_id: str, limit: int = 50
    ) -> list[ExecutionRecordRead]:
        """Return execution records for a thread, newest first."""
        rows = (
            self._session.query(ExecutionRecordRow)
            .filter(ExecutionRecordRow.thread_id == thread_id)
            .order_by(ExecutionRecordRow.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_row_to_read(r) for r in rows]


def _row_to_read(row: ExecutionRecordRow) -> ExecutionRecordRead:
    """Project an ORM row into the read Pydantic DTO."""
    from src.models.execution_record import ExecutionRecordStatus

    return ExecutionRecordRead(
        id=row.id,
        thread_id=row.thread_id,
        turn_id=row.turn_id,
        lane=row.lane,
        status=ExecutionRecordStatus(row.status),
        duration_ms=row.duration_ms,
        path=row.path,
        intent_topic=row.intent_topic,
        intake_source=row.intake_source,
        reason_code=row.reason_code,
        target_rfq_code=row.target_rfq_code,
        registry_version=row.registry_version,
        user_message=row.user_message,
        final_answer=row.final_answer,
        planner_proposal_json=row.planner_proposal_json,
        validated_proposal_json=row.validated_proposal_json,
        plan_json=row.plan_json,
        state_json=row.state_json,
        tool_invocations_json=row.tool_invocations_json,
        evidence_refs_json=row.evidence_refs_json,
        escalations_json=row.escalations_json,
        error_json=row.error_json,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
