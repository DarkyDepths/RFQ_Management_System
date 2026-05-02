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
* Stages do **not** handle their own escalation. They emit a
  ``(trigger, reason_code, source_stage, details)`` tuple; the Gate
  decides routing.
* The Finalizer is **policy-stupid** — it always reads
  ``state.plan.finalizer_template_key`` regardless of source. The Gate
  never feeds the Finalizer ``state.escalations[-1]`` to figure out
  what to render.

Routing contract (§6 escalation matrix):

* trigger -> ``ESCALATION_MATRIX[trigger]`` -> target Path 8.x sub-case
  (8.1 unsupported, 8.2 out-of-scope, 8.3 clarification, 8.4
  inaccessible, 8.5 no-evidence / source-down / llm-down /
  turn-too-slow).

Allowed registry reader (CI guard §11.5.2):

* This module and ``execution_plan_factory.py`` are the **only** two
  files in ``src/pipeline/`` permitted to import from
  ``src.config.path_registry``. The Gate uses the registry only to
  look up ``PathConfig.finalizer_template_keys[reason_code]`` when
  constructing the ``EscalationRequest``.

Status: SIGNATURE STUB. Type contracts wired in Batch 1; matrix +
factory re-entry land in a later batch.
"""

from __future__ import annotations

from src.models.execution_state import ExecutionState
from src.models.path_registry import ReasonCode
from src.pipeline.execution_plan_factory import ExecutionPlanFactory


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
        state: ExecutionState,  # noqa: ARG002
        trigger: str,  # noqa: ARG002
        reason_code: ReasonCode,  # noqa: ARG002
        source_stage: str,  # noqa: ARG002
    ) -> None:
        raise NotImplementedError(
            "EscalationGate.route() scaffolded only. "
            "Must call ExecutionPlanFactory.build_from_escalation() per §5.2."
        )
