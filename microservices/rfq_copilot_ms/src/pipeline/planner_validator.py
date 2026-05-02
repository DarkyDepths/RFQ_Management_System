"""PlannerValidator — Stage 2 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §2.3 and §2.4.

Pure deterministic function:
``(PlannerProposal) -> ValidatedPlannerProposal | EscalationTrigger``.

Catches **LLM-output structural failure modes only**: malformed schema,
semantically invalid direct emissions, structural arity mismatches.

It does **NOT**:

* Read the Path Registry. (CI guard §11.5.2 enforces this — no
  ``from src.config.path_registry import`` allowed in this module.)
* Enforce policy (allowed/forbidden fields, confidence thresholds,
  intent_topic existence, Group C judgment fields, Path 3 query slots).
  All policy enforcement lives in the ``ExecutionPlanFactory`` (rules
  F1..F8).
* Construct ``TurnExecutionPlan``. Only the factory may do that
  (CI guard §11.5.1).

Validator rules in execution order — first failure wins (§2.3):

1. ``path`` is a known ``PathId`` enum value.
2. ``path == 8_1 / 8_2`` -> direct pass-through.
2b. ``path == 8_3`` AND ``multi_intent_detected == True`` -> pass-through.
2c. ``path == 8_3`` AND flag false -> ``invalid_planner_proposal`` -> 8.1.
2d. ``path in {8_4, 8_5}`` (forbidden direct emission) -> 8.1.
3. ``intent_topic`` is non-empty / not pure whitespace.
4. Paths 4/5/6: at least 1 target_candidate.
5. Path 7: at least 2 target_candidates (NEVER silently downgrade to 4).

Replan policy: at most one re-prompt per turn with the rejection reason
as feedback. A second failure routes to the Escalation Gate. Factory
rejections (rules F1..F8) are NOT replanned — the registry will not
change between retries.

Status: SIGNATURE STUB. Type contracts wired in Batch 1; rule logic
lands in a later batch.
"""

from __future__ import annotations

from src.models.planner_proposal import (
    PlannerProposal,
    ValidatedPlannerProposal,
    ValidationRejection,
)


class PlannerValidator:
    """LLM-failure structural checks only (rules 1, 2, 2b, 2c, 2d, 3, 4, 5).

    Pure deterministic function — no Path Registry reads, no policy
    enforcement (those move to ExecutionPlanFactory rules F1..F8).
    """

    def validate(
        self, proposal: PlannerProposal  # noqa: ARG002
    ) -> ValidatedPlannerProposal | ValidationRejection:
        raise NotImplementedError(
            "PlannerValidator.validate() is scaffolded but not implemented. "
            "See docs/11-Architecture_Frozen_v2.md §2.3."
        )
