"""Access — Stage 4 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Access row).

Manager-mediated access check: the manager API is the authority on
whether the actor may read this RFQ. We don't have a separate IAM yet;
``RfqNotFound`` (404) and any future 403 from the manager mean "no
access" from the copilot's perspective.

Slice 1 / Batch 5 implementation:

* For the resolved target, call ``manager.get_rfq_detail(rfq_code, actor)``.
* On ``RfqNotFound`` -> StageError ``access_denied_explicit`` -> Path 8.4.
* On ``ManagerUnreachable`` -> StageError ``manager_unreachable`` ->
  Path 8.5 (mapped to ``source_unavailable`` reason_code by the gate).
* On success -> AccessDecision(granted=True) appended to state.

The fetched DTO is returned to the caller (orchestrator) as a
side-channel cache so the Tool Executor can avoid a redundant
``get_rfq_detail`` call when ``get_rfq_profile`` is in
``allowed_evidence_tools``. This is a Slice 1 ergonomic — Slice 5+ may
introduce a richer ``cached_evidence`` slot on ExecutionState.
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.execution_state import AccessDecision, ResolvedTarget
from src.models.manager_dto import ManagerRfqDetailDto
from src.models.path_registry import ReasonCode
from src.pipeline.errors import StageError
from src.utils.errors import ManagerUnreachable, RfqNotFound


def check_path_4_access(
    *,
    target: ResolvedTarget,
    actor: Actor,
    manager: ManagerConnector,
) -> tuple[AccessDecision, ManagerRfqDetailDto]:
    """Verify the actor may read the resolved RFQ.

    Returns a tuple of:

    * ``AccessDecision`` (granted=True) — to append to
      ``state.access_decisions``.
    * ``ManagerRfqDetailDto`` — the fetched detail, cached for the Tool
      Executor to reuse instead of a redundant manager call.

    Raises ``StageError`` on access-denied / manager-unreachable.
    """
    if target.rfq_code is None:
        # Defensive — Resolver must always set rfq_code for Slice 1.
        raise StageError(
            trigger="no_target_proposed",
            reason_code=ReasonCode("no_target_proposed"),
            source_stage="access",
            details={"reason": "ResolvedTarget has no rfq_code"},
        )

    try:
        detail = manager.get_rfq_detail(target.rfq_code, actor)
    except RfqNotFound as exc:
        raise StageError(
            trigger="access_denied_explicit",
            reason_code=ReasonCode("access_denied_explicit"),
            source_stage="access",
            details={"rfq_code": target.rfq_code, "cause": str(exc)},
        ) from exc
    except ManagerUnreachable as exc:
        raise StageError(
            trigger="manager_unreachable",
            reason_code=ReasonCode("source_unavailable"),
            source_stage="access",
            details={"rfq_code": target.rfq_code, "cause": str(exc)},
        ) from exc

    decision = AccessDecision(
        target_id=target.rfq_id,
        granted=True,
        reason="manager_ok",
        checked_at=datetime.now(timezone.utc),
    )
    return decision, detail
