"""PlannerValidator behavior tests (Batch 3 — §2.3).

Verifies the deterministic LLM-output structural rules:
1, 2, 2b, 2c, 2d, 3, 4, 5. The validator MUST NOT read the Path
Registry — that's enforced by the §11.5.2 anti-drift guard, but we
also assert it here at module-import scope for fast feedback.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.models.path_registry import PathId
from src.models.planner_proposal import (
    PlannerProposal,
    ProposedTarget,
    ValidatedPlannerProposal,
    ValidationRejection,
)
from src.pipeline import planner_validator as planner_validator_module
from src.pipeline.planner_validator import PlannerValidator


# ── Fixture helpers ───────────────────────────────────────────────────────


def _make_proposal(
    *,
    path: PathId = PathId.PATH_4,
    intent_topic: str = "deadline",
    confidence: float = 0.9,
    target_candidates: list[ProposedTarget] | None = None,
    multi_intent_detected: bool = False,
    classification_rationale: str = "test fixture",
) -> PlannerProposal:
    return PlannerProposal(
        path=path,
        intent_topic=intent_topic,
        confidence=confidence,
        classification_rationale=classification_rationale,
        target_candidates=target_candidates if target_candidates is not None else [],
        multi_intent_detected=multi_intent_detected,
    )


def _one_target() -> list[ProposedTarget]:
    return [ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code")]


def _two_targets() -> list[ProposedTarget]:
    return [
        ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code"),
        ProposedTarget(raw_reference="IF-0042", proposed_kind="rfq_code"),
    ]


@pytest.fixture
def validator() -> PlannerValidator:
    return PlannerValidator()


# ── 1. Accepts normal PATH_4 proposal with one target ─────────────────────


def test_accepts_normal_path_4_proposal(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_4,
        intent_topic="deadline",
        target_candidates=_one_target(),
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidatedPlannerProposal)
    assert result.proposal is proposal
    assert result.replan_history == []


# ── 2 / 2b. Accepts direct PATH_8_1, PATH_8_2 ─────────────────────────────


def test_accepts_path_8_1_direct(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_8_1, intent_topic="unsupported", confidence=0.9
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidatedPlannerProposal)


def test_accepts_path_8_2_direct(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_8_2, intent_topic="out_of_scope", confidence=0.9
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidatedPlannerProposal)


# ── 2b. Accepts PATH_8_3 only when multi_intent_detected=True ─────────────


def test_accepts_path_8_3_with_multi_intent_flag(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_8_3,
        intent_topic="multi_intent",
        confidence=0.9,
        multi_intent_detected=True,
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidatedPlannerProposal)


# ── 2c. Rejects PATH_8_3 without the multi_intent flag ────────────────────


def test_rejects_path_8_3_without_multi_intent_flag(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_8_3,
        intent_topic="anything",
        confidence=0.9,
        multi_intent_detected=False,
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.trigger == "invalid_planner_proposal"
    assert result.reason_code == "invalid_planner_proposal"
    assert result.rule_number == 2  # rule 2c


# ── 2d. Rejects PATH_8_4 / PATH_8_5 direct emissions ──────────────────────


@pytest.mark.parametrize(
    "forbidden_path", [PathId.PATH_8_4, PathId.PATH_8_5]
)
def test_rejects_forbidden_path_8_direct_emission(
    validator: PlannerValidator, forbidden_path: PathId
):
    proposal = _make_proposal(
        path=forbidden_path, intent_topic="anything", confidence=0.9
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.trigger == "invalid_planner_proposal"
    assert result.reason_code == "invalid_planner_proposal"
    assert result.rule_number == 2  # rule 2d


# ── 3. Rejects empty / whitespace intent_topic ────────────────────────────


@pytest.mark.parametrize("blank", ["", " ", "\t", "\n", "  \t \n "])
def test_rejects_empty_or_whitespace_intent_topic(
    validator: PlannerValidator, blank: str
):
    proposal = _make_proposal(
        path=PathId.PATH_4,
        intent_topic=blank,
        target_candidates=_one_target(),
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.trigger == "unclear_intent_topic"
    assert result.reason_code == "unclear_intent_topic"
    assert result.rule_number == 3


# ── 4. Rejects PATH_4 / PATH_5 / PATH_6 with no target_candidates ─────────


@pytest.mark.parametrize(
    "target_bound_path",
    [PathId.PATH_4, PathId.PATH_5, PathId.PATH_6],
)
def test_rejects_target_bound_path_with_no_targets(
    validator: PlannerValidator, target_bound_path: PathId
):
    proposal = _make_proposal(
        path=target_bound_path,
        intent_topic="some_intent",
        target_candidates=[],
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.trigger == "no_target_proposed"
    assert result.reason_code == "no_target_proposed"
    assert result.rule_number == 4


# ── 5. Rejects PATH_7 with fewer than two target_candidates ───────────────


def test_rejects_path_7_with_zero_targets(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_7, intent_topic="compare_rfqs", target_candidates=[]
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.trigger == "comparison_missing_target"
    assert result.reason_code == "comparison_missing_target"
    assert result.rule_number == 5


def test_rejects_path_7_with_one_target_never_downgrades(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_7,
        intent_topic="compare_rfqs",
        target_candidates=_one_target(),
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.trigger == "comparison_missing_target", (
        "Path 7 with 1 target must escalate to clarification — NEVER "
        "silently downgrade to Path 4."
    )
    assert result.rule_number == 5


def test_accepts_path_7_with_two_targets(validator: PlannerValidator):
    proposal = _make_proposal(
        path=PathId.PATH_7,
        intent_topic="compare_rfqs",
        target_candidates=_two_targets(),
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidatedPlannerProposal)


# ── 12. Validator does NOT import src.config.path_registry ───────────────


def test_validator_does_not_import_registry_config():
    """The §11.5.2 CI guard already enforces this for src/pipeline/. We
    re-assert it here at the per-module level so a regression fails this
    test specifically (faster signal than the directory-wide guard)."""
    src_path = Path(inspect.getfile(planner_validator_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.config.path_registry":
            pytest.fail(
                "PlannerValidator must not import src.config.path_registry. "
                "Policy enforcement belongs in ExecutionPlanFactory rules F1..F8. "
                f"Offending import on line {node.lineno}."
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "src.config.path_registry":
                    pytest.fail(
                        "PlannerValidator imports src.config.path_registry "
                        f"on line {node.lineno}."
                    )


# ── ValidationRejection record shape ──────────────────────────────────────


def test_rejection_has_required_forensic_fields(validator: PlannerValidator):
    """Every rejection must carry enough context for forensics:
    rejected_proposal, rule_number, trigger, reason_code,
    message_for_replan, attempt_index, rejected_at."""
    proposal = _make_proposal(
        path=PathId.PATH_4, intent_topic="", target_candidates=_one_target()
    )
    result = validator.validate(proposal)
    assert isinstance(result, ValidationRejection)
    assert result.rejected_proposal is proposal
    assert result.message_for_replan  # non-empty
    assert result.attempt_index == 0
    assert result.rejected_at is not None
