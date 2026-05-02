"""LLM Compose I/O contracts (Batch 8).

Wire types for the Compose stage (``src/pipeline/compose.py``). Compose
takes plan + evidence, calls the LLM with strict JSON-schema output,
and returns a ``ComposeOutput`` that the orchestrator stores on
``state.draft_text``.

Hard discipline (per freeze §5 Compose row + §8 forbidden):

* No tool selection. Compose is GIVEN the evidence; it doesn't fetch.
* No registry config import.
* No invented facts — answer ONLY from ``evidence_packets`` content.
* No hidden chain-of-thought field. The LLM may produce a rationale
  inside the prompt for verification, but it isn't part of the wire
  contract.

These DTOs are the only typed surface between the Compose function and
its callers. The actual Azure OpenAI request shape lives inside
``src/pipeline/compose.py`` and the existing ``LlmConnector``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ComposeInput(BaseModel):
    """The compact input passed to the Compose stage. Constructed by the
    orchestrator from ``state.plan`` + ``state.evidence_packets``.

    Compose's job is to render this into prose; it should NOT need
    anything beyond what's here.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    intent_topic: str
    target_rfq_code: Optional[str] = None
    canonical_requested_fields: list[str]
    # Per-target evidence as JSON-safe dicts. The orchestrator
    # serializes EvidencePacket objects via model_dump(mode="json")
    # before constructing ComposeInput so Compose doesn't need to
    # import ExecutionState types.
    evidence_packets: list[dict]
    answer_style: str = "concise"
    """Loose hint to the prompt — "concise" / "summary-bullets" /
    "single-sentence". Slice 1: only "concise" is supported."""

    max_answer_lines: int = 8
    """Soft cap on output lines. The shape guardrail enforces an
    absolute cap on character length; this hint shapes the prompt."""


class ComposeOutput(BaseModel):
    """The validated structured output from the Compose LLM call.

    ``draft_text`` is the candidate user-facing answer — NOT yet
    promoted to ``state.final_text`` (the Judge runs first). The Judge
    verifies, the orchestrator promotes on pass, the Gate routes on
    fail. The orchestrator NEVER returns ``draft_text`` directly to
    the user.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, protected_namespaces=()
    )

    draft_text: str
    used_source_refs: list[str] = []
    """Which evidence ``source_id``s the LLM claims to have used. The
    Judge can spot-check against ``state.evidence_packets[*].source_refs``.
    Not load-bearing in Slice 1 — the LLM is asked to populate this
    but the Judge doesn't currently enforce. Populates for forensics."""

    composed_at: datetime
    model_name: Optional[str] = None
