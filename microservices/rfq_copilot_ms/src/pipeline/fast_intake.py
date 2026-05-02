"""FastIntake — Stage 0 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5.0 and §2.6.

Anchored full-match regex matcher that short-circuits trivial messages
(greetings, thanks, farewells, empty input, pure punctuation) before the
GPT-4o Planner runs. On a hit, emits an ``IntakeDecision`` (see
``src/models/intake_decision.py``). On a miss, returns ``None`` and the
orchestrator falls through to the Planner. FastIntake never raises,
never blocks.

Hard discipline (CI-enforced — §11.5.3 + §11.3):

* **Anchored full-match only** (``re.fullmatch`` via the precompiled
  patterns in :mod:`src.pipeline.fast_intake_patterns`). No substring
  matching, no fuzzy ranking, no token similarity.
* **No LLM, no DB, no network.** Pure deterministic regex over the user
  message string.
* **Limited path range.** May only emit paths whose ``IntentConfig``
  declares ``IntakeSource.FAST_INTAKE`` in ``allowed_intake_sources``.
  In Slice 1: Path 1 (greeting / thanks / farewell), Path 8.2
  (out_of_scope_nonsense), Path 8.3 (empty_message).
* **Limited path range — never operational.** FastIntake must NEVER emit
  Path 4 (operational manager-grounded) or any other answer path.
  Operational classification is the LLM Planner's job.
* **No registry config import.** This module does not import
  ``src.config.path_registry``. The registry-allowlist guard (§11.5.2)
  is scoped to the factory + escalation gate; FastIntake stays out.
* **When in doubt, miss.** False negatives cost a Planner round-trip
  (cheap). False positives short-circuit a real question into a canned
  reply (broken UX).

Status: implemented in Batch 4 (FastIntake + template Finalizer + /v2
slice).
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.models.intake_decision import IntakeDecision
from src.pipeline.fast_intake_patterns import (
    FAST_INTAKE_PATTERNS,
    PATTERN_VERSION,
)


def try_match(
    message: str,
    now: datetime | None = None,
) -> IntakeDecision | None:
    """Run the closed pattern table against ``message``.

    Returns an ``IntakeDecision`` on the first match; returns ``None`` on
    miss (the orchestrator then falls through to the Planner).

    Normalization is deliberately conservative: only outer whitespace is
    trimmed before matching, and the original ``message`` is preserved
    in ``IntakeDecision.raw_message`` for forensics. Case-insensitivity
    for greetings / thanks / farewells is baked into the patterns
    themselves via ``re.IGNORECASE`` (see ``fast_intake_patterns.py``).

    ``now`` is injectable for deterministic testing; defaults to UTC now.
    """
    trimmed = message.strip()
    timestamp = now if now is not None else datetime.now(timezone.utc)

    for pattern in FAST_INTAKE_PATTERNS:
        if pattern.compiled_regex.fullmatch(trimmed) is not None:
            return IntakeDecision(
                pattern_id=pattern.pattern_id,
                pattern_version=PATTERN_VERSION,
                path=pattern.path,
                intent_topic=pattern.intent_topic,
                matched_at=timestamp,
                raw_message=message,
            )

    return None
