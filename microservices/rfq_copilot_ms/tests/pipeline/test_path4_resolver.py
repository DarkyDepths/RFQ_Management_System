"""Path 4 Resolver tests (Batch 5)."""

from __future__ import annotations

import pytest

from src.models.planner_proposal import ProposedTarget
from src.pipeline.errors import StageError
from src.pipeline.resolver import resolve_path_4_target


def test_explicit_rfq_code_resolves():
    candidates = [ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code")]
    target = resolve_path_4_target(target_candidates=candidates, current_rfq_code=None)
    assert target.rfq_code == "IF-0001"
    assert target.resolution_method == "search_by_code"


def test_page_default_uses_current_rfq_code():
    candidates = [ProposedTarget(raw_reference="", proposed_kind="page_default")]
    target = resolve_path_4_target(
        target_candidates=candidates, current_rfq_code="IF-0042"
    )
    assert target.rfq_code == "IF-0042"
    assert target.resolution_method == "page_default"


def test_empty_candidates_with_page_context_falls_back_to_page_default():
    target = resolve_path_4_target(
        target_candidates=[], current_rfq_code="IF-0099"
    )
    assert target.rfq_code == "IF-0099"
    assert target.resolution_method == "page_default"


def test_no_target_and_no_page_context_triggers_8_3():
    with pytest.raises(StageError) as exc_info:
        resolve_path_4_target(target_candidates=[], current_rfq_code=None)
    err = exc_info.value
    assert err.trigger == "no_target_proposed"
    assert err.source_stage == "resolver"


def test_explicit_code_takes_precedence_over_page_default():
    candidates = [
        ProposedTarget(raw_reference="IF-0001", proposed_kind="rfq_code"),
        ProposedTarget(raw_reference="", proposed_kind="page_default"),
    ]
    target = resolve_path_4_target(
        target_candidates=candidates, current_rfq_code="IF-0042"
    )
    assert target.rfq_code == "IF-0001"


def test_page_default_without_page_context_triggers_8_3():
    candidates = [ProposedTarget(raw_reference="", proposed_kind="page_default")]
    with pytest.raises(StageError):
        resolve_path_4_target(target_candidates=candidates, current_rfq_code=None)
