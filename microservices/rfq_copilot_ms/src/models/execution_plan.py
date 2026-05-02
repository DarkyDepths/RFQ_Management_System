"""TurnExecutionPlan + factory I/O types (§2.2, §2.7, §14.3).

See ``docs/11-Architecture_Frozen_v2.md`` §2.2 (semantics), §2.7
(factory contract), and §14.3 (authoritative type contracts).

Three types in this module:

* ``TurnExecutionPlan`` — the trusted, executable plan. **Strategy and
  policy ONLY** — no runtime outcomes (those live in
  ``ExecutionState``). ``extra="forbid"`` enforces the boundary at the
  type level: ``resolved_targets``, ``tool_invocations``, ``draft_text``,
  ``judge_verdict``, etc. are rejected by validation.

  **Constructed EXCLUSIVELY by ``ExecutionPlanFactory``** (§2.7) from
  one of: ``IntakeDecision`` (FastIntake source),
  ``ValidatedPlannerProposal`` (Planner source), or
  ``EscalationRequest`` (Gate source).

  CI guard §11.5.1 fails the build if any module other than
  ``src/pipeline/execution_plan_factory.py`` instantiates this class.
  Defining the class HERE (as a class declaration, not a call) is fine
  — the AST guard distinguishes calls from class declarations.

* ``EscalationRequest`` — Escalation Gate output (§5.2). Input to
  ``ExecutionPlanFactory.build_from_escalation``. The Gate constructs
  this when a stage emits a failure trigger and re-enters the factory
  rather than instantiating ``TurnExecutionPlan`` directly.

* ``FactoryRejection`` — returned by ``build_from_planner`` when one of
  rules F1..F8 fails. Routed by the orchestrator directly to the
  Escalation Gate with ``source_stage='execution_plan_factory'``.
  Factory rejections are NOT replanned — the registry will not change
  between retries.

Frozen + extra-forbid throughout. ``frozen=True`` is shallow in Pydantic
v2 (it blocks attribute reassignment, not list-content mutation). Deep
immutability is not the architectural defense; CI guard §11.5.1 is.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.path_registry import (
    AccessPolicyName,
    ComparableFieldGroups,
    GuardrailId,
    IntakeSource,
    JudgePolicy,
    MemoryPolicy,
    ModelProfile,
    PathId,
    PersistencePolicy,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
    ToolId,
)
from src.models.planner_proposal import ProposedTarget, ValidatedPlannerProposal


class TurnExecutionPlan(BaseModel):
    """The trusted, executable plan (§2.2, §14.3).

    **Strategy and policy ONLY.** Runtime outcomes
    (``resolved_targets``, ``access_decisions``, ``tool_invocations``,
    ``draft_text``, ``final_text``, ``judge_verdict``,
    ``guardrail_strips``, ``escalations``) live in ``ExecutionState`` —
    ``extra="forbid"`` rejects them here.

    Constructed EXCLUSIVELY by ``ExecutionPlanFactory`` (§2.7).
    CI guard §11.5.1 enforces single-construction.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, protected_namespaces=()
    )

    path: PathId
    intent_topic: str
    source: IntakeSource
    """``fast_intake`` | ``planner`` | ``escalation``. Set by the
    factory. Forensic field — drives ``execution_records.intake_path``
    persistence and source-aware diagnostics."""

    target_candidates: list[ProposedTarget] = Field(default_factory=list)
    resolver_strategy: ResolverStrategy
    required_target_policy: TargetPolicy

    # Tool/access policy resolved from the registry (deterministic copy).
    allowed_evidence_tools: list[ToolId] = Field(default_factory=list)
    allowed_resolver_tools: list[ToolId] = Field(default_factory=list)
    access_policy: AccessPolicyName

    # Field whitelist + post-alias-normalization canonical request.
    allowed_fields: list[str] = Field(default_factory=list)
    forbidden_fields: list[str] = Field(default_factory=list)
    canonical_requested_fields: list[str] = Field(default_factory=list)

    # Stage policies copied from the registry.
    active_guardrails: list[GuardrailId] = Field(default_factory=list)
    judge_policy: Optional[JudgePolicy] = None
    memory_policy: Optional[MemoryPolicy] = None
    persistence_policy: PersistencePolicy

    # Finalizer routing.
    finalizer_template_key: str
    finalizer_reason_code: Optional[ReasonCode] = None
    """Set on direct Path 8.x emission OR by the Escalation Gate. Drives
    the per-template variant selection inside the Finalizer (§5.2)."""

    # Compose model. ``None`` for template-only paths (Path 1, all Path
    # 8.x, all FastIntake plans, template-first Path 4 per §12.6).
    # Compose stage skipped per §5.1.
    model_profile: Optional[ModelProfile] = None

    # Path-7-specific (copied from registry to keep stages self-contained).
    min_accessible_targets_for_comparison: Optional[int] = None
    comparable_field_groups: Optional[ComparableFieldGroups] = None


class EscalationRequest(BaseModel):
    """Escalation Gate output (§5.2, §14.3).

    Input to ``ExecutionPlanFactory.build_from_escalation``. The Gate
    builds this when any stage emits a failure trigger; the factory then
    constructs the Path 8.x ``TurnExecutionPlan`` from it.

    The Gate must NEVER instantiate ``TurnExecutionPlan`` directly —
    re-entering the factory via this request is the architecturally
    sanctioned path (CI guard §11.5.1).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_path: PathId
    reason_code: ReasonCode
    source_stage: str
    trigger: str


class FactoryRejection(BaseModel):
    """ExecutionPlanFactory rule F1..F8 rejection (§2.7, §14.3).

    Returned by ``build_from_planner`` when source-aware policy fails.
    Routed by the orchestrator directly to the Escalation Gate with
    ``source_stage="execution_plan_factory"``. **Factory rejections are
    NOT replanned** — the registry will not change between retries.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    trigger: str
    reason_code: ReasonCode
    rejected_input: ValidatedPlannerProposal
    factory_rule: Literal["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
    rejected_at: datetime
