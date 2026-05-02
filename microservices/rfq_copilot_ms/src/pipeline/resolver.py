"""Resolver — Stage 3 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Resolver row).

Slice 1 / Batch 5 implements the minimal Path 4 resolver only:

* Explicit RFQ code from ``plan.target_candidates`` -> use it.
* ``proposed_kind == "page_default"`` AND request carries
  ``current_rfq_code`` -> use the page context.
* Empty ``target_candidates`` AND request carries ``current_rfq_code``
  -> use the page context (defensive fallback).
* Otherwise -> raise StageError trigger=``no_target_proposed`` /
  reason_code=``no_target_proposed`` -> Path 8.3 clarification.

Out of scope for Slice 1:
* Portfolio search by descriptor (Path 3 territory)
* Fuzzy name matching
* Multiple-target resolution for comparison (Path 7)
* Session-state pick (resume conversation about an unresolved target)

The Resolver does NOT call the manager. It only converts a
target_candidate string into a ResolvedTarget shell with the rfq_code
recorded — Access then verifies the target exists and is permitted via
``manager.get_rfq_detail()``.
"""

from __future__ import annotations

from uuid import uuid4

from src.models.execution_state import ResolvedTarget
from src.models.path_registry import ReasonCode
from src.pipeline.errors import StageError


def resolve_path_4_target(
    *,
    target_candidates: list,
    current_rfq_code: str | None,
) -> ResolvedTarget:
    """Resolve exactly one Path 4 target. Raises StageError on failure.

    Returns a ``ResolvedTarget`` with a synthetic ``rfq_id`` (UUID4) —
    the real UUID is confirmed by the manager in the Access stage.
    For Slice 1 we treat the rfq_code string from the planner as the
    canonical reference and let the manager resolve it.
    """
    # 1. Explicit RFQ code from planner.
    for candidate in target_candidates:
        if getattr(candidate, "proposed_kind", None) == "rfq_code":
            raw = getattr(candidate, "raw_reference", None)
            if raw:
                return ResolvedTarget(
                    rfq_id=uuid4(),
                    rfq_code=raw,
                    rfq_label=raw,
                    resolution_method="search_by_code",
                )

    # 2. page_default planner emission + page context provided.
    has_page_default = any(
        getattr(c, "proposed_kind", None) == "page_default"
        for c in target_candidates
    )
    if has_page_default and current_rfq_code:
        return ResolvedTarget(
            rfq_id=uuid4(),
            rfq_code=current_rfq_code,
            rfq_label=current_rfq_code,
            resolution_method="page_default",
        )

    # 3. Defensive fallback: planner emitted no targets but the user
    #    is on an RFQ page — use the page context.
    if not target_candidates and current_rfq_code:
        return ResolvedTarget(
            rfq_id=uuid4(),
            rfq_code=current_rfq_code,
            rfq_label=current_rfq_code,
            resolution_method="page_default",
        )

    # 4. No usable target.
    raise StageError(
        trigger="no_target_proposed",
        reason_code=ReasonCode("no_target_proposed"),
        source_stage="resolver",
        details={
            "target_candidates_count": len(target_candidates),
            "current_rfq_code_present": current_rfq_code is not None,
        },
    )
