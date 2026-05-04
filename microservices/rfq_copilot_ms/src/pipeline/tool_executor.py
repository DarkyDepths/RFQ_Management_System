"""Tool Executor — Stage 6 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Tool Executor section)
and §8 (forbidden — the deterministic stage must never become an LLM
tool-caller).

**Deterministic invocation.** Reads ``plan.allowed_evidence_tools``
(a list set by the Path Registry, copied into the plan by the factory)
and invokes each tool with arguments derived from ``resolved_targets``
and ``plan.canonical_requested_fields``. **Never an LLM call. Never
selects which tool to run.** If a future intent requires a tool that
isn't in the registry mapping, the answer is *add the mapping*, not
let the LLM pick.

Tool ID -> manager method mapping (Slice 1 / Batch 5):

* ``ToolId("get_rfq_profile")`` -> ``ManagerConnector.get_rfq_detail``
* ``ToolId("get_rfq_stages")``  -> ``ManagerConnector.get_rfq_stages``

Hard discipline (CI-enforced — §11.3):

* No imports from any LLM SDK.
* No tool-selection logic. No conditional branching based on free-form
  intent.
* No ``ToolId`` accepted unless it appears in ``plan.allowed_evidence_tools``
  (factory pre-approved).
* Unknown tool ids in the plan -> StageError ``unknown_tool``.

Status: Batch 5 implements the Path 4 manager-grounded subset only.
RAG (Path 2), portfolio (Path 3), intelligence (Path 5) tools land in
their respective slices.
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.execution_state import (
    EvidencePacket,
    ExecutionState,
    SourceRef,
    ToolInvocation,
)
from src.models.manager_dto import (
    ManagerRfqDetailDto,
    ManagerRfqStageDto,
)
from src.models.path_registry import ReasonCode, ToolId
from src.pipeline.access import _is_uuid
from src.pipeline.errors import StageError
from src.utils.errors import (
    ManagerAuthFailed,
    ManagerUnreachable,
    RfqAccessDenied,
    RfqNotFound,
)


# Slice 1 tool ID -> manager method mapping. Adding a tool requires
# updating this dict AND adding the tool to PATH_CONFIGS.
_PATH_4_MANAGER_TOOLS: set[str] = {"get_rfq_profile", "get_rfq_stages"}


def execute_path_4(
    *,
    state: ExecutionState,
    actor: Actor,
    manager: ManagerConnector,
    cached_rfq_detail: ManagerRfqDetailDto | None = None,
) -> None:
    """Run the Path 4 tools declared in ``state.plan.allowed_evidence_tools``.

    Mutates ``state``:

    * Appends ``ToolInvocation`` records to ``state.tool_invocations``.
    * Appends ``EvidencePacket`` per target (with manager fields) to
      ``state.evidence_packets``.

    Raises ``StageError`` on tool-failure (manager unreachable, etc.)
    OR on disallowed tool id (defense in depth — factory should already
    have rejected at F1).

    ``cached_rfq_detail`` is the optional cached profile from the Access
    stage. If the plan asks for ``get_rfq_profile`` and a cache is
    present, we skip the redundant manager call.
    """
    if not state.resolved_targets:
        raise StageError(
            trigger="no_target_proposed",
            reason_code=ReasonCode("no_target_proposed"),
            source_stage="tool_executor",
            details={"reason": "no resolved_targets to execute against"},
        )

    target = state.resolved_targets[0]  # Path 4: exactly one target

    if target.rfq_code is None:
        raise StageError(
            trigger="no_target_proposed",
            reason_code=ReasonCode("no_target_proposed"),
            source_stage="tool_executor",
            details={"reason": "resolved target missing rfq_code"},
        )

    fields_for_packet: dict[str, object] = {}
    source_refs: list[SourceRef] = []

    for tool_id in state.plan.allowed_evidence_tools:
        if str(tool_id) not in _PATH_4_MANAGER_TOOLS:
            # Plan declared a tool the executor doesn't know about.
            # Should never happen — registry config + factory copy
            # path should keep these in sync. Fail loudly.
            raise StageError(
                trigger="unknown_tool",
                reason_code=ReasonCode("source_unavailable"),
                source_stage="tool_executor",
                details={
                    "tool_id": str(tool_id),
                    "known_tools": sorted(_PATH_4_MANAGER_TOOLS),
                },
            )

        if str(tool_id) == "get_rfq_profile":
            _execute_get_rfq_profile(
                state=state,
                target=target,
                actor=actor,
                manager=manager,
                cached_rfq_detail=cached_rfq_detail,
                fields_for_packet=fields_for_packet,
                source_refs=source_refs,
            )
        elif str(tool_id) == "get_rfq_stages":
            _execute_get_rfq_stages(
                state=state,
                target=target,
                actor=actor,
                manager=manager,
                fields_for_packet=fields_for_packet,
                source_refs=source_refs,
            )

    # Build the per-target evidence packet from accumulated fields.
    if fields_for_packet:
        state.evidence_packets.append(
            EvidencePacket(
                target_id=target.rfq_id,
                target_label=target.rfq_label,
                fields=fields_for_packet,
                source_refs=source_refs,
            )
        )


def _execute_get_rfq_profile(
    *,
    state: ExecutionState,
    target,
    actor: Actor,
    manager: ManagerConnector,
    cached_rfq_detail: ManagerRfqDetailDto | None,
    fields_for_packet: dict[str, object],
    source_refs: list[SourceRef],
) -> None:
    """Call manager.get_rfq_detail (or use the Access cache) and merge
    plan-allowed fields into the packet."""
    started = datetime.now(timezone.utc)

    if cached_rfq_detail is not None:
        detail = cached_rfq_detail
        latency_ms = 0  # cached — no manager call this turn
        status = "ok"
    else:
        try:
            # Dispatch by identifier shape (Batch 9.1) — same logic as
            # access.py so /v1 (UUID-passing) and /v2 (code-passing)
            # both reach the right manager endpoint.
            if _is_uuid(target.rfq_code):
                detail = manager.get_rfq_detail(target.rfq_code, actor)
            else:
                detail = manager.get_rfq_detail_by_code(
                    target.rfq_code, actor
                )
            latency_ms = max(
                1,
                int(
                    (datetime.now(timezone.utc) - started).total_seconds() * 1000
                ),
            )
            status = "ok"
        except RfqNotFound as exc:
            # Mid-pipeline 404 is unusual — Access already verified.
            # Defensive: route to 8.4.
            raise StageError(
                trigger="access_denied_explicit",
                reason_code=ReasonCode("access_denied_explicit"),
                source_stage="tool_executor",
                details={"tool_name": "get_rfq_profile", "cause": str(exc)},
            ) from exc
        except RfqAccessDenied as exc:
            raise StageError(
                trigger="access_denied_explicit",
                reason_code=ReasonCode("access_denied_explicit"),
                source_stage="tool_executor",
                details={
                    "tool_name": "get_rfq_profile",
                    "cause": str(exc),
                    "manager_status": 403,
                },
            ) from exc
        except ManagerAuthFailed as exc:
            raise StageError(
                trigger="manager_auth_failed",
                reason_code=ReasonCode("manager_auth_failed"),
                source_stage="tool_executor",
                details={"tool_name": "get_rfq_profile", "cause": str(exc)},
            ) from exc
        except ManagerUnreachable as exc:
            raise StageError(
                trigger="manager_unreachable",
                reason_code=ReasonCode("source_unavailable"),
                source_stage="tool_executor",
                details={"tool_name": "get_rfq_profile", "cause": str(exc)},
            ) from exc

    state.tool_invocations.append(
        ToolInvocation(
            tool_name=ToolId("get_rfq_profile"),
            args={"rfq_code": target.rfq_code},
            result_summary=f"detail for {target.rfq_code}",
            latency_ms=latency_ms,
            status=status,
        )
    )

    # Project allowed fields from the DTO into the packet.
    detail_dict = detail.model_dump()
    for canonical_field in state.plan.canonical_requested_fields:
        if canonical_field in detail_dict:
            value = detail_dict[canonical_field]
            if value is not None:
                fields_for_packet[canonical_field] = value

    source_refs.append(
        SourceRef(
            source_type="manager",
            source_id=f"get_rfq_profile:{target.rfq_code}",
            fetched_at=started,
        )
    )


def _execute_get_rfq_stages(
    *,
    state: ExecutionState,
    target,
    actor: Actor,
    manager: ManagerConnector,
    fields_for_packet: dict[str, object],
    source_refs: list[SourceRef],
) -> None:
    """Call manager.get_rfq_stages and merge stage list / blocker info
    into the packet, projecting only plan-allowed fields."""
    started = datetime.now(timezone.utc)
    try:
        # Dispatch by identifier shape (Batch 9.1) — see _execute_get_rfq_profile.
        if _is_uuid(target.rfq_code):
            stages = manager.get_rfq_stages(target.rfq_code, actor)
        else:
            stages = manager.get_rfq_stages_by_code(target.rfq_code, actor)
        latency_ms = max(
            1,
            int(
                (datetime.now(timezone.utc) - started).total_seconds() * 1000
            ),
        )
        status = "ok"
    except RfqNotFound as exc:
        raise StageError(
            trigger="access_denied_explicit",
            reason_code=ReasonCode("access_denied_explicit"),
            source_stage="tool_executor",
            details={"tool_name": "get_rfq_stages", "cause": str(exc)},
        ) from exc
    except RfqAccessDenied as exc:
        raise StageError(
            trigger="access_denied_explicit",
            reason_code=ReasonCode("access_denied_explicit"),
            source_stage="tool_executor",
            details={
                "tool_name": "get_rfq_stages",
                "cause": str(exc),
                "manager_status": 403,
            },
        ) from exc
    except ManagerAuthFailed as exc:
        raise StageError(
            trigger="manager_auth_failed",
            reason_code=ReasonCode("manager_auth_failed"),
            source_stage="tool_executor",
            details={"tool_name": "get_rfq_stages", "cause": str(exc)},
        ) from exc
    except ManagerUnreachable as exc:
        raise StageError(
            trigger="manager_unreachable",
            reason_code=ReasonCode("source_unavailable"),
            source_stage="tool_executor",
            details={"tool_name": "get_rfq_stages", "cause": str(exc)},
        ) from exc

    state.tool_invocations.append(
        ToolInvocation(
            tool_name=ToolId("get_rfq_stages"),
            args={"rfq_code": target.rfq_code},
            result_summary=f"{len(stages)} stages for {target.rfq_code}",
            latency_ms=latency_ms,
            status=status,
        )
    )

    # Project plan-allowed fields from each stage into the packet.
    # The blockers intent asks for blocker_status / blocker_reason_code
    # (the current-stage blocker fields). The stages intent asks for
    # name / order / status (the full ordered list).
    requested = set(state.plan.canonical_requested_fields)

    if "name" in requested or "order" in requested or "status" in requested:
        # Full stage list projection.
        projected_stages = []
        for stage in stages:
            entry: dict[str, object] = {}
            stage_dict = stage.model_dump()
            for f in ("name", "order", "status"):
                if f in requested and f in stage_dict and stage_dict[f] is not None:
                    entry[f] = stage_dict[f]
            if entry:
                projected_stages.append(entry)
        if projected_stages:
            fields_for_packet["stages"] = projected_stages

    if "blocker_status" in requested or "blocker_reason_code" in requested:
        # Blockers projection: scan stages for an ACTIVE blocker.
        # Manager normalizes blocker_status to {"Blocked", "Resolved",
        # None}; "Resolved" means the blocker is RESOLVED, not active
        # (Batch 9.1 audit P1-1: previous truthy check surfaced
        # resolved blockers as active, lying to the user).
        active_blocker = None
        for stage in stages:
            if stage.blocker_status == "Blocked":
                active_blocker = {
                    "stage_name": stage.name,
                    "blocker_status": stage.blocker_status,
                    "blocker_reason_code": stage.blocker_reason_code,
                }
                break  # first wins for Slice 1
        # Always include the result, including None — the EvidenceCheck
        # / Renderer will distinguish "no blocker" from "no evidence".
        fields_for_packet["active_blocker"] = active_blocker

    source_refs.append(
        SourceRef(
            source_type="manager",
            source_id=f"get_rfq_stages:{target.rfq_code}",
            fetched_at=started,
        )
    )
