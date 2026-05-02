"""TurnExecutionPlan + factory I/O types (§2.2, §2.7, §14.3).

See ``docs/11-Architecture_Frozen_v2.md`` §2.2 (semantics), §2.7
(factory contract), and §14.3 (authoritative type contracts).

Four types in this module:

* ``TurnExecutionPlan`` — the trusted, executable plan. **Constructed
  EXCLUSIVELY by ``ExecutionPlanFactory``** (§2.7) from one of:
  ``IntakeDecision`` (FastIntake source), ``ValidatedPlannerProposal``
  (Planner source), or ``EscalationRequest`` (Gate source). The pipeline
  reads only this for policy. Self-contained — stages never reach back
  into the registry.

  CI guard §11.5.1 fails the build if any module other than
  ``src/pipeline/execution_plan_factory.py`` instantiates this class.

* ``EscalationRequest`` — Escalation Gate output (§5.2). Input to
  ``ExecutionPlanFactory.build_from_escalation``. The Gate constructs
  this when a stage emits a failure trigger and re-enters the factory.

* ``FactoryRejection`` — returned by ``build_from_planner`` when one of
  rules F1..F8 fails. Routed by the orchestrator directly to the
  Escalation Gate with ``source_stage='execution_plan_factory'``.
  Factory rejections are NOT replanned — the registry will not change
  between retries.

(``IntakeSource`` enum lives in ``src/models/path_registry.py`` since
it's also referenced by ``IntentConfig.allowed_intake_sources``.)

Batch 0 status: STUB ONLY. Pydantic bodies land in Slice 1.

CRITICAL: when Slice 1 implements ``TurnExecutionPlan(...)``, the only
file that may instantiate it is ``src/pipeline/execution_plan_factory.py``.
The class **definition** (``class TurnExecutionPlan(BaseModel):``) is
fine here — the AST guard distinguishes calls from class declarations.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future shape (illustrative — do not import yet):
#
#   from typing import Literal, Optional
#   from pydantic import BaseModel
#   from src.models.path_registry import (
#       PathId, IntakeSource, ResolverStrategy, AccessPolicyName,
#       ToolId, GuardrailId, ReasonCode,
#       TargetPolicy, JudgePolicy, MemoryPolicy, PersistencePolicy,
#       ModelProfile, ComparableFieldGroups,
#   )
#   from src.models.planner_proposal import ProposedTarget, ValidatedPlannerProposal
#
#   class TurnExecutionPlan(BaseModel):
#       """Constructed EXCLUSIVELY by ExecutionPlanFactory. CI-enforced."""
#       path: PathId
#       intent_topic: str
#       source: IntakeSource
#       target_candidates: list[ProposedTarget]
#       resolver_strategy: ResolverStrategy
#       required_target_policy: TargetPolicy
#       allowed_evidence_tools: list[ToolId]
#       allowed_resolver_tools: list[ToolId]
#       access_policy: AccessPolicyName
#       allowed_fields: list[str]
#       forbidden_fields: list[str]
#       canonical_requested_fields: list[str]
#       active_guardrails: list[GuardrailId]
#       judge_policy: Optional[JudgePolicy]
#       memory_policy: Optional[MemoryPolicy]
#       persistence_policy: PersistencePolicy
#       finalizer_template_key: str
#       finalizer_reason_code: Optional[ReasonCode] = None
#       model_profile: Optional[ModelProfile] = None
#       min_accessible_targets_for_comparison: Optional[int] = None
#       comparable_field_groups: Optional[ComparableFieldGroups] = None
#
#   class EscalationRequest(BaseModel):
#       target_path: PathId
#       reason_code: ReasonCode
#       source_stage: str
#       trigger: str
#
#   class FactoryRejection(BaseModel):
#       trigger: str
#       reason_code: ReasonCode
#       rejected_input: ValidatedPlannerProposal
#       factory_rule: Literal["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
#       rejected_at: ...
