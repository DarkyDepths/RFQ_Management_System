"""Planner tests (Batch 5)."""

from __future__ import annotations

import pytest

from src.pipeline.planner import Planner
from src.models.path_registry import PathId
from src.models.planner_proposal import PlannerProposal
from src.utils.errors import LlmUnreachable
from tests.conftest import FakeLlmConnector, planner_proposal_json


def test_fake_llm_response_parses_into_planner_proposal(fake_llm: FakeLlmConnector):
    fake_llm.set_response(planner_proposal_json(
        path="path_4", intent_topic="deadline", confidence=0.9,
    ))
    p = Planner(llm_connector=fake_llm).classify(user_message="when due IF-0001?")
    assert isinstance(p, PlannerProposal)
    assert p.path is PathId.PATH_4
    assert p.intent_topic == "deadline"


def test_planner_rejects_malformed_json(fake_llm: FakeLlmConnector):
    fake_llm.set_response("this is not json")
    with pytest.raises(LlmUnreachable, match="malformed JSON"):
        Planner(llm_connector=fake_llm).classify(user_message="x")


def test_planner_rejects_invalid_schema(fake_llm: FakeLlmConnector):
    fake_llm.set_response('{"path": "not_a_real_path", "intent_topic": "x"}')
    with pytest.raises(LlmUnreachable, match="schema"):
        Planner(llm_connector=fake_llm).classify(user_message="x")


def test_planner_strips_code_fences(fake_llm: FakeLlmConnector):
    """Planner tolerates models that wrap output in ```json fences despite instruction."""
    inner = planner_proposal_json(path="path_4", intent_topic="deadline")
    fake_llm.set_response(f"```json\n{inner}\n```")
    p = Planner(llm_connector=fake_llm).classify(user_message="x")
    assert p.path is PathId.PATH_4


def test_planner_can_emit_path_8_2_out_of_scope(fake_llm: FakeLlmConnector):
    fake_llm.set_response(planner_proposal_json(
        path="path_8_2", intent_topic="out_of_scope",
        target_candidates=[], confidence=0.95,
    ))
    p = Planner(llm_connector=fake_llm).classify(user_message="write me a recipe")
    assert p.path is PathId.PATH_8_2


def test_planner_unavailable_raises(fake_llm: FakeLlmConnector):
    fake_llm.set_unreachable()
    with pytest.raises(LlmUnreachable):
        Planner(llm_connector=fake_llm).classify(user_message="x")


def test_planner_includes_page_context_in_system_prompt(fake_llm: FakeLlmConnector):
    fake_llm.set_response(planner_proposal_json(path="path_4"))
    Planner(llm_connector=fake_llm).classify(
        user_message="what is the deadline?",
        current_rfq_code="IF-0001",
    )
    # System prompt mentions the current RFQ
    sys_msg = fake_llm.calls[0]["messages"][0]
    assert sys_msg["role"] == "system"
    assert "IF-0001" in sys_msg["content"]


def test_planner_prompt_does_not_ask_llm_to_pick_tools(fake_llm: FakeLlmConnector):
    """The planner system prompt MUST NOT instruct the LLM to choose tools."""
    fake_llm.set_response(planner_proposal_json(path="path_4"))
    Planner(llm_connector=fake_llm).classify(user_message="x")
    sys_msg = fake_llm.calls[0]["messages"][0]["content"]
    # Forbidden words / phrases
    assert "DO NOT pick tools" in sys_msg or "do not pick tools" in sys_msg.lower()


def test_no_real_azure_call_in_test():
    """Sanity: a Planner constructed with FakeLlmConnector never reaches
    Azure. The fake records every call locally."""
    fake = FakeLlmConnector()
    fake.set_response(planner_proposal_json())
    Planner(llm_connector=fake).classify(user_message="x")
    assert len(fake.calls) == 1
