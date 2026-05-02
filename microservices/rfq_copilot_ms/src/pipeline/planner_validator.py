"""PlannerValidator — Stage 2 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §2.3 and §2.4.

Pure deterministic function:
``(PlannerProposal) -> ValidatedPlannerProposal | ValidationRejection``.

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
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.models.path_registry import PathId, ReasonCode
from src.models.planner_proposal import (
    PlannerProposal,
    ValidatedPlannerProposal,
    ValidationRejection,
)


# ── Path-set constants (closed enums; defined locally so this module
#    does NOT import the runtime registry config) ──────────────────────────

_PATH_8_DIRECT_OK = {PathId.PATH_8_1, PathId.PATH_8_2}
"""Path 8.x sub-cases the Planner may emit directly without further
checks. Path 8.3 is conditional on multi_intent_detected (rules 2b/2c).
Path 8.4 / 8.5 are forbidden direct emissions (rule 2d) — those failure
classes only arise from a stage trigger via the Escalation Gate."""

_PATH_8_FORBIDDEN_DIRECT = {PathId.PATH_8_4, PathId.PATH_8_5}
"""Rule 2d: forbidden Path 8.x direct emissions."""

_TARGET_BOUND_PATHS = {PathId.PATH_4, PathId.PATH_5, PathId.PATH_6}
"""Rule 4: paths that require at least 1 target_candidate."""


def _utc_now() -> datetime:
    """Single source of "now" so tests can monkeypatch if they ever need to."""
    return datetime.now(timezone.utc)


def _reject(
    *,
    proposal: PlannerProposal,
    rule_number: int,
    trigger: str,
    reason_code: str,
    message_for_replan: str,
    attempt_index: int = 0,
) -> ValidationRejection:
    """Construct a ValidationRejection with the standard shape."""
    return ValidationRejection(
        rejected_proposal=proposal,
        rule_number=rule_number,
        trigger=trigger,
        reason_code=ReasonCode(reason_code),
        message_for_replan=message_for_replan,
        attempt_index=attempt_index,
        rejected_at=_utc_now(),
    )


def _accept(proposal: PlannerProposal) -> ValidatedPlannerProposal:
    """Wrap a structurally sound proposal as a validated one. Carries
    no policy decisions; only structural soundness has been confirmed."""
    return ValidatedPlannerProposal(
        proposal=proposal,
        validated_at=_utc_now(),
        replan_history=[],
    )


class PlannerValidator:
    """LLM-failure structural checks only (rules 1, 2, 2b, 2c, 2d, 3, 4, 5).

    Pure deterministic function — no Path Registry reads, no policy
    enforcement (those move to ExecutionPlanFactory rules F1..F8).
    """

    def validate(
        self, proposal: PlannerProposal
    ) -> ValidatedPlannerProposal | ValidationRejection:
        """Apply rules in order; first failure wins."""

        # Rule 1 — path is a known PathId.
        # Pydantic already enforces this at PlannerProposal validation
        # time (PathId is a closed StrEnum). Defensive re-check here so
        # any future relaxation of the type doesn't silently bypass the
        # rule.
        if not isinstance(proposal.path, PathId):
            return _reject(
                proposal=proposal,
                rule_number=1,
                trigger="invalid_planner_proposal",
                reason_code="invalid_planner_proposal",
                message_for_replan=(
                    "The proposed path is not a recognized PathId. "
                    "Use one of the known path values."
                ),
            )

        # Rule 2 — direct PATH_8_1 / PATH_8_2 pass-through.
        if proposal.path in _PATH_8_DIRECT_OK:
            return _accept(proposal)

        # Rule 2b — PATH_8_3 with multi_intent_detected=True passes through.
        # Rule 2c — PATH_8_3 with the flag missing/false is invalid.
        if proposal.path is PathId.PATH_8_3:
            if proposal.multi_intent_detected:
                return _accept(proposal)
            return _reject(
                proposal=proposal,
                rule_number=2,  # rule 2c per §2.3
                trigger="invalid_planner_proposal",
                reason_code="invalid_planner_proposal",
                message_for_replan=(
                    "Path 8.3 may only be emitted directly when "
                    "multi_intent_detected=True. If the user message "
                    "carries one intent, classify it under the appropriate "
                    "answer path (1-7) instead."
                ),
            )

        # Rule 2d — PATH_8_4 / PATH_8_5 are forbidden as direct planner
        # emissions. They can only arise from stage failure triggers
        # (access denied / no evidence / source unreachable / llm down)
        # via the Escalation Gate.
        if proposal.path in _PATH_8_FORBIDDEN_DIRECT:
            return _reject(
                proposal=proposal,
                rule_number=2,  # rule 2d per §2.3
                trigger="invalid_planner_proposal",
                reason_code="invalid_planner_proposal",
                message_for_replan=(
                    "Path 8.4 (inaccessible) and Path 8.5 (no-evidence / "
                    "source-down / llm-down) cannot be emitted directly. "
                    "Classify the turn as an answer path (1-7); the "
                    "Escalation Gate will route to 8.4 / 8.5 if a stage "
                    "fails at runtime."
                ),
            )

        # Rule 3 — intent_topic is non-empty / not pure whitespace.
        if not proposal.intent_topic.strip():
            return _reject(
                proposal=proposal,
                rule_number=3,
                trigger="unclear_intent_topic",
                reason_code="unclear_intent_topic",
                message_for_replan=(
                    "intent_topic is empty or whitespace. Provide a concrete "
                    "intent like 'deadline', 'owner', 'compare_rfqs', etc."
                ),
            )

        # Rule 4 — paths 4 / 5 / 6 require at least 1 target_candidate.
        if (
            proposal.path in _TARGET_BOUND_PATHS
            and len(proposal.target_candidates) < 1
        ):
            return _reject(
                proposal=proposal,
                rule_number=4,
                trigger="no_target_proposed",
                reason_code="no_target_proposed",
                message_for_replan=(
                    f"Path {proposal.path.value} requires at least one "
                    f"target_candidate. Extract the RFQ reference (rfq_code, "
                    f"natural reference, page default, or session-state pick)."
                ),
            )

        # Rule 5 — path 7 requires at least 2 target_candidates.
        # NEVER silently downgrade to Path 4 — always escalate to
        # clarification (8.3 comparison_missing_target via the Gate).
        if (
            proposal.path is PathId.PATH_7
            and len(proposal.target_candidates) < 2
        ):
            return _reject(
                proposal=proposal,
                rule_number=5,
                trigger="comparison_missing_target",
                reason_code="comparison_missing_target",
                message_for_replan=(
                    "Path 7 (comparison) requires at least two target_candidates. "
                    "Do not downgrade to Path 4 — ask the user to clarify which "
                    "RFQs to compare."
                ),
            )

        # All structural rules passed.
        return _accept(proposal)
