"""FastIntake — Stage 0 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5.0 and §2.6.

Anchored full-match regex matcher that short-circuits trivial messages
(greetings, thanks, farewells, empty input, pure punctuation) before the
GPT-4o Planner runs. On a hit, emits an ``IntakeDecision`` (see
``src/models/intake_decision.py``) and hands it to the
``ExecutionPlanFactory``. On a miss, the orchestrator falls through to
the Planner — FastIntake never raises, never blocks.

Hard discipline (CI-enforced — §11.5.3):

* **Anchored full-match only** (``re.fullmatch`` or equivalent). No
  substring matching, no fuzzy ranking, no token similarity.
* **No LLM, no DB, no network.** Pure deterministic regex over the user
  message string.
* **Limited path range.** May only emit paths whose ``IntentConfig``
  declares ``IntakeSource.FAST_INTAKE`` in ``allowed_intake_sources``.
  In Slice 1: Path 1 (greeting/thanks/farewell), Path 8.2
  (out_of_scope_nonsense), Path 8.3 (empty_message).
* **When in doubt, miss.** False negatives cost a Planner round-trip
  (cheap). False positives short-circuit a real question into a canned
  reply (broken UX).

Status: SIGNATURE STUB. Type contracts wired in Batch 1; matching logic
lands in a later batch.
"""

from __future__ import annotations

from src.models.intake_decision import IntakeDecision


def try_match(user_message: str) -> IntakeDecision | None:  # noqa: ARG001
    """Return an ``IntakeDecision`` on a hit, ``None`` on a miss.

    Stub: always returns ``None``. Callers (none yet in Batch 1) fall
    through to the Planner path, preserving /v1 behavior unchanged.
    Real anchored-regex implementation lands in a later batch.
    """
    return None
