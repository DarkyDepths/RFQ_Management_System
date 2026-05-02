"""Contract tests — PlannerProposal + ValidatedPlannerProposal +
ValidationRejection + ProposedTarget (§2.1, §2.4, §14.3).

These tests enforce the type-system half of the architectural commitment
"the LLM produces language; code produces truth": ``PlannerProposal``
rejects every policy field it might try to smuggle in.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.path_registry import PathId, ReasonCode
from src.models.planner_proposal import (
    PlannerProposal,
    ProposedTarget,
    ValidatedPlannerProposal,
    ValidationRejection,
)


# ── ProposedTarget ─────────────────────────────────────────────────────────


def test_proposed_target_accepts_all_known_kinds():
    for kind in ("rfq_code", "natural_reference", "page_default", "session_state_pick"):
        t = ProposedTarget(raw_reference="x", proposed_kind=kind)  # type: ignore[arg-type]
        assert t.proposed_kind == kind


def test_proposed_target_rejects_unknown_kind():
    """``proposed_kind`` is a closed Literal — a hallucinated kind
    name is rejected at validation."""
    with pytest.raises(ValidationError):
        ProposedTarget(raw_reference="x", proposed_kind="invented_kind")  # type: ignore[arg-type]


def test_proposed_target_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="extra"):
        ProposedTarget(  # type: ignore[call-arg]
            raw_reference="IF-0001",
            proposed_kind="rfq_code",
            extra_attr="leak",
        )


# ── PlannerProposal — minimal valid shape ──────────────────────────────────


def _minimal_proposal_kwargs():
    return dict(
        path=PathId.PATH_4,
        intent_topic="deadline",
        confidence=0.9,
        classification_rationale="The user asked about IF-0001's deadline.",
    )


def test_planner_proposal_minimal_valid():
    p = PlannerProposal(**_minimal_proposal_kwargs())
    assert p.path is PathId.PATH_4
    assert p.target_candidates == []
    assert p.requested_fields == []
    assert p.multi_intent_detected is False
    assert p.filters is None


# ── confidence boundary ────────────────────────────────────────────────────


@pytest.mark.parametrize("good", [0.0, 0.001, 0.5, 0.999, 1.0])
def test_planner_proposal_confidence_accepts_in_range(good: float):
    p = PlannerProposal(**_minimal_proposal_kwargs() | {"confidence": good})
    assert p.confidence == good


@pytest.mark.parametrize("bad", [-0.01, -1.0, 1.01, 2.0, 100.0])
def test_planner_proposal_confidence_rejects_out_of_range(bad: float):
    with pytest.raises(ValidationError, match="confidence"):
        PlannerProposal(**_minimal_proposal_kwargs() | {"confidence": bad})


# ── Forbidden policy fields (load-bearing assertions) ─────────────────────

# Each entry below is a field the LLM must NEVER decide. Pydantic
# extra="forbid" catches all of them at validation. If any test here
# starts passing the construction, the architectural commitment that
# "the LLM produces language; code produces truth" has been broken.

_FORBIDDEN_POLICY_FIELDS = [
    ("evidence_tools", ["get_rfq_profile"]),
    ("judge_triggers", ["answer_makes_factual_claim"]),
    ("guardrails", ["evidence", "scope"]),
    ("memory_policy", {"working_pairs": 5}),
    ("persistence_policy", {"store_user_msg": True}),
    ("resolved_targets", [{"rfq_id": "00000000-0000-0000-0000-000000000001"}]),
    ("access_decisions", [{"granted": True}]),
    ("allowed_fields", ["deadline"]),
    ("forbidden_fields", ["margin"]),
    ("finalizer_template_key", "path_4_default"),
]


@pytest.mark.parametrize("field_name,value", _FORBIDDEN_POLICY_FIELDS)
def test_planner_proposal_rejects_forbidden_policy_field(field_name: str, value):
    """The LLM is forbidden from emitting any policy field. Each of
    these is owned by Path Registry / ExecutionPlanFactory / Resolver /
    Access / ExecutionState — never by the Planner."""
    bad = _minimal_proposal_kwargs() | {field_name: value}
    with pytest.raises(ValidationError, match="extra"):
        PlannerProposal(**bad)


# ── Allowed Path-3 query slots ─────────────────────────────────────────────


def test_planner_proposal_accepts_path_3_query_slots():
    """Path 3 portfolio queries carry structured slots (filters,
    output_shape, sort, limit) on the proposal. The factory rule F8
    enforces required-slot presence later — but the type system must
    accept the slots here."""
    p = PlannerProposal(
        path=PathId.PATH_3,
        intent_topic="portfolio_search",
        confidence=0.8,
        classification_rationale="search asked",
        filters={"status": "in_progress"},
        output_shape="list",
        sort="deadline_asc",
        limit=10,
    )
    assert p.filters == {"status": "in_progress"}
    assert p.output_shape == "list"


# ── ValidatedPlannerProposal ───────────────────────────────────────────────


def test_validated_planner_proposal_wraps_planner_proposal():
    inner = PlannerProposal(**_minimal_proposal_kwargs())
    validated = ValidatedPlannerProposal(
        proposal=inner,
        validated_at=datetime(2026, 5, 2, 12, 0, 0),
    )
    assert validated.proposal is inner
    assert validated.replan_history == []


def test_validated_planner_proposal_rejects_unknown_fields():
    inner = PlannerProposal(**_minimal_proposal_kwargs())
    with pytest.raises(ValidationError, match="extra"):
        ValidatedPlannerProposal(  # type: ignore[call-arg]
            proposal=inner,
            validated_at=datetime(2026, 5, 2, 12, 0, 0),
            policy_decision="leaked",
        )


# ── ValidationRejection ────────────────────────────────────────────────────


def test_validation_rejection_construction():
    rej = ValidationRejection(
        rejected_proposal=PlannerProposal(**_minimal_proposal_kwargs()),
        rule_number=4,
        trigger="no_target_proposed",
        reason_code=ReasonCode("no_target_proposed"),
        message_for_replan="You proposed Path 4 without a target.",
        attempt_index=0,
        rejected_at=datetime(2026, 5, 2, 12, 0, 0),
    )
    assert rej.rule_number == 4
    assert rej.attempt_index == 0


def test_planner_proposal_is_frozen():
    p = PlannerProposal(**_minimal_proposal_kwargs())
    with pytest.raises(ValidationError):
        p.intent_topic = "different"  # type: ignore[misc]
