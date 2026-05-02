"""Planner — Stage 1 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §2.1 and §3.5.

GPT-4o **structured** classifier (JSON schema enforced, ``temperature=0``).
Runs only when FastIntake (Stage 0) misses. Emits a single
``PlannerProposal`` (see ``src/models/planner_proposal.py``) — an
**untrusted** LLM output that downstream code never accepts directly.

The PlannerValidator (Stage 2) consumes the proposal and either emits a
``ValidatedPlannerProposal`` for the ExecutionPlanFactory or escalates
via the gate.

Allowed direct path emissions (per §2.1):

* Normal answer paths: 1, 2, 3, 4, 5, 6, 7
* Direct semantic emission: 8.1 (clear unsupported), 8.2 (clear out-of-scope)
* Direct semantic emission: 8.3 ONLY when ``multi_intent_detected=True``
* **NEVER** allowed: 8.4 (inaccessible), 8.5 (no-evidence / source-down)
  — these come only from the Escalation Gate routing a stage trigger.

Hard discipline:

* JSON-schema-enforced output (no free text — see §8 forbidden list).
* Uses ``PLANNER_MODEL_CONFIG`` (top-level config — runs *before* the
  path is known, so cannot read per-path ``model_profile``). See §3.5.
* Reads NO Path Registry entries directly. The validator + factory own
  policy enforcement.

Status: SIGNATURE STUB. Type contracts wired in Batch 1; LLM call lands
in a later batch.
"""

from __future__ import annotations

from src.models.planner_proposal import PlannerProposal


class Planner:
    """GPT-4o structured Planner — emits untrusted ``PlannerProposal``."""

    def classify(
        self,
        user_message: str,  # noqa: ARG002
        history: list | None = None,  # noqa: ARG002
    ) -> PlannerProposal:
        raise NotImplementedError(
            "Planner.classify() is scaffolded but not implemented. "
            "See docs/11-Architecture_Frozen_v2.md §2.1 / §3.5."
        )
