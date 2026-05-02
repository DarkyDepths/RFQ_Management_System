"""LLM Judge I/O contracts (Batch 8).

Wire types for the Judge stage (``src/pipeline/judge.py``). Judge takes
plan + evidence + draft_text, calls the LLM with strict JSON-schema
output, and returns a verdict + violations.

This module is intentionally minimal — ``JudgeVerdict`` and
``JudgeViolation`` already exist in ``src/models/execution_state.py``
(Batch 1, freeze §14.4) and are reused. We only add the Judge **input**
DTO and a ``JudgeVerdictStatus`` alias for callers that don't want to
import the full Literal.

Hard discipline (per freeze §5 Judge row + §8 forbidden):

* No tool selection. No manager calls. No registry config import.
* Verifies the draft; does NOT rewrite. The orchestrator owns
  promote-or-route; the Judge only emits a verdict.
* No invented facts — verdict must be derivable from the provided
  ``draft_text`` + ``evidence_packets``.

Reason-code mapping (Judge violation -> Path 8.5 reason_code):

* fabrication             -> ``judge_verdict_fabrication``
* forbidden_inference     -> ``judge_verdict_forbidden_inference``
* unsourced_citation      -> ``judge_verdict_unsourced_citation``
* target_isolation        -> ``target_isolation_violation``
* comparison_violation    -> ``judge_verdict_comparison_violation``

The orchestrator picks the FIRST violation's reason_code when raising
the gate-routing StageError. Multiple violations are persisted as
forensics; only the first drives routing.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


# Status alias for callers that want a clean enum-like value without
# importing the full ``JudgeVerdict.verdict`` Literal.
JudgeVerdictStatus = Literal["pass", "fail"]


# Reason-code mapping for known violation triggers. Used by the Judge
# stage when constructing JudgeViolation entries; used by the
# orchestrator when extracting the StageError reason_code from the
# first violation.
JUDGE_TRIGGER_TO_REASON_CODE: dict[str, str] = {
    "fabrication": "judge_verdict_fabrication",
    "forbidden_inference": "judge_verdict_forbidden_inference",
    "unsourced_citation": "judge_verdict_unsourced_citation",
    "target_isolation": "target_isolation_violation",
    "comparison_violation": "judge_verdict_comparison_violation",
}


class JudgeInput(BaseModel):
    """The compact input passed to the Judge stage. Constructed by the
    orchestrator from ``state.plan`` + ``state.evidence_packets`` +
    ``state.draft_text``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    intent_topic: str
    target_rfq_code: Optional[str] = None
    draft_text: str
    canonical_requested_fields: list[str]
    forbidden_fields: list[str]
    evidence_packets: list[dict]
    triggers_to_check: list[str]
    """Which violation triggers the Judge should explicitly check for.
    For Path 4: ``["fabrication", "forbidden_inference"]`` typically
    (set in the controller from ``plan.judge_policy.triggers``).
    """
