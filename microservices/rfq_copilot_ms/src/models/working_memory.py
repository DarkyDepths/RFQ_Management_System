"""WorkingMemoryEntry — one prior turn projected into working memory.

See ``docs/11-Architecture_Frozen_v2.md`` §3.x (memory) and Batch 10
plan (Slice 2 foundation).

Working memory is the short-term conversation context the copilot
loads at the start of each turn. The full forensic state of a prior
turn lives in ``execution_records``; this is the compact prompt-ready
projection.

Only **complete pairs** are admitted: an entry requires both a
``user_message`` AND a non-null ``assistant_answer``. Mid-flight Persist
failures (where the user message was recorded but the assistant answer
never landed) ARE surfaced in the message-reconstruction layer
(`V2HistoryDatasource.reconstruct_messages` returns user-only rows so
the UI can show "you asked X; I crashed") but DO NOT enter working
memory. Reasoning: the UI showing a half-formed turn is fine; semantic
resolution against an empty assistant answer is risky.

Batch 10 ONLY captures these entries into ``state.working_memory``.
Planner / Compose / Judge prompts are unchanged in Batch 10 — see
the anti-drift test ``test_batch10_no_history_injection.py``.
Batch 12 will introduce semantic follow-up resolution and (separately)
prompt injection; this shape is designed forward to that batch so no
schema migration is needed.

Hard discipline:

* ``frozen=True`` + ``extra="forbid"`` — same posture as every other
  per-record forensics object (see ``_FROZEN_RECORD`` in
  ``src/models/execution_state.py``).
* ``assistant_answer`` is **required** (not Optional) — see the
  reasoning above.
* No fields beyond what Batch 10 captures + Batch 12 will need. No
  hidden chain-of-thought, no internal labels, no per-turn forensic
  blobs (those stay in ``execution_records``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WorkingMemoryEntry(BaseModel):
    """One complete prior turn (user + assistant) loaded from
    ``execution_records`` for the current thread.

    Fields:

    * ``turn_id`` — the prior turn's id; lets downstream stages
      cross-reference back to the full ``execution_record`` for
      deeper inspection.
    * ``user_message`` — the prior user message verbatim.
    * ``assistant_answer`` — the prior assistant answer verbatim.
      Always non-null.
    * ``target_rfq_code`` — the RFQ that was the target of the prior
      turn, if any (Path 4). Captured in Batch 10; Batch 12's
      semantic follow-up resolution reads this to interpret "it" /
      "this RFQ" / "the same one" against prior context.
    * ``intent_topic`` — the prior turn's intent (e.g. ``"deadline"``,
      ``"summary"``, ``"out_of_scope"``). Captured in Batch 10;
      Batch 12 uses this as a follow-up classification hint.
    * ``path`` — the Path the prior turn took (e.g. ``"path_4"``,
      ``"path_8_3"``). Captured in Batch 10; Batch 12 uses this to
      decide whether a follow-up makes sense (a Path 8.x prior
      turn is rarely a useful follow-up anchor).
    * ``created_at`` — the prior turn's wall-clock timestamp.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    turn_id: str
    user_message: str
    assistant_answer: str
    target_rfq_code: Optional[str] = None
    intent_topic: Optional[str] = None
    path: Optional[str] = None
    created_at: datetime
