"""Compose — Stage 9 of the v4 canonical pipeline (Batch 8).

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Compose row) and §8
(Compose forbidden behaviors).

Slice 1 / Batch 8: Compose runs only for Path 4 *synthesis* intents
(``summary``, ``blockers``) where the deterministic renderer can't
naturally produce a fluent multi-field answer. Single-field intents
(``deadline``, ``owner``, etc.) stay deterministic — Compose adds
risk without value there.

Hard discipline:

* No tool selection. Compose is given the evidence; never fetches.
* No registry config import.
* No manager call.
* No ``TurnExecutionPlan`` instantiation.
* No invented facts — answer ONLY from the evidence dump in the
  prompt. The Judge verifies; Guardrails are the safety floor.
* Sets ``state.draft_text``, NOT ``state.final_text``. The
  orchestrator promotes after Judge passes.

Failure mapping:

* ``LlmUnreachable`` from the connector -> StageError
  ``llm_unavailable`` -> Path 8.5.
* Malformed JSON / missing schema fields -> StageError
  ``llm_unavailable`` (treat as effective LLM failure — the model
  didn't deliver a usable answer).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from src.connectors.llm_connector import LlmConnector
from src.models.compose import ComposeInput, ComposeOutput
from src.models.execution_state import ExecutionState
from src.models.path_registry import ReasonCode
from src.pipeline.errors import StageError
from src.utils.errors import LlmUnreachable


logger = logging.getLogger(__name__)


_COMPOSE_JSON_SCHEMA: dict = {
    "name": "ComposeOutput",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["draft_text", "used_source_refs"],
        "properties": {
            "draft_text": {
                "type": "string",
                "description": "User-facing answer; concise, grounded ONLY in the EVIDENCE FIELDS section.",
            },
            "used_source_refs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "source_id values from EVIDENCE the draft used. Empty array if none.",
            },
        },
    },
}
"""Azure OpenAI ``response_format`` schema for Compose (Batch 9.1).

Pins the wire shape at the API level so the model can never return
free-form prose. The Pydantic ``ComposeOutput`` validation in
``compose_path_4`` becomes defense in depth, not the primary contract.
"""


_SYSTEM_PROMPT = """\
You are RFQ Copilot Compose for the Gulf Heavy Industries estimation
team. Render a SHORT, GROUNDED answer about ONE RFQ.

HARD RULES — violations will be rejected by the Judge:

1. Use ONLY the EVIDENCE FIELDS section below. Never invent values.
   If the user asked for a field that isn't in the evidence, say so —
   don't guess.

2. Do NOT include intelligence claims: win probability, win prediction,
   bid strategy, workbook readiness, cost prediction, recommendation,
   competitive ranking, "we should bid", "predicted winner". Those
   belong to other stages of the platform.

3. Do NOT mention internal architecture: paths (path_4 etc.),
   reason_codes, factory, validator, gate, evidence packets, plans.
   Just answer the user's question.

4. Do NOT include forbidden fields. The orchestrator filters these out
   of EVIDENCE FIELDS, but if you see one, ignore it.

5. Use the same target label the EVIDENCE uses (e.g. "IF-0001").

6. Be concise — 4-6 lines for summaries; 1-3 lines for single-fact
   intents.

7. Cite source ids in ``used_source_refs`` so the Judge can spot-check.

Output ONLY the JSON object below. No prose outside it. No markdown
fences.

JSON SCHEMA:
{
  "draft_text": "<the user-facing answer>",
  "used_source_refs": ["<source_id>", ...]
}
"""


def compose_path_4(
    state: ExecutionState,
    llm_connector: LlmConnector,
    *,
    answer_style: str = "concise",
    max_answer_lines: int = 8,
) -> None:
    """Compose a Path 4 grounded answer from evidence_packets.

    Mutates ``state.draft_text``; never touches ``state.final_text``.
    Raises ``StageError`` on LLM failure or malformed output — the
    orchestrator catches and routes via the gate.
    """
    if state.plan.path.value != "path_4":
        raise StageError(
            trigger="invalid_planner_proposal",
            reason_code=ReasonCode("invalid_planner_proposal"),
            source_stage="compose",
            details={"reason": f"compose_path_4 called with path={state.plan.path.value}"},
        )

    if not state.evidence_packets:
        # Defense in depth: EvidenceCheck should have caught this.
        raise StageError(
            trigger="evidence_empty",
            reason_code=ReasonCode("no_evidence"),
            source_stage="compose",
            details={"reason": "no evidence_packets to compose from"},
        )

    target_rfq_code = state.evidence_packets[0].target_label

    compose_input = ComposeInput(
        path=state.plan.path.value,
        intent_topic=state.plan.intent_topic,
        target_rfq_code=target_rfq_code,
        canonical_requested_fields=list(state.plan.canonical_requested_fields),
        evidence_packets=[p.model_dump(mode="json") for p in state.evidence_packets],
        answer_style=answer_style,
        max_answer_lines=max_answer_lines,
    )

    user_content = _render_user_prompt(compose_input)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    # Compose temperature comes from the plan -- the factory copies
    # the per-path ModelProfile from the registry into the plan at
    # construction time, so reading state.plan keeps Compose inside
    # CI guard §11.5.2 (only Factory + Gate may import the registry
    # config). Falls back to 0.3 if no profile was attached.
    compose_temperature = (
        state.plan.model_profile.temperature
        if state.plan.model_profile is not None
        else 0.3
    )

    try:
        raw = llm_connector.complete(
            messages,
            max_tokens=600,
            response_format={
                "type": "json_schema",
                "json_schema": _COMPOSE_JSON_SCHEMA,
            },
            temperature=compose_temperature,
        )
    except LlmUnreachable as exc:
        logger.warning("Compose LLM unreachable: %s", exc)
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="compose",
            details={"cause": str(exc)},
        ) from exc

    cleaned = _strip_json_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Compose returned non-JSON output: %s", exc.__class__.__name__)
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="compose",
            details={"reason": "compose returned malformed JSON"},
        ) from exc

    # Inject server-side timestamp; reject any extra LLM-supplied fields
    # via ComposeOutput's extra="forbid" (refuse to accept hidden
    # chain-of-thought or anything else outside the contract).
    if not isinstance(parsed, dict):
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="compose",
            details={"reason": "compose returned non-object JSON"},
        )
    parsed["composed_at"] = datetime.now(timezone.utc).isoformat()

    try:
        output = ComposeOutput.model_validate(parsed)
    except Exception as exc:
        logger.warning(
            "Compose output failed ComposeOutput schema: %s",
            exc.__class__.__name__,
        )
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="compose",
            details={"reason": "compose output did not match schema"},
        ) from exc

    if not output.draft_text or not output.draft_text.strip():
        # The model returned the JSON shape but with empty content.
        # Treat as effective LLM failure.
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="compose",
            details={"reason": "compose returned empty draft_text"},
        )

    state.draft_text = output.draft_text


def _render_user_prompt(compose_input: ComposeInput) -> str:
    """Build the user-message body — INTENT, REQUEST, EVIDENCE FIELDS."""
    lines: list[str] = []
    lines.append(f"INTENT: {compose_input.intent_topic}")
    if compose_input.target_rfq_code:
        lines.append(f"TARGET RFQ: {compose_input.target_rfq_code}")
    lines.append(
        f"USER ASKED ABOUT FIELDS: "
        f"{', '.join(compose_input.canonical_requested_fields) or '(intent default)'}"
    )
    lines.append(f"STYLE: {compose_input.answer_style}")
    lines.append(f"MAX LINES: {compose_input.max_answer_lines}")
    lines.append("")
    lines.append("EVIDENCE FIELDS (verified manager data — answer ONLY from these):")
    for packet in compose_input.evidence_packets:
        lines.append(f"  Target: {packet.get('target_label', '?')}")
        for field_name, value in (packet.get("fields") or {}).items():
            lines.append(f"    {field_name}: {value}")
        for ref in packet.get("source_refs") or []:
            lines.append(
                f"    [source: {ref.get('source_type', '?')}/"
                f"{ref.get('source_id', '?')}]"
            )
    lines.append("")
    lines.append("Return the JSON object now.")
    return "\n".join(lines)


def _strip_json_fences(text: str) -> str:
    """Tolerate models that wrap output in ```json ... ``` fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped
