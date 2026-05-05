"""PortfolioGroundedReplyService — general-mode counterpart to RfqGroundedReplyService.

Same shape: prefetched manager context + REAL conversation history +
single LLM call. Different data: portfolio stats + a window of nearest-
deadline RFQs instead of one specific RFQ's detail.

Owns:
- the general-mode system prompt text
- the messages array shape
- the failure-mode mapping for the user-facing reply

Does NOT own:
- prompt FIELD formatting       -> manager_translator.format_portfolio_for_prompt
- HTTP details                  -> ManagerConnector
- LLM SDK details               -> LlmConnector
- persistence / actor / thread  -> TurnController
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Iterable

from src.connectors.llm_connector import LlmConnector
from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.db import TurnRow
from src.translators.manager_translator import format_portfolio_for_prompt
from src.utils.errors import (
    LlmUnreachable,
    ManagerAuthFailed,
    ManagerUnreachable,
    RfqAccessDenied,
)


logger = logging.getLogger(__name__)


_SYSTEM_PROMPT_TEMPLATE = (
    "You are RFQ Copilot, an assistant for the Gulf Heavy Industries "
    "estimation team. You answer general portfolio questions using ONLY "
    "the data in the \"PORTFOLIO DATA\" section below. "
    "Answer ONLY what was asked — do not volunteer unrelated facts. "
    "If the data does not contain the answer, say so explicitly — never "
    "invent, assume, or extrapolate. "
    "Today's date is {today}, so you can reason about time-relative "
    "questions like 'this week', 'due soon', or 'overdue' using the "
    "deadlines in the data. "
    "When listing RFQs, prefer their rfq_code (like IF-0001) and brief "
    "context. Keep responses concise (3-5 sentences max). "
    "Note: the RFQ list is a window of the soonest-deadline {rfq_count} "
    "RFQs out of the portfolio. Do not extrapolate beyond what's listed.\n\n"
    "PORTFOLIO DATA (platform truth — do not contradict):\n"
    "{portfolio_data}"
)

_FALLBACK_MANAGER_UNREACHABLE = (
    "I couldn't reach the portfolio data service right now. "
    "Try again in a moment."
)
_FALLBACK_MANAGER_AUTH_FAILED = (
    "I couldn't reach the portfolio data service due to a configuration "
    "issue on my side. Please notify the team."
)
_FALLBACK_ACCESS_DENIED = (
    "I'm not allowed to read the portfolio data."
)
_FALLBACK_LLM_UNREACHABLE = (
    "My language model is unavailable right now. Try again in a moment."
)

_RFQ_LIST_SIZE = 20
_RFQ_LIST_STATUSES = ["In preparation"]  # active RFQs only — manager uses display strings as enum values
_HISTORY_PAIR_LIMIT = 5


class PortfolioGroundedReplyService:
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
        user_message: str,
        history: Iterable[TurnRow],
    ) -> str:
        # 1. Fetch portfolio context. Both calls together; either failure is terminal.
        try:
            stats = self.manager.get_portfolio_stats(actor)
            rfqs = self.manager.list_rfqs(
                actor,
                size=_RFQ_LIST_SIZE,
                sort="deadline",
                statuses=_RFQ_LIST_STATUSES,
            )
        except RfqAccessDenied:
            # Manager 403 (Batch 9.1 typed error). Surface a distinct
            # message but stay graceful -- never raise out of /v1.
            return _FALLBACK_ACCESS_DENIED
        except ManagerAuthFailed:
            # Manager 401 -- copilot's credentials rejected. Distinct
            # from "service unreachable" so operators can spot it in
            # the response copy.
            return _FALLBACK_MANAGER_AUTH_FAILED
        except ManagerUnreachable:
            return _FALLBACK_MANAGER_UNREACHABLE

        # 2. Build messages: system + REAL history + current user.
        portfolio_data = format_portfolio_for_prompt(stats, rfqs)
        system_content = _SYSTEM_PROMPT_TEMPLATE.format(
            today=date.today().isoformat(),
            rfq_count=len(rfqs),
            portfolio_data=portfolio_data,
        )
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]
        messages.extend(_format_history(history))
        messages.append({"role": "user", "content": user_message})

        # 3. Call LLM.
        try:
            return self.llm.complete(messages, max_tokens=600)
        except LlmUnreachable:
            return _FALLBACK_LLM_UNREACHABLE


def _format_history(turns: Iterable[TurnRow]) -> list[dict[str, str]]:
    """Take the last N user/assistant pairs of real history. Never inject synthetic Q/A."""
    turn_list = list(turns)
    if not turn_list:
        return []
    recent = turn_list[-(2 * _HISTORY_PAIR_LIMIT):]
    return [{"role": t.role, "content": t.content} for t in recent]
