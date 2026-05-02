"""FastIntake pattern table — versioned, code-reviewed entries.

See ``docs/11-Architecture_Frozen_v2.md`` §5.0 (Slice 1 pattern table).

Each entry maps an anchored full-match regex to a ``(path, intent_topic)``
pair the ``ExecutionPlanFactory`` is allowed to build a minimal plan for.
The ``PATTERN_VERSION`` is bumped whenever this module changes so
``IntakeDecision.pattern_version`` survives in execution_record forensics
and a regression like "this greeting started missing in v1.3" is
diagnosable from the database.

Slice 1 table (active in Batch 4):

============================================  =======  =====================
Pattern (anchored full-match)                 Path     Intent topic
============================================  =======  =====================
``^\\s*$``                                     8.3      empty_message
``^[^\\w\\s]+$``                               8.2      out_of_scope_nonsense
``^(hi|hello|hey|salam|salut)[!.?\\s]*$``      1        greeting
``^(thanks|thank you|thx|merci)[!.?\\s]*$``    1        thanks
``^(bye|goodbye|cya|see you)[!.?\\s]*$``       1        farewell
============================================  =======  =====================

CI guard §11.5.3 enforces that no pattern emits a path outside
{Path 1, Path 8.2, Path 8.3} in Slice 1.

Discipline:

* **Anchored full-match only** — ``^...$`` paired with ``re.fullmatch``.
  No substring matching, no fuzzy ranking, no token similarity.
* **Closed table** — adding a pattern requires a code review and a
  ``PATTERN_VERSION`` bump.
* **No LLM, no DB, no network.** Pure deterministic regex over the user
  message string.
* **When in doubt, miss.** False negatives cost a Planner round-trip
  (cheap). False positives short-circuit a real question into a canned
  reply (broken UX). Patterns are deliberately narrow: "hello" matches,
  "hello what is the deadline" does NOT.

Out-of-scope detection in this module is **only** for trivially safe
cases: empty input, pure punctuation/symbols. Free-form natural-language
out-of-scope ("write me a recipe") is a Planner-level direct emission
in a later batch — never hardcoded here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.models.path_registry import IntakePatternId, PathId


PATTERN_VERSION: str = "1.0.0-batch4"
"""Semver of the pattern table at intake time. Carried into IntakeDecision
so forensics can diagnose pattern-table regressions."""


@dataclass(frozen=True)
class FastIntakePattern:
    """One anchored full-match pattern entry.

    Frozen dataclass — once compiled at module load the entry is
    immutable (Pydantic overhead would be wasteful for a small fixed
    table). The ``compiled_regex`` is held as a ``re.Pattern`` so
    matching uses the prebuilt pattern, not a re-compile per call.
    """

    pattern_id: IntakePatternId
    compiled_regex: re.Pattern[str]
    path: PathId
    intent_topic: str


# Compile once at module load. ``re.IGNORECASE`` on the conversational
# patterns so "Hi", "HI", "hello", "Hello" all match. The empty-message
# and nonsense patterns don't need IGNORECASE — they match by character
# class semantics that aren't case-sensitive.

_GREETING_REGEX = re.compile(
    r"^(hi|hello|hey|salam|salut)[!.?\s]*$", re.IGNORECASE
)
_THANKS_REGEX = re.compile(
    r"^(thanks|thank you|thx|merci)[!.?\s]*$", re.IGNORECASE
)
_FAREWELL_REGEX = re.compile(
    r"^(bye|goodbye|cya|see you)[!.?\s]*$", re.IGNORECASE
)
_EMPTY_REGEX = re.compile(r"^\s*$")
_NONSENSE_REGEX = re.compile(r"^[^\w\s]+$")


# Pattern order matters for documentation / diagnostics, but the regexes
# don't overlap (empty matches whitespace-only; nonsense requires at
# least 1 non-word non-whitespace char; greetings/thanks/farewell start
# with word characters). First-match-wins is safe.

FAST_INTAKE_PATTERNS: tuple[FastIntakePattern, ...] = (
    FastIntakePattern(
        pattern_id=IntakePatternId("empty_v1"),
        compiled_regex=_EMPTY_REGEX,
        path=PathId.PATH_8_3,
        intent_topic="empty_message",
    ),
    FastIntakePattern(
        pattern_id=IntakePatternId("nonsense_punct_v1"),
        compiled_regex=_NONSENSE_REGEX,
        path=PathId.PATH_8_2,
        intent_topic="out_of_scope_nonsense",
    ),
    FastIntakePattern(
        pattern_id=IntakePatternId("greeting_v1"),
        compiled_regex=_GREETING_REGEX,
        path=PathId.PATH_1,
        intent_topic="greeting",
    ),
    FastIntakePattern(
        pattern_id=IntakePatternId("thanks_v1"),
        compiled_regex=_THANKS_REGEX,
        path=PathId.PATH_1,
        intent_topic="thanks",
    ),
    FastIntakePattern(
        pattern_id=IntakePatternId("farewell_v1"),
        compiled_regex=_FAREWELL_REGEX,
        path=PathId.PATH_1,
        intent_topic="farewell",
    ),
)
"""Slice 1 active pattern table (5 entries). All patterns use anchored
full-match semantics via ``re.fullmatch``. Adding a pattern requires
bumping ``PATTERN_VERSION`` and a code review."""
