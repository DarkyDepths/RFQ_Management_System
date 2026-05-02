"""Canned reply generator — Batch 3 placeholder for the Batch 5 LLM call.

Pure function. No side effects. Single import target — Batch 5 swaps
this import in TurnController for the real LLM-backed reply without
touching routes, controllers, datasources, or persistence.
"""

from src.models.thread import GeneralMode, RfqBoundMode


_GENERAL = (
    "I can answer questions about a specific RFQ when you open me from "
    "an RFQ page. Portfolio-wide and intelligence-side answers are still "
    "being connected — coming in the next batches."
)


def generate_canned_reply(mode: GeneralMode | RfqBoundMode) -> str:
    """Used by TurnController for general mode only (Batch 4 onward).

    rfq_bound mode is now handled by RfqGroundedReplyService. The
    rfq_bound branch here remains as a defensive fallback for cases
    where the service was somehow not wired (should be unreachable in
    production paths).
    """
    if isinstance(mode, GeneralMode):
        return _GENERAL
    return (
        f"I'm ready for {mode.rfq_label} but my RFQ grounding service is "
        "not currently wired. Please retry in a moment."
    )
