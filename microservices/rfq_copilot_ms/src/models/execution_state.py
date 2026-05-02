"""ExecutionState — runtime mutable state for one turn (§2.5, §14.4).

See ``docs/11-Architecture_Frozen_v2.md`` §2.5 (semantics) and §14.4
(authoritative runtime types).

================================================================
The hard separation: state vs plan
================================================================

* ``TurnExecutionPlan`` (``src/models/execution_plan.py``) — STRATEGY
  AND POLICY ONLY. Frozen + extra-forbid. Constructed once by the
  factory, then read-only.

* ``ExecutionState`` (this module) — RUNTIME OUTCOMES ONLY. Mutable.
  Stages append to it as they run. Captures what *happened* during this
  turn, not what was *planned*.

The contract is type-enforced: this module's models accept the runtime
fields (``resolved_targets``, ``access_decisions``, ``tool_invocations``,
``evidence_packets``, ``draft_text``, ``guardrail_strips``,
``judge_verdict``, ``final_text``, ``final_path``, ``escalations``).
``TurnExecutionPlan`` rejects them via ``extra="forbid"``.

================================================================
Why ExecutionState is mutable (NOT frozen)
================================================================

Stages MUST be able to write their slice as they complete:
``state.resolved_targets = [...]`` after Resolver, ``state.draft_text =
"..."`` after Compose, etc. Freezing would force every stage to copy the
entire state on every write, defeating the partial-write design that
``execution_records`` (§4) relies on for forensics survivability.

The execution_record (§4.2) is a serialization of this object plus
timing/tokens metadata.

================================================================
Per-source field population (see freeze §4.2 matrix)
================================================================

==============================  ============  =============
Field                           FastIntake    Planner
==============================  ============  =============
``intake_path``                 fast_intake   planner
``intake_decision``             populated     None
``planner_proposal``            None          populated
``validated_planner_proposal``  None          populated
``planner_latency_ms``          None          populated
``planner_tokens``              None          populated
``turn_execution_plan``         populated     populated
==============================  ============  =============
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.intake_decision import IntakeDecision
from src.models.path_registry import (
    GuardrailId,
    JudgeTriggerName,
    PathId,
    ReasonCode,
    ToolId,
)
from src.models.planner_proposal import (
    PlannerProposal,
    ValidatedPlannerProposal,
)


# ── Runtime sub-objects (frozen per-record forensics) ─────────────────────


_FROZEN_RECORD = ConfigDict(extra="forbid", frozen=True)
"""Sub-objects appended to ExecutionState lists are frozen records — once
the Resolver writes a ResolvedTarget, no later stage may mutate it. The
container lists themselves remain mutable (stages append)."""


class ResolvedTarget(BaseModel):
    """Resolver output — UUID confirmed by the manager (§14.4)."""

    model_config = _FROZEN_RECORD

    rfq_id: UUID
    rfq_code: Optional[str] = None
    rfq_label: str
    resolution_method: Literal[
        "page_default",
        "search_by_code",
        "session_state",
        "search_by_descriptor",
    ]


class AccessDecision(BaseModel):
    """Per-target Access stage verdict (§14.4)."""

    model_config = _FROZEN_RECORD

    target_id: UUID
    granted: bool
    reason: Optional[str] = None
    checked_at: datetime


class SourceRef(BaseModel):
    """Provenance pointer for an evidence field (§14.4)."""

    model_config = _FROZEN_RECORD

    source_type: Literal["manager", "intelligence", "rag"]
    source_id: str
    fetched_at: datetime


class EvidencePacket(BaseModel):
    """Per-target labelled evidence (§14.4).

    Built by the Tool Executor (raw fetch) and assembled by the Context
    Builder (per-target labelling, prompt-injection delimiters per
    §12.1, field minimization per §12.2).

    ``target_id`` is None for non-target-bound paths (Path 2 / Path 3 /
    Path 8.x). ``target_label`` is always set (e.g. ``"IF-0001"``,
    ``"portfolio"``, ``"domain_kb"``).
    """

    model_config = _FROZEN_RECORD

    target_id: Optional[UUID] = None
    target_label: str
    fields: dict[str, object] = Field(default_factory=dict)
    source_refs: list[SourceRef] = Field(default_factory=list)


class ToolInvocation(BaseModel):
    """One Tool Executor call (forensics, §14.4)."""

    model_config = _FROZEN_RECORD

    tool_name: ToolId
    args: dict
    result_summary: str
    latency_ms: int
    status: Literal["ok", "timeout", "error_404", "error_500", "error_other"]
    error_message: Optional[str] = None


class GuardrailAction(BaseModel):
    """One guardrail action (forensics, §14.4)."""

    model_config = _FROZEN_RECORD

    guardrail_id: GuardrailId
    action: Literal["pass", "strip_claim", "rewrite", "escalate"]
    reason: Optional[str] = None
    affected_text: Optional[str] = None


class JudgeViolation(BaseModel):
    """One Judge violation entry (§14.4)."""

    model_config = _FROZEN_RECORD

    trigger: JudgeTriggerName
    reason_code: ReasonCode
    excerpt: Optional[str] = None


class JudgeVerdict(BaseModel):
    """Judge stage output (§14.4)."""

    model_config = _FROZEN_RECORD

    verdict: Literal["pass", "fail"]
    triggers_checked: list[JudgeTriggerName] = Field(default_factory=list)
    violations: list[JudgeViolation] = Field(default_factory=list)
    rationale: str
    latency_ms: int


class EscalationEvent(BaseModel):
    """One Escalation Gate firing (forensics, §14.4).

    Appended to ``ExecutionState.escalations`` whenever the Gate routes
    a stage failure trigger.

    NOTE: ``source_stage`` includes ``"factory"`` and ``"orchestrator"``
    in addition to the freeze §14.4 ten core stages. Factory rejections
    (rules F1..F8) and orchestrator-level catches (turn-budget,
    unhandled exceptions) need distinct source labels for forensics.
    Additive extension introduced in Batch 5; no breaking change to
    callers that emit the original ten values.
    """

    model_config = _FROZEN_RECORD

    trigger: str
    reason_code: ReasonCode
    source_stage: Literal[
        "planner",
        "validator",
        "factory",
        "resolver",
        "access",
        "tool_executor",
        "evidence_check",
        "context_builder",
        "compose",
        "guardrail",
        "judge",
        "orchestrator",
    ]
    fired_at: datetime
    details: Optional[dict] = None


# ── ExecutionState — mutable runtime container ────────────────────────────


class ExecutionState(BaseModel):
    """Runtime mutable state for one turn (§2.5, §14.4).

    Stages mutate it as they run. NOT frozen — partial-write semantics
    require in-place updates so the execution_record survives mid-pipeline
    crashes (see §4.3 lifecycle rules).

    ``extra="forbid"`` is still enforced: stages can update the declared
    slice fields, but cannot smuggle in new fields. New per-stage
    forensics need a model field added here in a future batch.
    """

    model_config = ConfigDict(extra="forbid")

    # ── Required at construction ──
    turn_id: str
    actor: Actor
    plan: TurnExecutionPlan
    user_message: str

    # ── Intake forensics — set by FastIntake / Planner ──
    intake_path: Literal["fast_intake", "planner"]
    intake_decision: Optional[IntakeDecision] = None
    planner_proposal: Optional[PlannerProposal] = None
    validated_planner_proposal: Optional[ValidatedPlannerProposal] = None

    # ── Filled by Resolver ──
    resolved_targets: list[ResolvedTarget] = Field(default_factory=list)

    # ── Filled by Access ──
    access_decisions: list[AccessDecision] = Field(default_factory=list)

    # ── Filled by Memory Load ──
    # Working memory is the recent user/assistant pair window; episodic
    # summaries are the longer-thread digests. Concrete element types
    # land in a future batch (Memory module owner). Kept loose here so
    # Batch 1 doesn't lock in a type that Slice 2+ may refine.
    working_memory: list = Field(default_factory=list)
    episodic_summaries: list = Field(default_factory=list)

    # ── Filled by Tool Executor / Context Builder ──
    evidence_packets: list[EvidencePacket] = Field(default_factory=list)
    tool_invocations: list[ToolInvocation] = Field(default_factory=list)

    # ── Filled by Compose ──
    draft_text: Optional[str] = None

    # ── Filled by Guardrails ──
    guardrail_strips: list[GuardrailAction] = Field(default_factory=list)

    # ── Filled by Judge ──
    judge_verdict: Optional[JudgeVerdict] = None

    # ── Filled by Finalizer / Escalation Gate ──
    final_text: Optional[str] = None
    final_path: Optional[PathId] = None
    """May differ from ``plan.path`` if the turn was escalated — e.g.
    plan emitted Path 4 but the Gate routed to Path 8.4 because the
    target was inaccessible."""

    escalations: list[EscalationEvent] = Field(default_factory=list)
