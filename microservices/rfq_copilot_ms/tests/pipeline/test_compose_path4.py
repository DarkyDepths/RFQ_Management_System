"""Compose stage tests (Batch 8).

Verify ``src/pipeline/compose.py::compose_path_4`` in isolation:

* Happy path — composes draft from evidence; sets ``state.draft_text``.
* LLM unreachable -> StageError llm_unavailable.
* Malformed JSON -> StageError llm_unavailable (treated as effective
  LLM failure; the model didn't deliver a usable answer).
* Empty draft_text -> StageError llm_unavailable.
* Schema mismatch (extra fields rejected) -> StageError llm_unavailable.
* Wrong path -> StageError invalid_planner_proposal (defense in depth).
* Empty evidence_packets -> StageError no_evidence (defense in depth;
  EvidenceCheck should have caught it).
* JSON wrapped in ```json fences -> tolerated.
* Prompt structure — system + user with EVIDENCE FIELDS section.
* Sets state.draft_text NOT state.final_text (orchestrator promotes).
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
from src.models.path_registry import (
    AccessPolicyName,
    GuardrailId,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ResolverStrategy,
    TargetPolicy,
)
from src.pipeline.compose import compose_path_4
from src.pipeline.errors import StageError
from tests.conftest import FakeLlmConnector


# ── Fixtures ─────────────────────────────────────────────────────────────


def _path_4_plan(*, intent_topic: str = "summary") -> TurnExecutionPlan:
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic=intent_topic,
        source=IntakeSource.PLANNER,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[],
        allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=["name", "client", "status", "deadline", "priority"],
        forbidden_fields=["margin", "win_probability"],
        canonical_requested_fields=["name", "client", "deadline"],
        active_guardrails=[GuardrailId("evidence")],
        judge_policy=None,
        memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
    )


def _state_with_evidence(plan: TurnExecutionPlan, actor: Actor) -> ExecutionState:
    state = ExecutionState(
        turn_id="t-compose",
        actor=actor,
        plan=plan,
        user_message="Give me a summary of IF-0001",
        intake_path="planner",
    )
    state.evidence_packets.append(EvidencePacket(
        target_id=uuid4(),
        target_label="IF-0001",
        fields={
            "name": "Refinery Upgrade",
            "client": "ACME Energy",
            "deadline": date(2026, 8, 1),
            "priority": "Critical",
        },
        source_refs=[SourceRef(
            source_type="manager",
            source_id="get_rfq_profile:IF-0001",
            fetched_at=datetime.now(timezone.utc),
        )],
    ))
    return state


# ── Happy path ───────────────────────────────────────────────────────────


def test_compose_happy_path_sets_draft_text(actor):
    plan = _path_4_plan(intent_topic="summary")
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({
        "draft_text": "IF-0001 (Refinery Upgrade) for ACME Energy is Critical priority, due 2026-08-01.",
        "used_source_refs": ["get_rfq_profile:IF-0001"],
    }))
    compose_path_4(state, llm)
    assert state.draft_text is not None
    assert "IF-0001" in state.draft_text
    assert state.final_text is None  # compose never promotes


def test_compose_uses_evidence_fields_in_user_prompt(actor):
    plan = _path_4_plan(intent_topic="summary")
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({"draft_text": "ok", "used_source_refs": []}))
    compose_path_4(state, llm)
    assert len(llm.calls) == 1
    user_msg = llm.calls[0]["messages"][1]["content"]
    assert "EVIDENCE FIELDS" in user_msg
    assert "IF-0001" in user_msg
    assert "Refinery Upgrade" in user_msg
    assert "ACME Energy" in user_msg


def test_compose_tolerates_json_fences(actor):
    plan = _path_4_plan()
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response("```json\n" + json.dumps({
        "draft_text": "fenced answer",
        "used_source_refs": [],
    }) + "\n```")
    compose_path_4(state, llm)
    assert state.draft_text == "fenced answer"


# ── Failure modes ────────────────────────────────────────────────────────


def test_compose_llm_unreachable_raises_stage_error(actor):
    plan = _path_4_plan()
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    llm.set_unreachable()
    with pytest.raises(StageError) as exc_info:
        compose_path_4(state, llm)
    err = exc_info.value
    assert err.trigger == "llm_unavailable"
    assert str(err.reason_code) == "llm_unavailable"
    assert err.source_stage == "compose"


def test_compose_malformed_json_raises_stage_error(actor):
    plan = _path_4_plan()
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response("not valid json at all")
    with pytest.raises(StageError) as exc_info:
        compose_path_4(state, llm)
    err = exc_info.value
    assert err.trigger == "llm_unavailable"
    assert err.source_stage == "compose"


def test_compose_empty_draft_text_raises_stage_error(actor):
    plan = _path_4_plan()
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({"draft_text": "   ", "used_source_refs": []}))
    with pytest.raises(StageError) as exc_info:
        compose_path_4(state, llm)
    assert exc_info.value.trigger == "llm_unavailable"


def test_compose_schema_mismatch_raises_stage_error(actor):
    plan = _path_4_plan()
    state = _state_with_evidence(plan, actor)
    llm = FakeLlmConnector()
    # extra="forbid" on ComposeOutput rejects unknown fields.
    llm.set_response(json.dumps({
        "draft_text": "ok",
        "used_source_refs": [],
        "secret_chain_of_thought": "here is what I really think",
    }))
    with pytest.raises(StageError) as exc_info:
        compose_path_4(state, llm)
    assert exc_info.value.trigger == "llm_unavailable"


def test_compose_rejects_non_path_4(actor):
    # Construct a plan with intent set on path_4 then mutate via factory
    # not possible (frozen). Instead build a plan that says path_4 but
    # we'll force the wrong path by building a fresh plan with PATH_8_5.
    # Simpler: build a path_4 plan and assert the path matches; then
    # use the inverse — build a plan that's path_4 and confirm the
    # path-guard runs on a manufactured non-path_4 plan via direct call.
    plan = TurnExecutionPlan(
        path=PathId.PATH_8_5,
        intent_topic="summary",
        source=IntakeSource.ESCALATION,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.NONE,
        required_target_policy=TargetPolicy.none(),
        allowed_evidence_tools=[],
        allowed_resolver_tools=[],
        access_policy=AccessPolicyName.NONE,
        allowed_fields=[],
        forbidden_fields=[],
        canonical_requested_fields=[],
        active_guardrails=[],
        judge_policy=None,
        memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_8_5.no_evidence",
    )
    state = ExecutionState(
        turn_id="t-x", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    state.evidence_packets.append(EvidencePacket(
        target_id=uuid4(), target_label="IF-0001",
        fields={"deadline": date(2026, 8, 1)},
        source_refs=[],
    ))
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({"draft_text": "x", "used_source_refs": []}))
    with pytest.raises(StageError) as exc_info:
        compose_path_4(state, llm)
    assert exc_info.value.trigger == "invalid_planner_proposal"


def test_compose_no_evidence_raises_stage_error(actor):
    plan = _path_4_plan()
    state = ExecutionState(
        turn_id="t-x", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    # No evidence_packets appended.
    llm = FakeLlmConnector()
    llm.set_response(json.dumps({"draft_text": "x", "used_source_refs": []}))
    with pytest.raises(StageError) as exc_info:
        compose_path_4(state, llm)
    err = exc_info.value
    assert err.trigger == "evidence_empty"
    assert str(err.reason_code) == "no_evidence"
    assert err.source_stage == "compose"


def test_compose_does_not_call_llm_when_pre_check_fails(actor):
    """No evidence -> raise BEFORE the LLM is called (cost protection)."""
    plan = _path_4_plan()
    state = ExecutionState(
        turn_id="t-x", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    llm = FakeLlmConnector()
    # Don't queue a response. If the stage calls .complete, the fake
    # raises AssertionError. The StageError should fire first.
    with pytest.raises(StageError):
        compose_path_4(state, llm)
    assert llm.calls == []
