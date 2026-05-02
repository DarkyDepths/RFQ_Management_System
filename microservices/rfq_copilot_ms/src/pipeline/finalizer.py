"""Finalizer — Stage 12 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Finalizer row) and §12.6
(template-first rendering for simple Path 4 facts — deferred to Slice 5).

**Policy-stupid template renderer.** Reads
``state.plan.finalizer_template_key`` (and ``finalizer_reason_code`` for
Path 8.x sub-cases) and renders the user-facing message. Does NOT
inspect ``state.escalations[-1]`` to decide its template — the
Escalation Gate already re-entered the factory and the appropriate
Path 8.x plan is in ``state.plan`` with the correct template key
attached. This is the property that makes the architecture testable:
the same Finalizer code path runs for successful turns, FastIntake
plans, and escalation-routed Path 8.x plans (§5.2).

Hard discipline:

* **Template-only.** No LLM call. No manager call. No registry config
  import — the plan is self-contained (factory copied template_key in).
* **Short, product-safe wording.** No internal labels like "Path 8.3"
  in user-facing text.
* **No invented RFQ facts.** Path 8.x templates do not produce data;
  they explain why no answer is available.
* **Loud failure on unknown template_key.** If the plan carries a
  template_key that's not in ``_TEMPLATES``, raise ValueError. Better
  to crash than render a misleading default.

Status: Batch 4 implements the templates required by the FastIntake +
Path 8 vertical slice (Path 1 greeting/thanks/farewell, Path 8.2/8.3
direct emissions, plus the Path 8.1/8.4/8.5 templates exercised by
escalation tests). Templates not in the dict raise ``ValueError``;
later batches will extend the dict as new reason_codes become reachable.

Sets ``state.final_text`` and ``state.final_path`` on the in-place
``ExecutionState`` per §5 stage contract.
"""

from __future__ import annotations

from src.models.execution_plan import TurnExecutionPlan
from src.models.execution_state import ExecutionState


# ── Template dictionary (the entire v4 user-facing surface for Slice 1
#    template-only paths). Centralized here so all wording is reviewable
#    in one place. Keys mirror PATH_CONFIGS finalizer_template_keys
#    values exactly — bumping a template_key in PATH_CONFIGS without
#    adding the matching template here will raise ValueError loudly.

_TEMPLATES: dict[str, str] = {
    # ── Path 1 — conversational ──────────────────────────────────────
    "path_1.greeting": (
        "Hi — I can help with RFQ deadlines, stages, blockers, owners, "
        "and portfolio questions."
    ),
    "path_1.thanks": "You're welcome.",
    "path_1.farewell": "Goodbye.",
    # ── Path 8.1 — unsupported / invalid ─────────────────────────────
    "path_8_1.unsupported_intent": "I can't help with that yet.",
    # ── Path 8.2 — out-of-scope ──────────────────────────────────────
    "path_8_2.out_of_scope": (
        "I can only help with RFQ, estimation, and industrial project "
        "questions."
    ),
    "path_8_2.out_of_scope_nonsense": (
        "I couldn't understand that. Please ask an RFQ-related question."
    ),
    # ── Path 8.3 — clarification ─────────────────────────────────────
    "path_8_3.empty_message": (
        "Please type a question or tell me which RFQ you want to look at."
    ),
    "path_8_3.no_target": (
        "Which RFQ are you asking about? Please share an RFQ code "
        "(like IF-0001) or open the RFQ page first."
    ),
    "path_8_3.unclear_intent": (
        "Could you rephrase that? I'm not sure what you'd like to know."
    ),
    "path_8_3.low_confidence": (
        "I'm not sure I understood that — could you rephrase or share "
        "more detail?"
    ),
    "path_8_3.ambiguous": (
        "I found more than one match — could you specify which RFQ "
        "you mean?"
    ),
    "path_8_3.multi_intent": (
        "You asked more than one thing in that message — which would "
        "you like me to handle first?"
    ),
    "path_8_3.comparison_missing_target": (
        "Which RFQs would you like me to compare? Please share two or "
        "more RFQ codes."
    ),
    "path_8_3.pre_search_underspecified": (
        "Could you narrow that down? Try filtering by status, owner, "
        "or a deadline window."
    ),
    "path_8_3.post_search_unrenderable": (
        "That returned a lot of RFQs — could you filter further?"
    ),
    # ── Path 8.4 — inaccessible / missing ────────────────────────────
    "path_8_4.denied": "I can't access that RFQ.",
    "path_8_4.all_inaccessible": (
        "I can't access any of the RFQs you mentioned."
    ),
    # ── Path 8.5 — no evidence / source unavailable / llm unavailable ──
    "path_8_5.no_evidence": (
        "I don't have enough grounded information to answer that safely."
    ),
    "path_8_5.source_unavailable": (
        "The data source I needed isn't reachable right now. "
        "Please try again shortly."
    ),
    "path_8_5.llm_unavailable": (
        "The language model I rely on isn't available right now. "
        "Please try again shortly."
    ),
}


def render_template(plan: TurnExecutionPlan) -> str:
    """Pure renderer — no side effects, no state mutation.

    Looks up ``plan.finalizer_template_key`` in the template dict and
    returns the user-facing string. Raises ``ValueError`` if the key is
    not in the dict.

    Exposed as a module-level function so tests can exercise rendering
    without constructing a full ``ExecutionState``.
    """
    template_key = plan.finalizer_template_key
    if template_key not in _TEMPLATES:
        raise ValueError(
            f"Finalizer has no template for {template_key!r}. "
            f"Known templates: {sorted(_TEMPLATES.keys())}. "
            f"Either add the template to src/pipeline/finalizer.py "
            f"_TEMPLATES, or fix PATH_CONFIGS to use a registered key."
        )
    return _TEMPLATES[template_key]


def finalize(state: ExecutionState) -> None:
    """Render the user-facing message and write it back to the
    ExecutionState.

    Two cases:

    1. **Already-grounded answer** (``state.final_text`` is already set)
       — typically Path 4 where ``path4_renderer.render_path_4()``
       populated ``final_text`` from manager evidence. Finalizer is a
       no-op for content; just sets ``final_path`` for forensics.
    2. **Template-only path** (``state.final_text`` is None) — Path 1
       conversational, Path 8.x safety paths. Look up the template via
       ``state.plan.finalizer_template_key`` and render.

    Sets:

    * ``state.final_text`` — the rendered template string (case 2 only).
    * ``state.final_path`` — copies ``state.plan.path`` so the caller
      can record the actual path used (which may differ from the
      original plan.path after escalation).

    Does NOT call into Persist (§13) — that's a separate stage in a
    later batch.
    """
    if state.final_text is None:
        state.final_text = render_template(state.plan)
    state.final_path = state.plan.path
