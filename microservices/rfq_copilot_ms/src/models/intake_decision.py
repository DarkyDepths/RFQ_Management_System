"""IntakeDecision — FastIntake output type (§2.6, §14.3).

See ``docs/11-Architecture_Frozen_v2.md`` §2.6 (semantics) and §14.3
(authoritative type contract).

Emitted by the deterministic FastIntake stage (§5.0) when an anchored
full-match pattern hits. **Trusted as a classification request, but
never executable on its own** — the ``ExecutionPlanFactory`` still
constructs the ``TurnExecutionPlan`` from it (rule F2 verifies the
matched pattern's ``(path, intent_topic)`` declares
``IntakeSource.FAST_INTAKE`` in ``allowed_intake_sources``).

``pattern_version`` is critical: it carries the semver of the pattern
table at intake time so a regression like "this greeting started
missing in v1.3" stays diagnosable from execution_record forensics.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.path_registry import IntakePatternId, PathId


class IntakeDecision(BaseModel):
    """FastIntake output. Frozen + extra-forbid: no policy data, no
    runtime outcomes — just the classification request.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pattern_id: IntakePatternId
    pattern_version: str
    path: PathId
    intent_topic: str
    matched_at: datetime
    raw_message: str
