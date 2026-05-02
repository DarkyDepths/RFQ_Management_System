"""IntakeDecision — FastIntake output type (§2.6, §14.3).

See ``docs/11-Architecture_Frozen_v2.md`` §2.6 (semantics) and §14.3
(authoritative type contract).

Emitted by the deterministic FastIntake stage (§5.0) when an anchored
full-match pattern hits. Trusted as a *classification request* but
**never executable on its own** — the ``ExecutionPlanFactory`` still
constructs the ``TurnExecutionPlan`` from it (rule F2 verifies the
matched pattern's ``(path, intent_topic)`` declares
``IntakeSource.FAST_INTAKE`` in ``allowed_intake_sources``).

Shape (per §14.3):

* ``pattern_id: IntakePatternId`` — which compiled pattern matched.
* ``pattern_version: str`` — semver of the pattern table at intake
  time. Survives in ``execution_records`` for forensics so a regression
  ("this greeting started missing in v1.3") is diagnosable from the
  database.
* ``path: PathId`` — the path the pattern declares (PATH_1, PATH_8_2,
  or PATH_8_3 in Slice 1).
* ``intent_topic: str`` — e.g. "greeting", "thanks", "farewell",
  "out_of_scope_nonsense", "empty_message".
* ``matched_at: datetime``.
* ``raw_message: str`` — exact user message that matched (forensics).

Batch 0 status: STUB ONLY. Pydantic body lands in Slice 1.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future shape (illustrative — do not import yet):
#
#   from datetime import datetime
#   from pydantic import BaseModel
#   from src.models.path_registry import PathId, IntakePatternId
#
#   class IntakeDecision(BaseModel):
#       pattern_id: IntakePatternId
#       pattern_version: str
#       path: PathId
#       intent_topic: str
#       matched_at: datetime
#       raw_message: str
