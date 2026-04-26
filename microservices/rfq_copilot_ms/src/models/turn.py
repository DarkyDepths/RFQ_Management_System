"""Turn Pydantic models — wire shapes for the turn endpoint.

Snake_case throughout to match the wire contract pinned in
frontend/rfq_ui_ms/src/types/copilot.ts (WireMessage / WireTurnResponse).
The frontend connector normalizes wire <-> domain (camelCase).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


MessageRole = Literal["user", "assistant"]


class MessageView(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime


class TurnRequest(BaseModel):
    user_message: str


class TurnResponse(BaseModel):
    message_id: str  # ID of the user message that was just persisted.
    assistant_message: MessageView
