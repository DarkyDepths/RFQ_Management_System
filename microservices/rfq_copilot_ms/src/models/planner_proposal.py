"""Planner I/O types — PlannerProposal, ValidatedPlannerProposal,
ValidationRejection, ProposedTarget (§2.1, §2.4, §14.3).

See ``docs/11-Architecture_Frozen_v2.md`` §2.1 / §2.3 / §2.4 (semantics)
and §14.3 (authoritative type contract).

Three types form the LLM-side of intake:

* ``PlannerProposal`` — **untrusted** raw output of the GPT-4o Planner.
  Never executed directly. Consumed only by the PlannerValidator.
  ``extra="forbid"`` is the contract enforcement: the LLM cannot
  smuggle policy fields (evidence_tools, judge_triggers, guardrails,
  resolved_targets, etc.) — those would be silently rejected by Pydantic
  validation.
* ``ValidatedPlannerProposal`` — wraps a structurally sound proposal.
  Carries no policy decisions; only structural soundness has been
  confirmed. Input to ``ExecutionPlanFactory.build_from_planner``.
* ``ValidationRejection`` — one PlannerValidator rejection record. Each
  replan attempt appends one entry. Only the FINAL failed attempt's
  trigger is routed to the Escalation Gate.

``ProposedTarget`` is also defined here — the Planner-extracted RFQ
reference (e.g. ``"IF-0001"``, ``"the SEC RFQ"``, ``"this one"``) before
the Resolver stage confirms it against the manager.

Forbidden direct path emissions from the Planner (§2.1):
* Path 8.4 (inaccessible) and Path 8.5 (no-evidence / source-down /
  llm-down) — these classes can only arise from a stage failure
  trigger via the Escalation Gate. PlannerValidator rule 2d catches
  direct emission and rejects to 8.1. (Validation logic lives in the
  PlannerValidator stage, not in this Pydantic model — Batch 3.)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.path_registry import PathId, ReasonCode


class ProposedTarget(BaseModel):
    """LLM-extracted target reference, not yet resolved (§14.3).

    ``proposed_kind`` is closed by ``Literal[...]`` so any other value
    (a hallucinated kind name, for example) is rejected at validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_reference: str
    proposed_kind: Literal[
        "rfq_code",
        "natural_reference",
        "page_default",
        "session_state_pick",
    ]


class PlannerProposal(BaseModel):
    """Untrusted LLM output (§2.1, §14.3).

    Never executed directly. Must pass through the PlannerValidator
    (which emits ``ValidatedPlannerProposal`` or a
    ``ValidationRejection``) before the ExecutionPlanFactory will accept
    it.

    ``extra="forbid"`` is load-bearing here: it enforces that the LLM
    cannot emit policy fields. If the LLM tries to add ``evidence_tools``
    or ``judge_triggers`` or ``resolved_targets`` to its JSON output,
    Pydantic validation fails BEFORE any pipeline code accepts it. This
    is the type-system half of the architectural commitment that
    "the LLM produces language; code produces truth."
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: PathId
    intent_topic: str
    target_candidates: list[ProposedTarget] = Field(default_factory=list)
    requested_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    classification_rationale: str
    """Audit/debug only. **Validator and downstream stages MUST NOT use
    this field for any decision** — it is for human inspection only."""

    multi_intent_detected: bool = False
    """Optional semantic-classification flag. When true, the planner
    emits ``path=PATH_8_3`` directly with
    ``reason_code="multi_intent_detected"``; PlannerValidator rule 2b
    passes the proposal through; the factory builds the minimal Path
    8.3 plan. The Escalation Gate is bypassed entirely."""

    # Path-3-specific structured query slots (null on other paths).
    # ExecutionPlanFactory rule F8 enforces presence against
    # IntentConfig.required_query_slots.
    filters: Optional[dict] = None
    output_shape: Optional[str] = None
    sort: Optional[str] = None
    limit: Optional[int] = None


class ValidationRejection(BaseModel):
    """One PlannerValidator rejection (§14.3).

    Each replan attempt appends one entry to
    ``ValidatedPlannerProposal.replan_history``. Only the FINAL failed
    attempt's trigger is routed to the Escalation Gate.

    ``rule_number`` references the validator rules in §2.3 (rules 1, 2,
    2b, 2c, 2d, 3, 4, 5 in the PlannerValidator-only set).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rejected_proposal: PlannerProposal
    rule_number: int
    trigger: str
    reason_code: ReasonCode
    message_for_replan: str
    attempt_index: int
    rejected_at: datetime


class ValidatedPlannerProposal(BaseModel):
    """PlannerValidator output (§2.4, §14.3).

    Wraps a structurally sound ``PlannerProposal``. Carries NO policy
    decisions — only structural soundness has been confirmed. Input to
    ``ExecutionPlanFactory.build_from_planner`` (rules F1..F8 then add
    the policy from the registry).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal: PlannerProposal
    validated_at: datetime
    replan_history: list[ValidationRejection] = Field(default_factory=list)
