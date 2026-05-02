"""Finalizer — Stage 12 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Finalizer row) and §12.6
(template-first rendering for simple Path 4 facts).

**Policy-stupid template renderer.** Reads
``state.plan.finalizer_template_key`` (and ``finalizer_reason_code`` for
Path 8.x sub-cases) and renders the user-facing message. **Does NOT**
inspect ``state.escalations[-1]`` to decide its template — the
Escalation Gate already re-entered the factory and the appropriate
Path 8.x plan is in ``state.plan`` with the correct template key
attached. This is the property that makes the architecture testable:
the same Finalizer code path runs for successful turns, FastIntake
plans, and escalation-routed Path 8.x plans (§5.2).

Template-first eligibility (§12.6):

For Path 4 intents whose answer is a single field value (``deadline``,
``status``, ``owner``, ``current_stage_name``, ``priority``), the factory
sets ``model_profile=None`` so Compose is skipped and the Finalizer
renders the deterministic template directly with zero LLM cost.
``blockers``, ``description``, ``progress``, ``workflow`` keep
``model_profile`` set and run Compose normally.

Hard constraint: a template-first intent that returns a missing value
MUST escalate to 8.5 ``no_evidence`` rather than render
``"deadline: None"``. Evidence Check (Stage 7) catches this.

Sets ``status=COMPLETED`` on normal completion or ``status=ESCALATED``
when the rendered template came from a Path 8.x plan. ``status=FAILED``
is reserved for the rare hard-crash case (template render itself
crashed).

Batch 0 status: STUB ONLY. No template registry / no rendering yet.
"""

from __future__ import annotations

from src.models.execution_state import ExecutionState


def finalize(state: ExecutionState) -> None:  # noqa: ARG001
    """Render ``state.plan.finalizer_template_key`` (with the
    ``finalizer_reason_code`` variant for Path 8.x), write
    ``state.final_text`` + ``state.final_path``, transition the turn
    status to ``COMPLETED`` or ``ESCALATED``.

    Policy-stupid: never inspects ``state.escalations[-1]`` to choose
    the template. The Escalation Gate already re-entered the factory
    and the appropriate Path 8.x plan is in ``state.plan``.
    """
    raise NotImplementedError(
        "finalizer.finalize() scaffolded only. "
        "See docs/11-Architecture_Frozen_v2.md §5 (Finalizer) / §12.6."
    )
