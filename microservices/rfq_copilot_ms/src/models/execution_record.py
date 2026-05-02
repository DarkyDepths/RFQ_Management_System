"""Pydantic DTOs for the v2 execution_records persistence layer.

Wire types between the Persist stage, the datasource, and any future
read endpoint. The ORM type ``ExecutionRecordRow`` lives in
``src/models/db.py`` (matching the /v1 convention of one db.py module
for all SQLAlchemy tables); these Pydantic models are the API surface.

Status values:

* ``"answered"`` — pipeline produced a grounded answer (Path 1 / 4) or
  a normal templated reply.
* ``"escalated"`` — a stage failed, the EscalationGate routed to
  Path 8.x, and the safe template was rendered. The user got a
  meaningful (if unhappy) reply.
* ``"failed"`` — even the safety net failed (gate / finalizer crashed
  or an unexpected exception bubbled to the orchestrator). The user
  got a generic Path 8.5 fallback. Should be rare.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ExecutionRecordStatus(StrEnum):
    """Closed enum of execution_record row statuses."""

    ANSWERED = "answered"
    ESCALATED = "escalated"
    FAILED = "failed"


class ExecutionRecordCreate(BaseModel):
    """Payload the Persist stage hands to the datasource.

    Mirrors ``ExecutionRecordRow`` shape but on the Pydantic side so
    Persist can construct safely without touching SQLAlchemy directly.
    All JSON fields are pre-serialized to JSON-safe primitives by the
    Persist stage's ``_to_jsonable`` helper.
    """

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    turn_id: str
    lane: str = "v2"
    status: ExecutionRecordStatus
    duration_ms: Optional[int] = None

    path: Optional[str] = None
    intent_topic: Optional[str] = None
    intake_source: Optional[str] = None
    reason_code: Optional[str] = None
    target_rfq_code: Optional[str] = None
    registry_version: Optional[str] = None

    user_message: str
    final_answer: Optional[str] = None

    planner_proposal_json: Optional[Any] = None
    validated_proposal_json: Optional[Any] = None
    plan_json: Optional[Any] = None
    state_json: Optional[Any] = None
    tool_invocations_json: Optional[Any] = None
    evidence_refs_json: Optional[Any] = None
    escalations_json: Optional[Any] = None
    error_json: Optional[Any] = None


class ExecutionRecordRead(BaseModel):
    """Read-side projection of ``ExecutionRecordRow``. Identical shape
    to ``ExecutionRecordCreate`` plus the row id + timestamps."""

    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: str
    turn_id: str
    lane: str
    status: ExecutionRecordStatus
    duration_ms: Optional[int] = None

    path: Optional[str] = None
    intent_topic: Optional[str] = None
    intake_source: Optional[str] = None
    reason_code: Optional[str] = None
    target_rfq_code: Optional[str] = None
    registry_version: Optional[str] = None

    user_message: str
    final_answer: Optional[str] = None

    planner_proposal_json: Optional[Any] = None
    validated_proposal_json: Optional[Any] = None
    plan_json: Optional[Any] = None
    state_json: Optional[Any] = None
    tool_invocations_json: Optional[Any] = None
    evidence_refs_json: Optional[Any] = None
    escalations_json: Optional[Any] = None
    error_json: Optional[Any] = None

    created_at: datetime
    updated_at: Optional[datetime] = None
