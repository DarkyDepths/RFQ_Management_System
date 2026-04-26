"""Thread Pydantic models — wire shapes for the thread endpoints.

Snake_case throughout to match the frontend wire types.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from src.models.turn import MessageView


class GeneralMode(BaseModel):
    kind: Literal["general"]


class RfqBoundMode(BaseModel):
    kind: Literal["rfq_bound"]
    rfq_id: str
    rfq_label: str


ThreadMode = Annotated[Union[GeneralMode, RfqBoundMode], Field(discriminator="kind")]


class OpenThreadRequest(BaseModel):
    mode: ThreadMode


class OpenThreadResponse(BaseModel):
    thread_id: str
    messages: list[MessageView]


class NewThreadRequest(BaseModel):
    mode: ThreadMode


class NewThreadResponse(BaseModel):
    thread_id: str
