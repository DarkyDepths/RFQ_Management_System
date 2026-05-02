"""Planner I/O types — PlannerProposal, ValidatedPlannerProposal,
ValidationRejection, ProposedTarget (§2.1, §2.4, §14.3).

See ``docs/11-Architecture_Frozen_v2.md`` §2.1 / §2.3 / §2.4 (semantics)
and §14.3 (authoritative type contract).

Three types in this module form the LLM-side of intake:

* ``PlannerProposal`` — **untrusted** raw output of the GPT-4o Planner.
  Never executed directly. Consumed only by the PlannerValidator.
* ``ValidatedPlannerProposal`` — wraps a structurally sound proposal.
  Carries no policy decisions; only structural soundness has been
  confirmed. Input to ``ExecutionPlanFactory.build_from_planner``.
* ``ValidationRejection`` — one PlannerValidator rejection record.
  Each replan attempt appends one entry. Only the FINAL failed attempt's
  trigger is routed to the Escalation Gate.

``ProposedTarget`` is also defined here — the Planner-extracted RFQ
reference (e.g. ``"IF-0001"``, ``"the SEC RFQ"``, ``"this one"``) before
the Resolver stage confirms it against the manager.

Forbidden direct emissions from the Planner (§2.1):

* Path 8.4 (inaccessible) and Path 8.5 (no-evidence / source-down /
  llm-down) — these classes can only arise from a stage failure
  trigger via the Escalation Gate. PlannerValidator rule 2d catches
  direct emission and rejects to 8.1.

Batch 0 status: STUB ONLY. Pydantic bodies land in Slice 1.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future shape (illustrative — do not import yet):
#
#   from datetime import datetime
#   from typing import Literal, Optional
#   from pydantic import BaseModel, Field
#   from src.models.path_registry import PathId, ReasonCode
#
#   class ProposedTarget(BaseModel):
#       raw_reference: str
#       proposed_kind: Literal["rfq_code", "natural_reference",
#                              "page_default", "session_state_pick"]
#
#   class PlannerProposal(BaseModel):
#       """Untrusted LLM output. Never executed directly."""
#       path: PathId
#       intent_topic: str
#       target_candidates: list[ProposedTarget] = Field(default_factory=list)
#       requested_fields: list[str] = Field(default_factory=list)
#       confidence: float
#       classification_rationale: str   # audit/debug only — never enforcement
#       multi_intent_detected: bool = False
#       filters: Optional[dict] = None
#       output_shape: Optional[str] = None
#       sort: Optional[str] = None
#       limit: Optional[int] = None
#
#   class ValidatedPlannerProposal(BaseModel):
#       proposal: PlannerProposal
#       validated_at: datetime
#       replan_history: list["ValidationRejection"] = Field(default_factory=list)
#
#   class ValidationRejection(BaseModel):
#       rejected_proposal: PlannerProposal
#       rule_number: int                # 1..5 in §2.3
#       trigger: str
#       reason_code: ReasonCode
#       message_for_replan: str
#       attempt_index: int
#       rejected_at: datetime
