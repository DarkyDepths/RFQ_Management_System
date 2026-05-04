"""Access — Stage 4 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Access row).

Manager-mediated access check: the manager API is the authority on
whether the actor may read this RFQ.

Identifier resolution (Batch 9.1):

* The Resolver populates ``ResolvedTarget.rfq_code`` with whatever
  reference the planner extracted — either a UUID (when the frontend
  passes ``current_rfq_code`` populated from a UUID) OR a human-
  readable code like ``IF-0001`` (when the planner extracted it from
  the user message).
* The Access stage detects which form it has via ``_is_uuid`` and
  calls the matching connector method:
    - UUID  -> ``manager.get_rfq_detail(uuid, actor)``      ``/rfqs/{uuid}``
    - code  -> ``manager.get_rfq_detail_by_code(code, actor)`` ``/rfqs/by-code/{code}``
* The manager (Batch 9.1 PR-A) ships the by-code endpoint; before
  that landed, every ``IF-XXXX`` reference 422'd at the by-id route.

Failure mapping:

* ``RfqNotFound`` (404)             -> Path 8.4 ``access_denied_explicit``
* ``RfqAccessDenied`` (403)         -> Path 8.4 ``access_denied_explicit``
                                       (actor authed but lacks permission)
* ``ManagerAuthFailed`` (401)       -> Path 8.5 ``manager_auth_failed``
                                       (deployment misconfig — must
                                       surface separately from "down")
* ``ManagerUnreachable`` (5xx/net)  -> Path 8.5 ``source_unavailable``

The fetched DTO is returned to the caller as a side-channel cache so
the Tool Executor can avoid a redundant manager call when
``get_rfq_profile`` is in ``allowed_evidence_tools``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.execution_state import AccessDecision, ResolvedTarget
from src.models.manager_dto import ManagerRfqDetailDto
from src.models.path_registry import ReasonCode
from src.pipeline.errors import StageError
from src.utils.errors import (
    ManagerAuthFailed,
    ManagerUnreachable,
    RfqAccessDenied,
    RfqNotFound,
)


def _is_uuid(value: str) -> bool:
    """Return True iff ``value`` is a syntactically valid UUID.

    Used by the access + tool-executor stages to pick between the
    by-id and by-code manager endpoints. Cheap stdlib check; no
    network call. False for empty / None / non-UUID strings like
    ``IF-0001``.
    """
    if not value or not isinstance(value, str):
        return False
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


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
    Picks the manager endpoint by inspecting ``target.rfq_code``:
    UUIDs go through ``/rfqs/{uuid}``; codes through
    ``/rfqs/by-code/{code}`` (Batch 9.1).
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
        if _is_uuid(target.rfq_code):
            detail = manager.get_rfq_detail(target.rfq_code, actor)
        else:
            detail = manager.get_rfq_detail_by_code(target.rfq_code, actor)
    except RfqNotFound as exc:
        raise StageError(
            trigger="access_denied_explicit",
            reason_code=ReasonCode("access_denied_explicit"),
            source_stage="access",
            details={"rfq_code": target.rfq_code, "cause": str(exc)},
        ) from exc
    except RfqAccessDenied as exc:
        # Manager 403 — actor authenticated but cannot read this RFQ.
        raise StageError(
            trigger="access_denied_explicit",
            reason_code=ReasonCode("access_denied_explicit"),
            source_stage="access",
            details={
                "rfq_code": target.rfq_code,
                "cause": str(exc),
                "manager_status": 403,
            },
        ) from exc
    except ManagerAuthFailed as exc:
        # Manager 401 — copilot creds/headers rejected. Distinct from
        # source-down so operators see the deployment misconfig.
        raise StageError(
            trigger="manager_auth_failed",
            reason_code=ReasonCode("manager_auth_failed"),
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
