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

Batch 0 status: STUB ONLY. No LLM call wired yet.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future signature (illustrative — do not import yet):
#
#   from src.connectors.llm_connector import LlmConnector
#   from src.models.planner_proposal import PlannerProposal
#
#   class Planner:
#       def __init__(self, llm: LlmConnector): ...
#       def classify(self, user_message: str, history: list) -> PlannerProposal:
#           """One LLM call, JSON schema enforced, returns untrusted proposal."""


class Planner:
    """Stub class. Real GPT-4o structured-output wiring lands in Slice 1."""

    def classify(self, user_message: str, history: list | None = None):  # noqa: ARG002
        raise NotImplementedError(
            "Planner.classify() is scaffolded but not implemented. "
            "See docs/11-Architecture_Frozen_v2.md §2.1 / §3.5."
        )
