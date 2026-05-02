"""FastIntake pattern table — versioned, code-reviewed entries.

See ``docs/11-Architecture_Frozen_v2.md`` §5.0 (Slice 1 pattern table).

Each entry maps an anchored full-match regex to a ``(path, intent_topic)``
pair the ``ExecutionPlanFactory`` is allowed to build a minimal plan for.
The ``pattern_version`` is bumped whenever this module changes so
``IntakeDecision.pattern_version`` survives in execution_record forensics
and a regression like "this greeting started missing in v1.3" is
diagnosable from the database.

Slice 1 target table (do not implement in Batch 0):

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

Batch 0 status: STUB ONLY. Empty pattern table.
"""

from __future__ import annotations


PATTERN_VERSION: str = "0.0.0-batch0-scaffold"
"""Semver of the pattern table at intake time. Carried into IntakeDecision
so forensics can diagnose pattern-table regressions."""


FAST_INTAKE_PATTERNS: list = []
"""Slice 1 will populate this with anchored full-match regex entries.

Each future entry is expected to expose at least:
``pattern_id``, ``compiled_regex`` (with ``re.fullmatch`` semantics),
``path`` (PathId), and ``intent_topic`` (str).
"""
