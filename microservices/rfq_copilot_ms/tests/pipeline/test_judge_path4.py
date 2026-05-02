"""Judge stage tests (Batch 8).

Verify ``src/pipeline/judge.py::judge_path_4`` in isolation:

* Verdict pass -> sets ``state.judge_verdict``; no raise.
* Verdict fail (each of 5 violation triggers) -> StageError with
  the routed reason_code (matches gate's _TRIGGER_TO_PATH map).
* Multiple violations -> first violation drives routing; all
  recorded on state.judge_verdict for forensics.
* Verdict fail with no violations -> treated as fabrication.
* Unknown trigger from LLM -> normalized to fabrication (fail closed).
* Malformed JSON / invalid verdict value -> fabrication (fail closed —
  refuse to trust an unparseable verdict).
* LLM unreachable -> StageError llm_unavailable.
* Pre-conditions: no draft_text -> raise; no evidence -> raise.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import (
    EvidencePacket,
    ExecutionState,
    SourceRef,
)
from src.models.judge import JUDGE_TRIGGER_TO_REASON_CODE
from src.models.path_registry import (
    AccessPolicyName,
    GuardrailId,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ResolverStrategy,
    TargetPolicy,
)
from src.pipeline.errors import StageError
from src.pipeline.judge import judge_path_4
from tests.conftest import FakeLlmConnector


# ── Fixtures ─────────────────────────────────────────────────────────────


def _path_4_plan() -> TurnExecutionPlan:
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic="summary",
        source=IntakeSource.PLANNER,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[],
        allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=["name", "client", "deadline"],
        forbidden_fields=["margin", "win_probability"],
        canonical_requested_fields=["name", "client", "deadline"],
        active_guardrails=[GuardrailId("evidence")],
        judge_policy=None,
        memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
    )


def _state_with_draft(plan: TurnExecutionPlan, actor: Actor) -> ExecutionState:
    state = ExecutionState(
        turn_id="t-judge",
        actor=actor,
        plan=plan,
        user_message="summary IF-0001",
        intake_path="planner",
    )
    state.evidence_packets.append(EvidencePacket(
        target_id=uuid4(),
        target_label="IF-0001",
        fields={
            "name": "Refinery Upgrade",
            "client": "ACME Energy",
            "deadline": date(2026, 8, 1),
        },
        source_refs=[SourceRef(
            source_type="manager",
            source_id="get_rfq_profile:IF-0001",
            fetched_at=datetime.now(timezone.utc),
        )],
    ))
    state.draft_text = (
        "IF-0001 (Refinery Upgrade) for ACME Energy is due 2026-08-01."
    )
    return state


# ── Pass path ────────────────────────────────────────────────────────────


def test_judge_pass_sets_verdict(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "verdict": "pass",
        "violations": [],
        "rationale": "draft is grounded in evidence",
    }))
    judge_path_4(state, llm)
    assert state.judge_verdict is not None
    assert state.judge_verdict.verdict == "pass"
    assert state.judge_verdict.violations == []


# ── Fail paths — one per violation trigger ──────────────────────────────


@pytest.mark.parametrize("trigger,expected_reason_code", [
    ("fabrication", "judge_verdict_fabrication"),
    ("forbidden_inference", "judge_verdict_forbidden_inference"),
    ("unsourced_citation", "judge_verdict_unsourced_citation"),
    ("target_isolation", "target_isolation_violation"),
    ("comparison_violation", "judge_verdict_comparison_violation"),
])
def test_judge_fail_routes_each_trigger_to_correct_reason_code(
    actor, trigger: str, expected_reason_code: str,
):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "verdict": "fail",
        "violations": [{"trigger": trigger, "excerpt": "bad phrase"}],
        "rationale": f"draft contains {trigger}",
    }))
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    err = exc_info.value
    # Trigger uses the reason_code value so the gate's _TRIGGER_TO_PATH
    # map routes correctly to Path 8.5.
    assert err.trigger == expected_reason_code
    assert str(err.reason_code) == expected_reason_code
    assert err.source_stage == "judge"
    # Verdict still recorded on state for forensics.
    assert state.judge_verdict is not None
    assert state.judge_verdict.verdict == "fail"
    assert len(state.judge_verdict.violations) == 1


def test_judge_first_violation_drives_routing_with_multiple(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "verdict": "fail",
        "violations": [
            {"trigger": "fabrication", "excerpt": "fake date"},
            {"trigger": "forbidden_inference", "excerpt": "high readiness"},
        ],
        "rationale": "two issues",
    }))
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "judge_verdict_fabrication"
    # Both violations recorded on state for forensics.
    assert len(state.judge_verdict.violations) == 2


def test_judge_unknown_trigger_normalized_to_fabrication(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "verdict": "fail",
        "violations": [{"trigger": "made_up_trigger", "excerpt": "x"}],
        "rationale": "x",
    }))
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    # Unknown trigger -> fabrication (fail closed).
    assert exc_info.value.trigger == "judge_verdict_fabrication"


def test_judge_fail_with_no_violations_treated_as_fabrication(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "verdict": "fail",
        "violations": [],
        "rationale": "vibes",
    }))
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "judge_verdict_fabrication"


# ── Malformed / fail-closed paths ────────────────────────────────────────


def test_judge_malformed_json_fails_closed(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response("not valid json at all")
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "judge_verdict_fabrication"


def test_judge_invalid_verdict_value_fails_closed(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "verdict": "maybe",
        "violations": [],
        "rationale": "uncertain",
    }))
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "judge_verdict_fabrication"


# ── LLM unreachable ─────────────────────────────────────────────────────


def test_judge_llm_unreachable_routes_to_llm_unavailable(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    llm = FakeLlmConnector()
    llm.set_unreachable()
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "llm_unavailable"
    assert exc_info.value.source_stage == "judge"


# ── Pre-conditions ──────────────────────────────────────────────────────


def test_judge_no_draft_text_raises(actor):
    plan = _path_4_plan()
    state = _state_with_draft(plan, actor)
    state.draft_text = None
    llm = FakeLlmConnector()
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "llm_unavailable"
    assert llm.calls == []  # short-circuit before LLM call


def test_judge_no_evidence_raises(actor):
    plan = _path_4_plan()
    state = ExecutionState(
        turn_id="t-judge", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    state.draft_text = "some draft"
    # No evidence packets.
    llm = FakeLlmConnector()
    with pytest.raises(StageError) as exc_info:
        judge_path_4(state, llm)
    assert exc_info.value.trigger == "evidence_empty"
    assert llm.calls == []


# ── Reason-code-mapping integrity ────────────────────────────────────────


def test_judge_trigger_to_reason_code_covers_all_5():
    """Sanity: the JUDGE_TRIGGER_TO_REASON_CODE map covers exactly the
    5 triggers the system prompt advertises, and all map values are
    present in the gate's routing table (asserted indirectly above)."""
    assert set(JUDGE_TRIGGER_TO_REASON_CODE.keys()) == {
        "fabrication",
        "forbidden_inference",
        "unsourced_citation",
        "target_isolation",
        "comparison_violation",
    }
