"""Deterministic guardrail tests (Batch 7)."""

from __future__ import annotations

import ast
import inspect
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

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
from src.pipeline import guardrails as guardrails_module
from src.pipeline.errors import StageError
from src.pipeline.guardrails import (
    evidence_guardrail,
    forbidden_field_guardrail,
    internal_label_guardrail,
    known_guardrails,
    run_path_4_guardrails,
    scope_guardrail,
    shape_guardrail,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


def _path_4_plan(
    *,
    forbidden_fields: list[str] | None = None,
    active_guardrails: list[str] | None = None,
) -> TurnExecutionPlan:
    return TurnExecutionPlan(
        path=PathId.PATH_4,
        intent_topic="deadline",
        source=IntakeSource.PLANNER,
        target_candidates=[],
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        required_target_policy=TargetPolicy(min_targets=1, max_targets=1),
        allowed_evidence_tools=[],
        allowed_resolver_tools=[],
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        allowed_fields=["deadline"],
        forbidden_fields=forbidden_fields if forbidden_fields is not None else [
            "margin", "bid_amount", "internal_cost",
            "win_probability", "ranking", "winner", "estimation_quality",
        ],
        canonical_requested_fields=["deadline"],
        active_guardrails=[
            GuardrailId(g) for g in (active_guardrails or [
                "evidence", "forbidden_field", "internal_label", "scope", "shape",
            ])
        ],
        judge_policy=None,
        memory_policy=None,
        persistence_policy=PersistencePolicy(),
        finalizer_template_key="path_4.default",
    )


def _state_with_text(
    plan: TurnExecutionPlan,
    actor,
    final_text: str | None,
    *,
    with_evidence: bool = True,
) -> ExecutionState:
    state = ExecutionState(
        turn_id="t1", actor=actor, plan=plan,
        user_message="x", intake_path="planner",
    )
    if with_evidence:
        state.evidence_packets.append(EvidencePacket(
            target_id=uuid4(), target_label="IF-0001",
            fields={"deadline": date(2026, 6, 15)},
            source_refs=[SourceRef(
                source_type="manager", source_id="get_rfq_profile:IF-0001",
                fetched_at=datetime.now(timezone.utc),
            )],
        ))
    state.final_text = final_text
    state.final_path = PathId.PATH_4
    return state


# ── Registry sanity ──────────────────────────────────────────────────────


def test_known_guardrails_lists_all_five():
    assert known_guardrails() == [
        "evidence", "forbidden_field", "internal_label", "scope", "shape",
    ]


# ── evidence guardrail ──────────────────────────────────────────────────


def test_evidence_passes_with_packed_evidence(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "IF-0001 deadline is 2026-06-15.")
    evidence_guardrail(state)  # no raise


def test_evidence_fails_when_text_set_but_no_packets(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "fabricated answer", with_evidence=False)
    with pytest.raises(StageError) as exc_info:
        evidence_guardrail(state)
    err = exc_info.value
    assert err.trigger == "evidence_empty"
    assert err.reason_code == "no_evidence"
    assert err.source_stage == "guardrail"
    assert err.details["guardrail"] == "evidence"


def test_evidence_passes_silently_when_text_is_none(actor):
    """Empty final_text isn't this guardrail's job — shape catches it."""
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, None, with_evidence=False)
    evidence_guardrail(state)  # no raise


# ── forbidden_field guardrail ───────────────────────────────────────────


def test_forbidden_field_passes_normal_answer(actor):
    plan = _path_4_plan()
    state = _state_with_text(
        plan, actor, "IF-0001 deadline is 2026-06-15."
    )
    forbidden_field_guardrail(state)  # no raise


@pytest.mark.parametrize(
    "leaky_text",
    [
        "IF-0001 margin is 12.5%",
        "The win_probability for IF-0001 is high",
        "IF-0001 has a bid_amount of $1.2M",
        "estimated ranking: 2nd",
        "internal_cost is $500K",
    ],
)
def test_forbidden_field_fails_on_leak(actor, leaky_text: str):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, leaky_text)
    with pytest.raises(StageError) as exc_info:
        forbidden_field_guardrail(state)
    err = exc_info.value
    assert err.trigger == "forbidden_inference_detected_deterministic"
    assert err.details["guardrail"] == "forbidden_field"


def test_forbidden_field_case_insensitive(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "The MARGIN is 5%")
    with pytest.raises(StageError):
        forbidden_field_guardrail(state)


def test_forbidden_field_word_boundary_avoids_false_positives(actor):
    """'marginally' contains 'margin' but isn't the forbidden field name."""
    plan = _path_4_plan()
    state = _state_with_text(
        plan, actor, "IF-0001 is marginally late",  # NB: "marginally" should NOT trigger
    )
    # Word-boundary regex protects 'marginally' from matching 'margin' alone.
    forbidden_field_guardrail(state)  # no raise


def test_forbidden_field_skips_if_text_none(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, None, with_evidence=False)
    forbidden_field_guardrail(state)  # no raise


def test_forbidden_field_respects_plan_specific_list(actor):
    """If a future intent has a different forbidden list, the guardrail
    reads from plan.forbidden_fields — not a hardcoded list."""
    plan = _path_4_plan(forbidden_fields=["secret_field"])
    state = _state_with_text(plan, actor, "the secret_field is exposed")
    with pytest.raises(StageError):
        forbidden_field_guardrail(state)


# ── internal_label guardrail ────────────────────────────────────────────


def test_internal_label_passes_normal_answer(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "IF-0001 deadline is 2026-06-15.")
    internal_label_guardrail(state)  # no raise


@pytest.mark.parametrize(
    "leaky_text",
    [
        "answer is on path_4",
        "routing to PATH_8_5",
        "the reason_code was no_evidence",
        "TurnExecutionPlan failed",
        "see EvidencePacket above",
        "ExecutionPlanFactory rejected",
        "FactoryRejection: F5",
    ],
)
def test_internal_label_fails_on_leak(actor, leaky_text: str):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, leaky_text)
    with pytest.raises(StageError) as exc_info:
        internal_label_guardrail(state)
    err = exc_info.value
    assert err.trigger == "forbidden_inference_detected_deterministic"
    assert err.details["guardrail"] == "internal_label"


# ── scope guardrail ─────────────────────────────────────────────────────


def test_scope_passes_normal_answer(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "IF-0001 owner is Mohamed.")
    scope_guardrail(state)  # no raise


@pytest.mark.parametrize(
    "leaky_text",
    [
        "IF-0001 has a high win probability",
        "Bid strategy for IF-0001: aggressive",
        "Workbook readiness: 85%",
        "Cost prediction: $1.2M",
        "We should bid on IF-0001",
        "Predicted winner: IF-0001",
        "Readiness score: 7/10",
    ],
)
def test_scope_fails_on_intelligence_claim(actor, leaky_text: str):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, leaky_text)
    with pytest.raises(StageError) as exc_info:
        scope_guardrail(state)
    err = exc_info.value
    assert err.details["guardrail"] == "scope"


# ── shape guardrail ─────────────────────────────────────────────────────


def test_shape_passes_normal_answer(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "IF-0001 deadline is 2026-06-15.")
    shape_guardrail(state)  # no raise


def test_shape_fails_on_none(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, None, with_evidence=False)
    with pytest.raises(StageError):
        shape_guardrail(state)


def test_shape_fails_on_empty(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "   ")
    with pytest.raises(StageError):
        shape_guardrail(state)


def test_shape_fails_on_raw_json(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, '{"deadline": "2026-06-15"}')
    with pytest.raises(StageError):
        shape_guardrail(state)


def test_shape_fails_on_traceback(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor,
        'Traceback (most recent call last):\n  File "x.py", line 1, in <module>')
    with pytest.raises(StageError):
        shape_guardrail(state)


def test_shape_fails_on_python_repr(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor,
        "answer was <ManagerRfqDetailDto object at 0x7f8b8c0d1234>")
    with pytest.raises(StageError):
        shape_guardrail(state)


def test_shape_fails_on_excessive_length(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "X" * 5000)
    with pytest.raises(StageError):
        shape_guardrail(state)


def test_shape_fails_on_validation_error_string(actor):
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "ValidationError: missing field")
    with pytest.raises(StageError):
        shape_guardrail(state)


# ── Dispatcher ──────────────────────────────────────────────────────────


def test_dispatcher_runs_all_active_guardrails(actor):
    """Path 4 default has all 5 active. Happy-path answer passes all."""
    plan = _path_4_plan()
    state = _state_with_text(plan, actor, "IF-0001 deadline is 2026-06-15.")
    run_path_4_guardrails(state)  # no raise


def test_dispatcher_first_failure_wins(actor):
    """If multiple guardrails would fail, the first one (per
    plan.active_guardrails order) raises."""
    plan = _path_4_plan(active_guardrails=["evidence", "scope"])
    # Both guardrails would fail: no evidence + scope-leaky text.
    state = _state_with_text(
        plan, actor, "IF-0001 has a high win probability",
        with_evidence=False,
    )
    with pytest.raises(StageError) as exc_info:
        run_path_4_guardrails(state)
    # 'evidence' runs first per plan order; it should win.
    assert exc_info.value.details["guardrail"] == "evidence"


def test_dispatcher_skips_unknown_guardrail_silently(actor):
    """Future config could declare a guardrail that doesn't have a
    function yet. Defense-in-depth: don't crash; just skip."""
    plan = _path_4_plan(active_guardrails=["not_implemented_yet"])
    state = _state_with_text(plan, actor, "anything")
    run_path_4_guardrails(state)  # no raise


def test_dispatcher_only_runs_listed_guardrails(actor):
    """If plan only declares 'evidence', forbidden_field is NOT run.
    Verifies the dispatcher honors plan.active_guardrails."""
    plan = _path_4_plan(active_guardrails=["evidence"])
    state = _state_with_text(plan, actor, "the margin is 5%")  # would fail forbidden_field
    run_path_4_guardrails(state)  # but only evidence runs; passes


# ── Anti-drift AST guards ────────────────────────────────────────────────


def test_guardrails_does_not_import_registry_config():
    src_path = Path(inspect.getfile(guardrails_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.config.path_registry":
            pytest.fail(
                f"guardrails.py must not import src.config.path_registry "
                f"(line {node.lineno})."
            )


def test_guardrails_does_not_construct_turn_execution_plan():
    src_path = Path(inspect.getfile(guardrails_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "TurnExecutionPlan"
        ):
            pytest.fail(
                f"guardrails.py constructs TurnExecutionPlan at line "
                f"{node.lineno}. Only the factory may do that."
            )


def test_guardrails_does_not_import_manager_or_llm():
    src_path = Path(inspect.getfile(guardrails_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    forbidden = {
        "src.connectors.llm_connector",
        "src.connectors.manager_ms_connector",
        "openai", "anthropic", "httpx", "requests",
    }
    leaked = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top_level = node.module.split(".")[0]
            if node.module in forbidden or top_level in forbidden:
                leaked.append(node.module)
    assert not leaked, f"guardrails imports forbidden modules: {leaked}"
