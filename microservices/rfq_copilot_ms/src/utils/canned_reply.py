"""Canned reply generator — Batch 3 placeholder for the Batch 5 LLM call.

Pure function. No side effects. Single import target — Batch 5 swaps
this import in TurnController for the real LLM-backed reply without
touching routes, controllers, datasources, or persistence.
"""

from src.models.thread import GeneralMode, RfqBoundMode


_GENERAL = (
    "Backend connected — your message is now persisted on the copilot service. "
    "I'm still in MVP demo mode without grounding; manager-side RFQ data lands "
    "in the next batch."
)


def generate_canned_reply(mode: GeneralMode | RfqBoundMode) -> str:
    if isinstance(mode, GeneralMode):
        return _GENERAL
    return (
        f"Backend connected for {mode.rfq_label} — your message is now persisted "
        "on the copilot service. I'm still in MVP demo mode without RFQ-side "
        "grounding; deadline, stage, owner, and blockers will be answered through "
        "rfq_manager_ms in the next batch."
    )
