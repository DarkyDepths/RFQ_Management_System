"""Persist — Stage 13 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §4 (execution_record schema)
and §5 (Persist row).

Serializes the ``ExecutionState`` plus turn metadata into one row in
the ``execution_records`` table. Pure sink — never reads policy, never
calls external services, never alters answer content.

Hard discipline:

* Persist is a **sink, not a decision-maker**. It records what
  happened; it does not change what happens.
* No registry config import. No manager / LLM / network calls. No
  ``TurnExecutionPlan`` construction (the plan is already on
  ``state.plan`` — Persist just serializes it).
* In production (``strict=False``) a DB write failure logs and returns
  ``None``; the user answer is unaffected. In tests (``strict=True``)
  the failure raises so the test catches it.

Safe-serialization rules:

* Pydantic models -> ``model.model_dump(mode="json")`` so dates / enums
  / UUIDs become strings.
* ``EvidencePacket.fields`` (``dict[str, object]``) and
  ``ToolInvocation.args`` (``dict``) may contain raw ``date`` /
  ``datetime`` / ``UUID`` values — recursively converted by
  ``_to_jsonable``.
* No environment variables. No raw secrets. No hidden chain-of-thought.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.datasources.execution_record_datasource import (
    ExecutionRecordDatasource,
)
from src.models.execution_record import (
    ExecutionRecordCreate,
    ExecutionRecordRead,
    ExecutionRecordStatus,
)
from src.models.execution_state import ExecutionState


logger = logging.getLogger(__name__)


def persist_execution_record(
    *,
    session: Session,
    state: ExecutionState,
    thread_id: str,
    user_message: str,
    final_answer: Optional[str],
    status: ExecutionRecordStatus,
    duration_ms: Optional[int] = None,
    error_payload: Optional[dict] = None,
    strict: bool = False,
) -> Optional[ExecutionRecordRead]:
    """Write one ``execution_records`` row from the final ``ExecutionState``.

    Returns the persisted record on success, ``None`` on failure when
    ``strict=False``. Raises in ``strict=True`` mode (used by tests).

    The controller in production calls with ``strict=False`` so a DB
    blip never breaks the user-facing answer. Persistence remains a
    forensics nice-to-have, never load-bearing for correctness.
    """
    try:
        payload = _build_payload(
            state=state,
            thread_id=thread_id,
            user_message=user_message,
            final_answer=final_answer,
            status=status,
            duration_ms=duration_ms,
            error_payload=error_payload,
        )
        ds = ExecutionRecordDatasource(session)
        return ds.create(payload)
    except Exception as exc:
        logger.warning(
            "persist_execution_record failed for turn=%s thread=%s status=%s: %s",
            getattr(state, "turn_id", "?"),
            thread_id,
            status,
            exc.__class__.__name__,
        )
        if strict:
            raise
        return None


# ── Payload assembly ──────────────────────────────────────────────────────


def _build_payload(
    *,
    state: ExecutionState,
    thread_id: str,
    user_message: str,
    final_answer: Optional[str],
    status: ExecutionRecordStatus,
    duration_ms: Optional[int],
    error_payload: Optional[dict],
) -> ExecutionRecordCreate:
    """Project state + turn metadata into the create payload."""
    plan = state.plan

    # Top-level denormalized fields for cheap queries.
    path = plan.path.value if plan.path else None
    intake_source = plan.source.value if plan.source else None
    reason_code = (
        str(plan.finalizer_reason_code)
        if plan.finalizer_reason_code is not None
        else None
    )

    target_rfq_code: Optional[str] = None
    if state.resolved_targets:
        first = state.resolved_targets[0]
        target_rfq_code = first.rfq_code

    return ExecutionRecordCreate(
        thread_id=thread_id,
        turn_id=state.turn_id,
        lane="v2",
        status=status,
        duration_ms=duration_ms,
        path=path,
        intent_topic=plan.intent_topic,
        intake_source=intake_source,
        reason_code=reason_code,
        target_rfq_code=target_rfq_code,
        registry_version=state.registry_version,
        user_message=user_message,
        final_answer=final_answer,
        planner_proposal_json=_dump_optional_pydantic(state.planner_proposal),
        validated_proposal_json=_dump_optional_pydantic(
            state.validated_planner_proposal
        ),
        plan_json=_dump_pydantic(plan),
        state_json=_dump_state(state),
        tool_invocations_json=[
            _dump_pydantic(inv) for inv in state.tool_invocations
        ],
        evidence_refs_json=_dump_evidence_refs(state),
        escalations_json=[_dump_pydantic(ev) for ev in state.escalations],
        error_json=error_payload,
    )


def _dump_pydantic(model: BaseModel) -> dict:
    """Pydantic v2 -> JSON-safe dict (dates -> ISO, enums -> values, etc.)."""
    return model.model_dump(mode="json")


def _dump_optional_pydantic(model: Optional[BaseModel]) -> Optional[dict]:
    return _dump_pydantic(model) if model is not None else None


def _dump_state(state: ExecutionState) -> dict:
    """Project a state snapshot focused on runtime outcomes (excludes
    plan + intake — those are persisted in dedicated columns).

    Uses ``model_dump(mode="json")`` and then strips the duplicated
    fields so the row stays compact.

    ``draft_text`` is also stripped (Batch 8): on success it duplicates
    ``final_answer``; on Judge failure it's the rejected-and-unsafe
    candidate that the user never saw — and we don't want to persist
    fabricated / scope-violating content even for forensics. The
    ``judge_verdict.violations[*].excerpt`` is enough forensic signal
    for "what tripped the Judge" without storing the full unsafe draft.
    """
    dumped = state.model_dump(mode="json")
    # Strip duplicates to keep the row compact (these have dedicated columns).
    for k in (
        "plan",
        "planner_proposal",
        "validated_planner_proposal",
        "tool_invocations",
        "escalations",
        "draft_text",
    ):
        dumped.pop(k, None)
    return _to_jsonable(dumped)


def _dump_evidence_refs(state: ExecutionState) -> list[dict]:
    """Per-target evidence summary: target label + source refs (NOT the
    full field values — those live in state_json/evidence_packets)."""
    out: list[dict] = []
    for packet in state.evidence_packets:
        out.append(
            {
                "target_label": packet.target_label,
                "target_id": str(packet.target_id) if packet.target_id else None,
                "field_keys": sorted(packet.fields.keys()),
                "source_refs": [
                    _to_jsonable(ref.model_dump(mode="json"))
                    for ref in packet.source_refs
                ],
            }
        )
    return out


def _to_jsonable(value: Any) -> Any:
    """Recursive JSON-safe conversion.

    Handles types Pydantic v2's ``model_dump(mode="json")`` may leave
    untouched in ``dict[str, object]`` slots:
    * ``datetime`` / ``date`` -> ISO strings
    * ``UUID`` -> str
    * ``Enum`` -> ``.value``
    * ``set`` / ``frozenset`` -> sorted list
    * Pydantic ``BaseModel`` -> ``model_dump(mode="json")``
    * Everything else -> passthrough (json.dumps will validate at write time).
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return _to_jsonable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_to_jsonable(item) for item in value)
    # Unknown type — return its string representation so JSON writes
    # don't blow up. This is a safety net; callers should pre-convert.
    return repr(value)
