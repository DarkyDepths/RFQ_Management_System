"""Pipeline stage failure mechanism.

Stages signal failures to the orchestrator by raising :class:`StageError`.
The orchestrator catches and routes via :class:`EscalationGate` which
re-enters :class:`ExecutionPlanFactory` to construct the safe Path 8.x
plan. Stages NEVER instantiate ``TurnExecutionPlan`` directly (CI guard
§11.5.1) and NEVER decide their own escalation routing (§5.2).

This is the cleanest Python idiom for "stage failed, route to gate":
exceptions carry the trigger + reason_code + source_stage tuple needed
by the §6 escalation matrix; the orchestrator's ``try/except`` is a
single intercept point.

Alternative considered: typed ``Result | StageError`` unions returned
from each stage. Rejected — Python doesn't enforce union exhaustiveness
at runtime; each stage would need to manually plumb the failure shape.
Exceptions keep the happy path readable.
"""

from __future__ import annotations

from src.models.path_registry import ReasonCode


class StageError(Exception):
    """Raised by a pipeline stage to signal a failure that should be
    routed via the EscalationGate.

    Carries the four pieces the §6 escalation matrix needs:

    * ``trigger`` — the failure trigger name (matches §6 matrix keys)
    * ``reason_code`` — the user-facing classification (drives template)
    * ``source_stage`` — which stage raised (forensics)
    * ``details`` — optional arbitrary payload for forensics

    Example::

        raise StageError(
            trigger="manager_unreachable",
            reason_code=ReasonCode("source_unavailable"),
            source_stage="tool_executor",
            details={"tool_name": "get_rfq_profile"},
        )
    """

    def __init__(
        self,
        trigger: str,
        reason_code: ReasonCode,
        source_stage: str,
        details: dict | None = None,
    ):
        self.trigger = trigger
        self.reason_code = reason_code
        self.source_stage = source_stage
        self.details = details or {}
        super().__init__(
            f"[{source_stage}] trigger={trigger} reason_code={reason_code}"
        )
