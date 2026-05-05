"""/v2 thread management wire types (Batch 10).

These Pydantic models define the request/response shapes for the new
``POST /v2/threads/new`` / ``POST /v2/threads/open`` /
``POST /v2/threads/list`` / ``GET /v2/threads/{id}`` endpoints.

Mirror the /v1 ``GeneralMode`` / ``RfqBoundMode`` pattern so the
eventual frontend cutover (PR-D — separate from this batch) is small.
The /v2 mode adds an optional ``rfq_code`` field for display (the
human-readable RFQ code like ``IF-0001``) on top of the /v1 shape
which only carried the manager UUID and a free-form label.

Hard discipline (mirrors the rest of the v2 type contracts):

* ``extra="forbid"`` — wire shapes are closed; no smuggling new fields.
* Discriminated union on ``mode.kind`` — same trick /v1 uses.
* Reuse ``MessageView`` from ``src/models/turn.py`` for messages so
  the eventual frontend cutover doesn't need new message types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from src.models.turn import MessageView


# ── Mode (request body fragment) ─────────────────────────────────────────


class V2GeneralMode(BaseModel):
    """General-mode (no RFQ context) thread mode."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["general"]


class V2RfqBoundMode(BaseModel):
    """RFQ-bound thread mode. Carries both the manager UUID
    (``rfq_id``) and the human-readable code (``rfq_code``).

    /v1 only carried ``rfq_id`` + ``rfq_label``; /v2 also carries
    ``rfq_code`` so list views and titles can show ``"IF-0058"``
    without re-parsing the label string.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["rfq_bound"]
    rfq_id: str
    rfq_code: Optional[str] = None
    rfq_label: Optional[str] = None


V2ThreadMode = Annotated[
    Union[V2GeneralMode, V2RfqBoundMode], Field(discriminator="kind")
]


# ── Request bodies ──────────────────────────────────────────────────────


class V2NewThreadRequest(BaseModel):
    """``POST /v2/threads/new`` body."""

    model_config = ConfigDict(extra="forbid")

    mode: V2ThreadMode


class V2OpenThreadRequest(BaseModel):
    """``POST /v2/threads/open`` body."""

    model_config = ConfigDict(extra="forbid")

    mode: V2ThreadMode


class V2ListThreadsRequest(BaseModel):
    """``POST /v2/threads/list`` body."""

    model_config = ConfigDict(extra="forbid")

    mode: V2ThreadMode


# ── Response bodies ─────────────────────────────────────────────────────


class V2NewThreadResponse(BaseModel):
    """``POST /v2/threads/new`` response."""

    model_config = ConfigDict(extra="forbid")

    thread_id: str


class V2OpenThreadResponse(BaseModel):
    """``POST /v2/threads/open`` response.

    ``messages`` is reconstructed from ``execution_records`` for the
    thread, ordered chronologically. User-only rows surface (UI shows
    "you sent X; assistant didn't answer") -- working memory is
    stricter and skips those, but the open response is lenient so the
    UI can render the full conversation history.

    ``is_stale`` is computed from ``last_activity_at`` against the
    per-mode threshold (general 3 days, rfq_bound 7 days). When true,
    open-or-resume creates a fresh thread instead of returning the
    stale one — so a true ``is_stale`` will only appear here if the
    underlying row was reused for some reason; in normal flow it's
    always false.

    ``created_new`` is true when no fresh thread existed and one was
    created on this call.
    """

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    mode: V2ThreadMode
    messages: list[MessageView]
    is_stale: bool = False
    created_new: bool = False


class V2ThreadDetailResponse(BaseModel):
    """``GET /v2/threads/{id}`` response. Same shape as
    ``V2OpenThreadResponse`` minus ``created_new`` (a GET never
    creates)."""

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    mode: V2ThreadMode
    messages: list[MessageView]
    is_stale: bool = False


class V2ThreadSummary(BaseModel):
    """One row in ``V2ListThreadsResponse.threads``.

    ``preview`` is the last assistant answer truncated to a UI-friendly
    length; null when the thread has only user messages so far.
    ``title`` is set on the first /turn (deterministic — first user
    message truncated to 60 chars). Null until that first turn lands.
    """

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    title: Optional[str] = None
    rfq_code: Optional[str] = None
    rfq_label: Optional[str] = None
    last_activity_at: datetime
    is_stale: bool = False
    preview: Optional[str] = None


class V2ListThreadsResponse(BaseModel):
    """``POST /v2/threads/list`` response."""

    model_config = ConfigDict(extra="forbid")

    threads: list[V2ThreadSummary]
