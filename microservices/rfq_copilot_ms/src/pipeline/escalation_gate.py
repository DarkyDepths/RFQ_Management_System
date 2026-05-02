"""Escalation Gate — single intercept of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5.2 and §6.

**Cross-cutting intercept**, not a stage in the line. When any stage
emits a failure trigger (PlannerValidator, ExecutionPlanFactory,
Resolver, Access, Tool Executor, Evidence Check, Compose, Guardrails,
Judge, or the orchestrator's cumulative-budget rule), the Gate is
invoked.

Hard discipline (§5.2 + CI guard §11.5.1):

* The Gate **does NOT** instantiate ``TurnExecutionPlan`` directly.
  It builds an ``EscalationRequest`` and re-enters
  ``ExecutionPlanFactory.build_from_escalation(...)`` — the factory
  is the only sanctioned plan constructor, including for Path 8.x.
* Stages do **not** handle their own escalation. They raise
  ``StageError(trigger, reason_code, source_stage, details)``;
  the Gate decides routing.
* The Finalizer is **policy-stupid** — it always reads
  ``state.plan.finalizer_template_key`` regardless of source. The Gate
  never feeds the Finalizer ``state.escalations[-1]`` to figure out
  what to render.

Routing contract (§6 escalation matrix):

* The Gate maps ``trigger`` -> target Path 8.x sub-case.
* Within that sub-case, ``reason_code`` selects the template variant.

Allowed registry reader (CI guard §11.5.2):

* This module and ``execution_plan_factory.py`` are the **only** two
  files in ``src/pipeline/`` permitted to import from
  ``src.config.path_registry``.

Trigger -> Path mapping table (Slice 1 / Batch 5 reachable triggers):

==============================================  ============
Trigger                                         Path
==============================================  ============
unclear_intent_topic                            8.3
no_target_proposed                              8.3
confidence_below_threshold                      8.3
multi_intent_detected                           8.3
empty_message                                   8.3
unsupported_intent_topic                        8.1
unsupported_field_requested                     8.1
forbidden_field_requested                       8.1
intake_source_not_allowed                       8.1
invalid_planner_proposal                        8.1
group_C_field_requested                         8.1
out_of_scope                                    8.2
out_of_scope_nonsense                           8.2
access_denied_explicit                          8.4
all_inaccessible                                8.4
manager_unreachable / source_unavailable        8.5
llm_unavailable                                 8.5
evidence_empty / no_evidence                    8.5
unknown_tool                                    8.5
turn_too_slow                                   8.5
==============================================  ============

If a trigger has no mapping entry, the gate raises ``ValueError``
loudly — never invent a fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Registry CONFIG import is restricted to this module + execution_plan_factory.py
# by CI guard §11.5.2.
from src.config.path_registry import PATH_CONFIGS  # noqa: F401 — kept for the allowlist anchor + future template lookups
from src.models.execution_plan import EscalationRequest
from src.models.execution_state import EscalationEvent, ExecutionState
from src.models.path_registry import PathId, ReasonCode
from src.pipeline.execution_plan_factory import ExecutionPlanFactory


# ── Trigger -> Path 8.x mapping (Slice 1 reachable set) ───────────────────


_TRIGGER_TO_PATH: dict[str, PathId] = {
    # Path 8.1 — unsupported / invalid (factory + validator rejections)
    "unsupported_intent_topic": PathId.PATH_8_1,
    "unsupported_field_requested": PathId.PATH_8_1,
    "forbidden_field_requested": PathId.PATH_8_1,
    "intake_source_not_allowed": PathId.PATH_8_1,
    "invalid_planner_proposal": PathId.PATH_8_1,
    "group_C_field_requested": PathId.PATH_8_1,
    # Path 8.2 — out-of-scope (planner-direct + judge)
    "out_of_scope": PathId.PATH_8_2,
    "out_of_scope_nonsense": PathId.PATH_8_2,
    "judge_verdict_scope_drift": PathId.PATH_8_2,
    # Path 8.3 — clarification (validator + resolver + planner-direct)
    "unclear_intent_topic": PathId.PATH_8_3,
    "no_target_proposed": PathId.PATH_8_3,
    "comparison_missing_target": PathId.PATH_8_3,
    "confidence_below_threshold": PathId.PATH_8_3,
    "multi_intent_detected": PathId.PATH_8_3,
    "empty_message": PathId.PATH_8_3,
    "ambiguous_target_count_exceeded": PathId.PATH_8_3,
    "pre_search_query_underspecified": PathId.PATH_8_3,
    "post_search_no_safe_presentation": PathId.PATH_8_3,
    # Path 8.4 — inaccessible
    "access_denied_explicit": PathId.PATH_8_4,
    "all_inaccessible": PathId.PATH_8_4,
    "partial_inaccessibility_below_min": PathId.PATH_8_4,
    # Path 8.5 — no_evidence / source_down / llm_down / orchestrator backstop
    "evidence_empty": PathId.PATH_8_5,
    "no_evidence": PathId.PATH_8_5,
    "manager_unreachable": PathId.PATH_8_5,
    "source_unavailable": PathId.PATH_8_5,
    "intelligence_unreachable": PathId.PATH_8_5,
    "llm_unreachable": PathId.PATH_8_5,
    "llm_unavailable": PathId.PATH_8_5,
    "judge_verdict_fabrication": PathId.PATH_8_5,
    "judge_verdict_forbidden_inference": PathId.PATH_8_5,
    "judge_verdict_unsourced_citation": PathId.PATH_8_5,
    "judge_verdict_comparison_violation": PathId.PATH_8_5,
    "target_isolation_violation": PathId.PATH_8_5,
    "forbidden_inference_detected_deterministic": PathId.PATH_8_5,
    "ambiguity_loop_max_reached": PathId.PATH_8_5,
    "turn_too_slow": PathId.PATH_8_5,
    "unknown_tool": PathId.PATH_8_5,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EscalationGate:
    """Cross-cutting failure-trigger intercept.

    Routes to Path 8.x by building an ``EscalationRequest`` and calling
    ``ExecutionPlanFactory.build_from_escalation(...)``. **Never
    instantiates ``TurnExecutionPlan`` directly** — CI guard §11.5.1
    enforces this.
    """

    def __init__(self, factory: ExecutionPlanFactory):
        self._factory = factory

    def route(
        self,
        state: ExecutionState,
        trigger: str,
        reason_code: ReasonCode,
        source_stage: str,
        details: dict | None = None,
    ) -> None:
        """Map trigger -> Path 8.x, build EscalationRequest, re-enter
        factory, swap ``state.plan`` for the new Path 8.x plan, and
        append an EscalationEvent for forensics.

        Raises ``ValueError`` on unmapped trigger — fail loudly, never
        invent a fallback.
        """
        target_path = _TRIGGER_TO_PATH.get(trigger)
        if target_path is None:
            raise ValueError(
                f"EscalationGate has no Path 8.x mapping for trigger "
                f"{trigger!r}. Add an entry to "
                f"src/pipeline/escalation_gate.py::_TRIGGER_TO_PATH "
                f"or fix the source stage to emit a known trigger. "
                f"Source stage: {source_stage!r}, reason_code: {reason_code!r}."
            )

        request = EscalationRequest(
            target_path=target_path,
            reason_code=reason_code,
            source_stage=source_stage,
            trigger=trigger,
        )

        # Re-enter the factory — the only sanctioned construction path
        # for Path 8.x plans (CI guard §11.5.1).
        p8_plan = self._factory.build_from_escalation(
            request, actor=state.actor
        )

        # Swap the plan in-place. The orchestrator's downstream stages
        # (Finalizer) read state.plan and render the safe template.
        state.plan = p8_plan

        # Forensics record (lands in execution_records when Persist ships).
        state.escalations.append(
            EscalationEvent(
                trigger=trigger,
                reason_code=reason_code,
                source_stage=source_stage,  # type: ignore[arg-type] — Literal narrowed at runtime
                fired_at=_utc_now(),
                details=details,
            )
        )

        # Reset any partially-rendered final_text so the Finalizer
        # renders the Path 8.x template instead of the aborted Path 4
        # render.
        state.final_text = None
        state.final_path = None
