"""FastIntake behavior tests (Batch 4 — §5.0).

Verifies the deterministic anchored-full-match patterns. Defense in
depth on top of the §11.5.3 anti-drift guard:

* Hits emit IntakeDecision with the right path/intent/pattern_id.
* Operational queries (anything containing real RFQ words) MUST miss.
* "When in doubt, miss" — false-positive UX is worse than false-negative
  latency.
"""

from __future__ import annotations

import ast
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.models.intake_decision import IntakeDecision
from src.models.path_registry import PathId
from src.pipeline import fast_intake as fast_intake_module
from src.pipeline.fast_intake import try_match
from src.pipeline.fast_intake_patterns import FAST_INTAKE_PATTERNS


# ── Greeting ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "msg",
    ["hello", "Hello", "HELLO", "hi", "Hi", "hey", "Hey", "salam", "salut"],
)
def test_greeting_matches(msg: str):
    result = try_match(msg)
    assert isinstance(result, IntakeDecision)
    assert result.path is PathId.PATH_1
    assert result.intent_topic == "greeting"
    assert result.raw_message == msg


def test_greeting_with_outer_whitespace_matches():
    """ ' hello! ' (with leading/trailing space + punctuation) matches —
    we trim outer whitespace before fullmatch."""
    result = try_match(" hello! ")
    assert isinstance(result, IntakeDecision)
    assert result.path is PathId.PATH_1
    assert result.intent_topic == "greeting"
    # raw_message preserves the original (with whitespace) for forensics
    assert result.raw_message == " hello! "


def test_greeting_with_trailing_punctuation_matches():
    for msg in ["hello!", "hello.", "hi?", "hey!!"]:
        result = try_match(msg)
        assert isinstance(result, IntakeDecision), f"{msg!r} should match"
        assert result.intent_topic == "greeting"


# ── Greeting embedded in real question — must MISS ────────────────────────


@pytest.mark.parametrize(
    "msg",
    [
        "hello what is the deadline",
        "hi can you check IF-0042",
        "hey when is IF-0001 due?",
    ],
)
def test_greeting_followed_by_real_question_misses(msg: str):
    """Anchored full-match: the greeting prefix doesn't shortcut a real
    operational query. False positives here would short-circuit a real
    question into a canned greeting reply — the broken-UX failure mode."""
    assert try_match(msg) is None


# ── Thanks ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "msg",
    ["thanks", "Thanks", "THANKS", "thank you", "Thank You", "thx", "merci"],
)
def test_thanks_matches(msg: str):
    result = try_match(msg)
    assert isinstance(result, IntakeDecision)
    assert result.path is PathId.PATH_1
    assert result.intent_topic == "thanks"


def test_thanks_with_punctuation_matches():
    for msg in ["thanks!", "thank you!", "thanks."]:
        result = try_match(msg)
        assert isinstance(result, IntakeDecision), f"{msg!r} should match"
        assert result.intent_topic == "thanks"


@pytest.mark.parametrize(
    "msg",
    [
        "thanks, what is the deadline?",
        "thank you, can you also show blockers",
    ],
)
def test_thanks_followed_by_real_question_misses(msg: str):
    assert try_match(msg) is None


# ── Farewell ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "msg",
    ["bye", "Bye", "BYE", "goodbye", "Goodbye", "cya", "see you"],
)
def test_farewell_matches(msg: str):
    result = try_match(msg)
    assert isinstance(result, IntakeDecision)
    assert result.path is PathId.PATH_1
    assert result.intent_topic == "farewell"


def test_farewell_with_punctuation_matches():
    for msg in ["bye!", "goodbye!", "bye."]:
        result = try_match(msg)
        assert isinstance(result, IntakeDecision), f"{msg!r} should match"
        assert result.intent_topic == "farewell"


def test_farewell_followed_by_real_question_misses():
    assert try_match("bye, show urgent RFQs") is None


# ── Empty message ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("msg", ["", " ", "  ", "\t", "\n", " \t \n "])
def test_empty_message_matches(msg: str):
    result = try_match(msg)
    assert isinstance(result, IntakeDecision)
    assert result.path is PathId.PATH_8_3
    assert result.intent_topic == "empty_message"


# ── Out-of-scope nonsense (pure punctuation/symbols) ──────────────────────


@pytest.mark.parametrize(
    "msg",
    ["???", "!!!", "...", "///", "~~~", "?!?!", "...???", "!@#$"],
)
def test_pure_punctuation_matches_nonsense(msg: str):
    result = try_match(msg)
    assert isinstance(result, IntakeDecision)
    assert result.path is PathId.PATH_8_2
    assert result.intent_topic == "out_of_scope_nonsense"


# ── Anything else (real questions, RFQ codes, prose) MUST miss ────────────


@pytest.mark.parametrize(
    "msg",
    [
        "what is the deadline for IF-0001",
        "IF-0001",                       # RFQ code alone — Planner territory
        "show me the blockers",
        "write me a recipe",            # out-of-scope prose — Planner direct emission, NOT FastIntake
        "compare IF-0001 and IF-0042",
        "X",                            # single non-greeting letter
        "12345",                        # numbers
        "hello world",                  # not in greeting alone
    ],
)
def test_non_fast_intake_messages_miss(msg: str):
    """Anything that isn't a trivial greeting/thanks/farewell/empty/
    nonsense must miss. FastIntake never short-circuits a real query."""
    assert try_match(msg) is None


def test_write_me_a_recipe_specifically_does_not_match():
    """Spec'd explicitly. Out-of-scope prose detection belongs to the
    Planner (direct PATH_8_2 emission) in a later batch — must NOT be
    hardcoded here."""
    assert try_match("write me a recipe") is None


# ── IntakeDecision shape on hit ───────────────────────────────────────────


def test_intake_decision_carries_pattern_id_and_version():
    result = try_match("hi")
    assert isinstance(result, IntakeDecision)
    # pattern_id is a NewType over str; opaque to consumers but captured.
    assert result.pattern_id  # non-empty
    assert result.pattern_version  # non-empty version string
    assert result.matched_at.tzinfo is not None  # timezone-aware UTC


def test_injectable_now_is_used():
    """``now`` parameter is for deterministic testing — important for
    forensics fixtures that need stable timestamps."""
    fixed = datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc)
    result = try_match("hi", now=fixed)
    assert isinstance(result, IntakeDecision)
    assert result.matched_at == fixed


# ── Architectural guards (per-module fast feedback) ───────────────────────


def test_fast_intake_does_not_import_registry_config():
    """The §11.5.2 anti-drift guard already enforces this for
    src/pipeline/. Re-asserting at the per-module level so a regression
    fails this test specifically (faster signal)."""
    src_path = Path(inspect.getfile(fast_intake_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.config.path_registry":
            pytest.fail(
                f"FastIntake must not import src.config.path_registry "
                f"(line {node.lineno})."
            )


def test_fast_intake_never_emits_path_4_or_other_operational_paths():
    """Spec hard rule. Operational classification is the LLM Planner's
    job. The pattern table is reviewable in one place — assert no entry
    targets Path 2/3/4/5/6/7."""
    operational_paths = {
        PathId.PATH_2, PathId.PATH_3, PathId.PATH_4,
        PathId.PATH_5, PathId.PATH_6, PathId.PATH_7,
    }
    for pattern in FAST_INTAKE_PATTERNS:
        assert pattern.path not in operational_paths, (
            f"FastIntake pattern {pattern.pattern_id!r} targets "
            f"operational path {pattern.path}. FastIntake may only emit "
            f"Path 1 / Path 8.2 / Path 8.3 — operational classification "
            f"is the Planner's job."
        )


def test_fast_intake_always_emits_path_1_or_8_2_or_8_3():
    """Positive contract: every pattern targets one of the three
    permitted paths."""
    permitted = {PathId.PATH_1, PathId.PATH_8_2, PathId.PATH_8_3}
    for pattern in FAST_INTAKE_PATTERNS:
        assert pattern.path in permitted, (
            f"FastIntake pattern {pattern.pattern_id!r} targets {pattern.path}, "
            f"not in permitted set {permitted}."
        )
