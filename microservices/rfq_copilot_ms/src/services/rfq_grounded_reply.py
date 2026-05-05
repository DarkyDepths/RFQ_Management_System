"""RfqGroundedReplyService — orchestrates manager fetch + prompt build + LLM call.

Owns:
- the system prompt text
- the messages array shape (system + real history + current user)
- the failure-mode mapping for the user-facing reply

Does NOT own:
- prompt FIELD formatting       -> manager_translator.format_rfq_for_prompt
- HTTP details                  -> ManagerConnector
- LLM SDK details               -> LlmConnector
- persistence / actor / thread  -> TurnController

Stages call is best-effort. If stages fail but RFQ detail succeeded,
we proceed without blocker / stage-list context — the translator
renders "Blocker: data not available" and skips the stage list.
Per-batch design rule: do not fail the whole answer when only stage
context is missing.
"""

from __future__ import annotations

import logging
from typing import Iterable

from src.connectors.llm_connector import LlmConnector
from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.db import TurnRow
from src.models.manager_dto import ManagerRfqStageDto
from src.translators.manager_translator import format_rfq_for_prompt
from src.utils.errors import (
    LlmUnreachable,
    ManagerAuthFailed,
    ManagerUnreachable,
    RfqAccessDenied,
    RfqNotFound,
)


logger = logging.getLogger(__name__)


_SYSTEM_PROMPT_TEMPLATE = (
    "You are RFQ Copilot, an assistant for the Gulf Heavy Industries "
    "estimation team. Answer the user's question about this specific RFQ "
    "using ONLY the data in the \"RFQ DATA\" section below. "
    "Answer ONLY what was asked — do not volunteer unrelated fields. "
    "If the data does not contain the answer, say so explicitly — never "
    "invent, assume, or extrapolate. Keep responses concise (2-3 sentences). "
    "Do not echo the data verbatim; answer the question.\n\n"
    "RFQ DATA (platform truth — do not contradict):\n"
    "{rfq_data}"
)

_FALLBACK_MANAGER_UNREACHABLE = (
    "I couldn't reach the RFQ data service right now. Try again in a moment."
)
_FALLBACK_MANAGER_AUTH_FAILED = (
    "I couldn't reach the RFQ data service due to a configuration "
    "issue on my side. Please notify the team."
)
_FALLBACK_RFQ_ACCESS_DENIED = (
    "I'm not allowed to read this RFQ."
)
_FALLBACK_LLM_UNREACHABLE = (
    "My language model is unavailable right now. Try again in a moment."
)
_FALLBACK_RFQ_NOT_FOUND = (
    "I couldn't find data for this RFQ in the platform."
)

_HISTORY_PAIR_LIMIT = 5  # last 5 user/assistant pairs = up to 10 messages


class RfqGroundedReplyService:
    def __init__(
        self,
        manager_connector: ManagerConnector,
        llm_connector: LlmConnector,
    ):
        self.manager = manager_connector
        self.llm = llm_connector

    def generate(
        self,
        actor: Actor,
        rfq_id: str,
        user_message: str,
        history: Iterable[TurnRow],
    ) -> str:
        # 1. Fetch RFQ detail. Failure here is terminal for this turn.
        try:
            detail = self.manager.get_rfq_detail(rfq_id, actor)
        except RfqNotFound:
            return _FALLBACK_RFQ_NOT_FOUND
        except RfqAccessDenied:
            # Manager 403 (Batch 9.1 typed error). Surface a distinct
            # message but stay graceful -- never raise out of /v1.
            return _FALLBACK_RFQ_ACCESS_DENIED
        except ManagerAuthFailed:
            # Manager 401 -- copilot's credentials rejected. Distinct
            # from "service unreachable" so operators can spot it in
            # the response copy.
            return _FALLBACK_MANAGER_AUTH_FAILED
        except ManagerUnreachable:
            return _FALLBACK_MANAGER_UNREACHABLE

        # 2. Fetch stages (best-effort). Always attempt — Batch 4.1 includes
        #    the full stage list in the prompt, not just the current-stage blocker.
        all_stages: list[ManagerRfqStageDto] = []
        try:
            all_stages = self.manager.get_rfq_stages(rfq_id, actor)
        except (
            ManagerUnreachable,
            ManagerAuthFailed,
            RfqAccessDenied,
            RfqNotFound,
        ) as exc:
            # Best-effort: any manager failure on stages is recoverable.
            # The detail call above already succeeded, so we have enough
            # context; the stage list is just nice-to-have. Batch 9.1
            # added ManagerAuthFailed / RfqAccessDenied to the catch
            # list so a permission downgrade between calls doesn't
            # bubble out as an uncaught AppError.
            logger.warning(
                "Stages fetch failed for rfq %s; continuing without stage context: %s",
                rfq_id,
                exc.__class__.__name__,
            )

        current_stage = None
        if detail.current_stage_id is not None and all_stages:
            current_stage = next(
                (s for s in all_stages if s.id == detail.current_stage_id),
                None,
            )

        # 3. Build the messages array. System prompt + REAL history + current user.
        rfq_data_section = format_rfq_for_prompt(
            detail,
            current_stage,
            all_stages=all_stages or None,
        )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": _SYSTEM_PROMPT_TEMPLATE.format(rfq_data=rfq_data_section),
            }
        ]
        messages.extend(_format_history(history))
        messages.append({"role": "user", "content": user_message})

        # 4. Call LLM.
        try:
            return self.llm.complete(messages, max_tokens=500)
        except LlmUnreachable:
            return _FALLBACK_LLM_UNREACHABLE


def _format_history(turns: Iterable[TurnRow]) -> list[dict[str, str]]:
    """Take the last N user/assistant pairs of real history. Never inject synthetic Q/A."""
    turn_list = list(turns)
    if not turn_list:
        return []
    recent = turn_list[-(2 * _HISTORY_PAIR_LIMIT):]
    return [{"role": t.role, "content": t.content} for t in recent]
