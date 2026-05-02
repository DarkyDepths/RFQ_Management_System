"""Contract tests — IntakeDecision (§2.6, §14.3)."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.intake_decision import IntakeDecision
from src.models.path_registry import IntakePatternId, PathId


def _valid_kwargs():
    return dict(
        pattern_id=IntakePatternId("greeting_v1"),
        pattern_version="1.0.0",
        path=PathId.PATH_1,
        intent_topic="greeting",
        matched_at=datetime(2026, 5, 2, 12, 0, 0),
        raw_message="hi",
    )


def test_valid_intake_decision_roundtrip():
    d = IntakeDecision(**_valid_kwargs())
    assert d.path is PathId.PATH_1
    assert d.intent_topic == "greeting"
    assert d.pattern_version == "1.0.0"


def test_intake_decision_rejects_unknown_fields():
    """``extra="forbid"`` — no smuggling extra fields into a FastIntake
    output. Adding e.g. ``confidence`` would be a category error
    (FastIntake is deterministic regex, not probabilistic)."""
    bad = _valid_kwargs() | {"confidence": 0.95}
    with pytest.raises(ValidationError, match="extra"):
        IntakeDecision(**bad)


def test_intake_decision_pattern_version_required():
    """``pattern_version`` is mandatory — drives execution_record
    forensics (diagnose pattern-table regressions)."""
    bad = _valid_kwargs()
    del bad["pattern_version"]
    with pytest.raises(ValidationError):
        IntakeDecision(**bad)


def test_intake_decision_raw_message_required():
    bad = _valid_kwargs()
    del bad["raw_message"]
    with pytest.raises(ValidationError):
        IntakeDecision(**bad)


def test_intake_decision_is_frozen():
    d = IntakeDecision(**_valid_kwargs())
    with pytest.raises(ValidationError):
        d.intent_topic = "different"  # type: ignore[misc]
