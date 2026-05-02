"""Evidence Check — Stage 7 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Evidence Check row).

Deterministic gate that verifies the requested fields are actually
present in the evidence packets produced by the Tool Executor. If the
manager returned the RFQ but the specific field the user asked for is
``None`` / missing / empty, we MUST NOT make up an answer — route to
Path 8.5 ``no_evidence`` and let the Finalizer say "I don't have
enough grounded information."

Slice 1 / Batch 5 implements the Path 4 cases:

* For each ``canonical_requested_field``:
  - If the field is present in any evidence packet AND non-None /
    non-empty -> pass.
  - For the special ``stages`` intent, presence of a non-empty
    ``stages`` list satisfies the field (the ``name`` / ``order`` /
    ``status`` requested fields are stage-list-derived).
  - For the ``blockers`` intent, presence of the ``active_blocker``
    key in the packet (even if its value is ``None``) is sufficient —
    "no active blocker" is a grounded answer; the renderer reads it
    as such.
  - Otherwise -> StageError ``no_evidence`` -> Path 8.5.

Hard discipline:

* Never infers missing values. If the manager DTO has
  ``current_stage_name = None``, that's not evidence — escalate.
* Never synthesizes blockers from raw stage statuses unless the
  ``blocker_status`` / ``blocker_reason_code`` fields are present.
"""

from __future__ import annotations

from src.models.execution_state import ExecutionState
from src.models.path_registry import ReasonCode
from src.pipeline.errors import StageError


# Fields that are blocker-intent specific. Special-cased because the
# Tool Executor stores them under "active_blocker" (which may be None
# legitimately — "no blocker" is a real grounded answer).
_BLOCKER_FIELDS = {"blocker_status", "blocker_reason_code"}

# Fields that are stage-list-intent specific. Special-cased because the
# Tool Executor stores them under the synthetic key "stages".
_STAGE_LIST_FIELDS = {"name", "order"}


def check_path_4(state: ExecutionState) -> None:
    """Verify Path 4 evidence is present for every requested field.

    Raises ``StageError`` ``no_evidence`` -> Path 8.5 if any requested
    field has no grounded evidence.
    """
    requested = state.plan.canonical_requested_fields
    if not requested:
        # Defensive: factory rule F3 defaults empty requested_fields to
        # allowed_fields. If we got here with no requested fields,
        # something upstream is wrong — route to no_evidence.
        raise StageError(
            trigger="evidence_empty",
            reason_code=ReasonCode("no_evidence"),
            source_stage="evidence_check",
            details={"reason": "no canonical_requested_fields on plan"},
        )

    if not state.evidence_packets:
        raise StageError(
            trigger="evidence_empty",
            reason_code=ReasonCode("no_evidence"),
            source_stage="evidence_check",
            details={"reason": "no evidence_packets produced by Tool Executor"},
        )

    # Collect every field key present across all packets, with their values.
    seen_fields: dict[str, object] = {}
    for packet in state.evidence_packets:
        for key, value in packet.fields.items():
            seen_fields[key] = value

    # Check each requested canonical field.
    blockers_check = False
    stages_check = False
    direct_check_fields: list[str] = []

    for field in requested:
        if field in _BLOCKER_FIELDS:
            blockers_check = True
        elif field in _STAGE_LIST_FIELDS or field == "status":
            # "status" is ambiguous — could be RFQ-level (allowed under
            # Path 4 status intent) or stage-level (allowed under stages
            # intent). We disambiguate by checking the top-level "status"
            # key first; if absent, fall back to the stages-list check.
            if "status" in seen_fields and seen_fields["status"] is not None:
                continue  # RFQ-level status grounded
            stages_check = True
        else:
            direct_check_fields.append(field)

    # Direct fields: must be present and non-None.
    for field in direct_check_fields:
        if field not in seen_fields or seen_fields[field] is None:
            raise StageError(
                trigger="evidence_empty",
                reason_code=ReasonCode("no_evidence"),
                source_stage="evidence_check",
                details={
                    "missing_field": field,
                    "fields_seen": sorted(seen_fields.keys()),
                },
            )
        if isinstance(seen_fields[field], str) and not seen_fields[field].strip():
            raise StageError(
                trigger="evidence_empty",
                reason_code=ReasonCode("no_evidence"),
                source_stage="evidence_check",
                details={
                    "empty_field": field,
                },
            )

    # Blockers special case: presence of "active_blocker" key (even if
    # its value is None — "no blocker found" is grounded).
    if blockers_check and "active_blocker" not in seen_fields:
        raise StageError(
            trigger="evidence_empty",
            reason_code=ReasonCode("no_evidence"),
            source_stage="evidence_check",
            details={
                "reason": "blocker fields requested but no active_blocker key in evidence",
            },
        )

    # Stages list special case: presence of "stages" key with non-empty list.
    if stages_check:
        stages_value = seen_fields.get("stages")
        if not stages_value or not isinstance(stages_value, list):
            raise StageError(
                trigger="evidence_empty",
                reason_code=ReasonCode("no_evidence"),
                source_stage="evidence_check",
                details={"reason": "stages list requested but not present in evidence"},
            )
