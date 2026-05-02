"""v2 lane wire types for the turn endpoint.

Kept separate from ``src/models/turn.py`` (which is /v1's Pydantic
contract) so the two lanes can evolve independently. /v2 uses
``message`` (NOT ``user_message`` like /v1) per the Batch 4 contract
decision.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class V2TurnRequest(BaseModel):
    """Request body for ``POST /rfq-copilot/v2/threads/{thread_id}/turn``.

    Fields:

    * ``message`` — the user's text. Required.
    * ``current_rfq_code`` — optional RFQ-page context. If the user is
      viewing an RFQ in the UI and asks "what is the deadline?",
      sending this lets the Resolver pick up the page context for
      ``proposed_kind="page_default"`` planner emissions.
    * ``current_rfq_id`` — optional RFQ UUID/id. Reserved for future
      use; Slice 1 resolves by ``rfq_code``.
    """

    model_config = ConfigDict(extra="forbid")

    message: str
    current_rfq_code: Optional[str] = None
    current_rfq_id: Optional[str] = None


class V2TurnResponse(BaseModel):
    """Response body for ``POST /rfq-copilot/v2/threads/{thread_id}/turn``.

    Status values:

    * ``"answered"`` — pipeline produced a grounded or template answer.
      ``answer`` is the user-facing string.
    * Other status values are returned via ``JSONResponse`` with the
      appropriate HTTP code (e.g. 501 ``planner_not_implemented``);
      this Pydantic model only describes the 200 success shape.
    """

    model_config = ConfigDict(extra="forbid")

    lane: Literal["v2"] = "v2"
    status: Literal["answered"] = "answered"
    thread_id: str
    answer: str
    path: Optional[str] = None
    intent_topic: Optional[str] = None
    reason_code: Optional[str] = None
    execution_record_id: Optional[str] = None
    """ID of the persisted ``execution_records`` row for this turn.
    None when persistence was unavailable or failed (production
    ``strict=False`` mode); see Batch 6 / freeze §4."""
