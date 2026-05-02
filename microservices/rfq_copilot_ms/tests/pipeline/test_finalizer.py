"""Finalizer template-rendering tests (Batch 4).

Verifies the template-only rendering for Path 1 and Path 8.x, the
``state`` mutation contract, and the architectural guards (no LLM, no
manager, no registry-config imports, loud failure on unknown template
keys).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.models.actor import Actor
from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import ExecutionState
from src.models.path_registry import (
    AccessPolicyName,
    IntakeSource,
    PathId,
    PersistencePolicy,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
)
from src.pipeline import finalizer as finalizer_module
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.finalizer import finalize, render_template


# ── Helpers ───────────────────────────────────────────────────────────────


def _actor() -> Actor:
    return Actor(user_id="u1", display_name="User One", role="estimator")


def _make_template_only_plan(
    *,
    path: PathId,
    intent_topic: str,
    finalizer_template_key: str,
    finalizer_reason_code: ReasonCode | None = None,
    source: IntakeSource = IntakeSource.FAST_INTAKE,
) -> TurnExecutionPlan:
    """Build a template-only plan directly. We construct it manually
    here to keep these tests independent of the factory's internal
    routing — for production paths the factory builds these.

    NOTE: This direct construction would normally trip CI guard
    §11.5.1 (only the factory may instantiate TurnExecutionPlan), but
    that guard scopes its check to ``src/`` only. Tests can construct
    plans directly for fixture purposes.
    """
    return TurnExecutionPlan(
        path=path,
        intent_topic=intent_topic,
        source=source,
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
        finalizer_template_key=finalizer_template_key,
        finalizer_reason_code=finalizer_reason_code,
        model_profile=None,
    )


def _make_state(plan: TurnExecutionPlan) -> ExecutionState:
    return ExecutionState(
        turn_id="test-turn",
        actor=_actor(),
        plan=plan,
        user_message="test",
        intake_path="fast_intake",
    )


# ── Path 1 templates ──────────────────────────────────────────────────────


def test_renders_greeting():
    plan = _make_template_only_plan(
        path=PathId.PATH_1,
        intent_topic="greeting",
        finalizer_template_key="path_1.greeting",
    )
    text = render_template(plan)
    assert text  # non-empty
    assert "RFQ" in text  # invites the user toward the supported domain


def test_renders_thanks():
    plan = _make_template_only_plan(
        path=PathId.PATH_1,
        intent_topic="thanks",
        finalizer_template_key="path_1.thanks",
    )
    text = render_template(plan)
    assert "welcome" in text.lower()


def test_renders_farewell():
    plan = _make_template_only_plan(
        path=PathId.PATH_1,
        intent_topic="farewell",
        finalizer_template_key="path_1.farewell",
    )
    text = render_template(plan)
    assert "goodbye" in text.lower()


# ── Path 8.x templates ────────────────────────────────────────────────────


def test_renders_empty_message():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_3,
        intent_topic="empty_message",
        finalizer_template_key="path_8_3.empty_message",
        finalizer_reason_code=ReasonCode("empty_message"),
    )
    text = render_template(plan)
    assert "RFQ" in text or "question" in text.lower()


def test_renders_out_of_scope_nonsense():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_2,
        intent_topic="out_of_scope_nonsense",
        finalizer_template_key="path_8_2.out_of_scope_nonsense",
        finalizer_reason_code=ReasonCode("out_of_scope_nonsense"),
    )
    text = render_template(plan)
    assert "RFQ" in text or "understand" in text.lower()


def test_renders_path_8_1_unsupported():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_1,
        intent_topic="unsupported_intent",
        finalizer_template_key="path_8_1.unsupported_intent",
        finalizer_reason_code=ReasonCode("unsupported_intent"),
    )
    text = render_template(plan)
    assert text  # non-empty
    assert "can't" in text.lower() or "cannot" in text.lower() or "yet" in text.lower()


def test_renders_path_8_2_out_of_scope():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_2,
        intent_topic="out_of_scope",
        finalizer_template_key="path_8_2.out_of_scope",
        finalizer_reason_code=ReasonCode("out_of_scope"),
    )
    text = render_template(plan)
    assert "RFQ" in text or "estimation" in text.lower()


def test_renders_path_8_4_inaccessible():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_4,
        intent_topic="access_denied_explicit",
        finalizer_template_key="path_8_4.denied",
        finalizer_reason_code=ReasonCode("access_denied_explicit"),
    )
    text = render_template(plan)
    assert "access" in text.lower() or "RFQ" in text


def test_renders_path_8_5_no_evidence():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_5,
        intent_topic="no_evidence",
        finalizer_template_key="path_8_5.no_evidence",
        finalizer_reason_code=ReasonCode("no_evidence"),
    )
    text = render_template(plan)
    assert "information" in text.lower() or "answer" in text.lower()


# ── Privacy: no internal labels in user-facing answer ─────────────────────


@pytest.mark.parametrize(
    "template_key",
    [
        "path_1.greeting",
        "path_1.thanks",
        "path_1.farewell",
        "path_8_1.unsupported_intent",
        "path_8_2.out_of_scope",
        "path_8_2.out_of_scope_nonsense",
        "path_8_3.empty_message",
        "path_8_4.denied",
        "path_8_5.no_evidence",
    ],
)
def test_template_does_not_expose_internal_path_labels(template_key: str):
    """User-facing wording must not leak internal labels like 'Path 8.3'
    or 'reason_code'. Architecture trivia belongs in logs/forensics, not
    in the user reply."""
    plan = _make_template_only_plan(
        path=PathId.PATH_1,  # path doesn't matter for this test
        intent_topic="x",
        finalizer_template_key=template_key,
    )
    text = render_template(plan)
    forbidden_substrings = [
        "Path 8",
        "Path 1",
        "Path 4",
        "PATH_8",
        "PATH_1",
        "reason_code",
        "finalizer_template_key",
        "factory",
        "PlannerValidator",
        "ExecutionPlanFactory",
    ]
    for forbidden in forbidden_substrings:
        assert forbidden not in text, (
            f"Template {template_key!r} leaks internal label "
            f"{forbidden!r}: {text!r}"
        )


# ── finalize() mutates state ──────────────────────────────────────────────


def test_finalize_writes_final_text_and_path():
    plan = _make_template_only_plan(
        path=PathId.PATH_1,
        intent_topic="greeting",
        finalizer_template_key="path_1.greeting",
    )
    state = _make_state(plan)
    assert state.final_text is None
    assert state.final_path is None

    finalize(state)

    assert state.final_text is not None
    assert state.final_text  # non-empty
    assert state.final_path is PathId.PATH_1


def test_finalize_path_8_3_writes_path_8_3():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_3,
        intent_topic="empty_message",
        finalizer_template_key="path_8_3.empty_message",
        finalizer_reason_code=ReasonCode("empty_message"),
    )
    state = _make_state(plan)
    finalize(state)
    assert state.final_path is PathId.PATH_8_3


# ── Loud failure on unknown template_key ──────────────────────────────────


def test_unknown_template_key_raises_value_error():
    plan = _make_template_only_plan(
        path=PathId.PATH_1,
        intent_topic="x",
        finalizer_template_key="path_99.no_such_template",
    )
    with pytest.raises(ValueError, match="path_99.no_such_template"):
        render_template(plan)


def test_unknown_template_key_via_finalize_also_raises():
    plan = _make_template_only_plan(
        path=PathId.PATH_8_5,
        intent_topic="x",
        # Synthetic key that is intentionally not registered in
        # finalizer._TEMPLATES — exercises the "loud failure" path.
        finalizer_template_key="path_8_5.completely_unregistered_key",
    )
    state = _make_state(plan)
    with pytest.raises(ValueError):
        finalize(state)


# ── Architectural guards (per-module fast feedback) ───────────────────────


def test_finalizer_does_not_import_registry_config():
    src_path = Path(inspect.getfile(finalizer_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.config.path_registry":
            pytest.fail(
                f"Finalizer must not import src.config.path_registry "
                f"(line {node.lineno})."
            )


def test_finalizer_does_not_import_llm_or_manager():
    """Finalizer is template-only — must not pull in any LLM SDK or the
    manager connector."""
    src_path = Path(inspect.getfile(finalizer_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    forbidden = {
        "openai", "anthropic", "langchain", "httpx", "requests",
        "src.connectors.llm_connector", "src.connectors.manager_ms_connector",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top_level = node.module.split(".")[0]
            if node.module in forbidden or top_level in forbidden:
                pytest.fail(
                    f"Finalizer imports forbidden module {node.module!r} "
                    f"on line {node.lineno}."
                )


# ── End-to-end: factory-built FastIntake plan rendered by finalizer ──────


def test_full_finalize_path_for_factory_built_path_1_plan():
    """Round-trip: factory builds a Path 1 greeting plan, finalize
    renders the template into state.final_text. This is the production
    flow for FastIntake → Factory → Finalizer."""
    from datetime import datetime, timezone

    from src.models.intake_decision import IntakeDecision
    from src.models.path_registry import IntakePatternId

    decision = IntakeDecision(
        pattern_id=IntakePatternId("greeting_v1"),
        pattern_version="1.0.0-batch4",
        path=PathId.PATH_1,
        intent_topic="greeting",
        matched_at=datetime.now(timezone.utc),
        raw_message="hi",
    )
    factory = ExecutionPlanFactory()
    plan = factory.build_from_intake(decision)
    assert isinstance(plan, TurnExecutionPlan)

    state = ExecutionState(
        turn_id="t1",
        actor=_actor(),
        plan=plan,
        user_message="hi",
        intake_path="fast_intake",
    )
    finalize(state)
    assert state.final_text is not None
    assert "RFQ" in state.final_text  # the greeting template invites RFQ questions
    assert state.final_path is PathId.PATH_1
