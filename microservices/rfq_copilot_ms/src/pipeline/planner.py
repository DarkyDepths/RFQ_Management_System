"""Planner — Stage 1 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §2.1 and §3.5.

GPT-4o **structured** classifier (JSON schema enforced, ``temperature=0``).
Runs only when FastIntake (Stage 0) misses. Emits a single
``PlannerProposal`` (see ``src/models/planner_proposal.py``) — an
**untrusted** LLM output that downstream code never accepts directly.

The PlannerValidator (Stage 2) consumes the proposal and either emits a
``ValidatedPlannerProposal`` for the ExecutionPlanFactory or escalates
via the gate.

Allowed direct path emissions (per §2.1):

* Normal answer paths: 1, 2, 3, 4, 5, 6, 7
* Direct semantic emission: 8.1 (clear unsupported), 8.2 (clear out-of-scope)
* Direct semantic emission: 8.3 ONLY when ``multi_intent_detected=True``
* **NEVER** allowed: 8.4 (inaccessible), 8.5 (no-evidence / source-down)
  — these come only from the Escalation Gate routing a stage trigger.

Hard discipline:

* JSON-schema-enforced output via Azure OpenAI's ``response_format``
  parameter (no free text — see §8 forbidden list).
* Reads NO Path Registry entries directly. The validator + factory own
  policy enforcement.
* Constructor takes an ``llm_connector`` parameter so tests can inject
  a fake without monkeypatching (matches the /v1
  ``RfqGroundedReplyService`` injection pattern).

Status: Batch 5 — implemented for the Slice 1 path (Path 4 + direct
Path 8.x emissions). Path 2/3/5/6/7 classification will refine the
prompt as those paths ship.
"""

from __future__ import annotations

import json
import logging

from src.connectors.llm_connector import LlmConnector
from src.models.planner_proposal import PlannerProposal
from src.utils.errors import LlmUnreachable


logger = logging.getLogger(__name__)


# ── Planner model parameters ──────────────────────────────────────────────
#
# Mirrored from src/config/path_registry.py PLANNER_MODEL_CONFIG. The
# registry is the design-time source of truth; we mirror here because
# CI guard §11.5.2 forbids the Planner (and any pipeline module other
# than Factory + Gate) from importing the runtime config. An anti-drift
# test in tests/config/ asserts these values stay in sync with the
# registry — change one, change both.
_PLANNER_TEMPERATURE: float = 0.0
_PLANNER_MAX_TOKENS: int = 800


# System prompt — explains the classification task. The LLM emits ONLY
# the JSON proposal; downstream code does the rest. The prompt is the
# entire LLM-facing surface; keep it terse and rule-driven.
_SYSTEM_PROMPT = """\
You are the RFQ Copilot Planner. Your ONLY job is to classify the user's \
message into a single PlannerProposal JSON object. You DO NOT answer the \
question. You DO NOT pick tools. You DO NOT decide what fields to fetch. \
Downstream code uses your classification to plan the actual answer.

Allowed paths and intents (Slice 1 scope):

  path_4 — RFQ-specific operational questions about ONE RFQ.
    intent_topic must be one of:
      deadline       — when the RFQ is due
      owner          — who owns the RFQ
      status         — overall RFQ status
      current_stage  — which workflow stage is active
      priority       — urgency / priority level
      blockers       — current-stage blocker info
      stages         — full ordered list of workflow stages
      summary        — concise multi-field overview

  path_8_1 — direct emission for clearly unsupported asks.
    Use ONLY when the user's intent is operationally on-platform but \
    not yet supported (e.g. "send an email to the client" — the \
    platform doesn't do that).
    intent_topic: "unsupported_intent"

  path_8_2 — direct emission for clearly OUT-OF-SCOPE asks.
    Use for questions that are NOT about RFQ / estimation / industrial \
    projects (e.g. "write me a recipe", "what's the weather").
    intent_topic: "out_of_scope"

  path_8_3 — direct emission ONLY when multi_intent_detected=true.
    Use when the user clearly asks two unrelated questions in one \
    message and you cannot pick the primary one.
    Set multi_intent_detected=true. intent_topic: "multi_intent_detected"

target_candidates rules (Path 4):
  - If the user names an explicit RFQ code (e.g. "IF-0001"), set:
      target_candidates=[{"raw_reference":"IF-0001","proposed_kind":"rfq_code"}]
  - If the user asks about "this RFQ" / "it" / has no explicit RFQ:
      target_candidates=[{"raw_reference":"","proposed_kind":"page_default"}]
    (the resolver uses the page context if present)
  - For path_8_*, target_candidates=[]

requested_fields rules (Path 4):
  - Leave EMPTY for single-intent questions; the factory defaults to \
    the intent's allowed fields. Only fill if the user explicitly \
    enumerates fields.

confidence: 0.0..1.0. Use:
  >= 0.85 for clear, well-scoped questions
  >= 0.75 for confident classifications with minor ambiguity
  <  0.75 for genuinely uncertain classifications (will be escalated)

You MUST emit a single JSON object matching the response schema. No \
prose, no markdown, no commentary. The system enforces the JSON shape.
"""


# JSON schema for the PlannerProposal. We pass this to Azure OpenAI's
# response_format so the LLM cannot return free text.
_PROPOSAL_JSON_SCHEMA = {
    "name": "PlannerProposal",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "path",
            "intent_topic",
            "target_candidates",
            "requested_fields",
            "confidence",
            "classification_rationale",
            "multi_intent_detected",
            "filters",
            "output_shape",
            "sort",
            "limit",
        ],
        "properties": {
            "path": {
                "type": "string",
                "enum": [
                    "path_1", "path_2", "path_3", "path_4",
                    "path_5", "path_6", "path_7",
                    "path_8_1", "path_8_2", "path_8_3",
                ],
                "description": "Which path applies. Slice 1 supports path_4, path_8_1, path_8_2, path_8_3.",
            },
            "intent_topic": {
                "type": "string",
                "description": "Per-path intent name (e.g. 'deadline' for Path 4).",
            },
            "target_candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["raw_reference", "proposed_kind"],
                    "properties": {
                        "raw_reference": {"type": "string"},
                        "proposed_kind": {
                            "type": "string",
                            "enum": [
                                "rfq_code",
                                "natural_reference",
                                "page_default",
                                "session_state_pick",
                            ],
                        },
                    },
                },
            },
            "requested_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Empty by default; only fill if user enumerates fields explicitly.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "classification_rationale": {
                "type": "string",
                "description": "One short sentence on why this classification. Audit/debug only.",
            },
            "multi_intent_detected": {"type": "boolean"},
            # Azure's strict json_schema mode requires every object
            # schema to declare additionalProperties: false. ``filters``
            # is Path-3-specific (Slice 1 does not use it) and must be
            # null on every Slice 1 emission. When Path 3 ships, widen
            # this to an explicit object shape with declared properties
            # + required list (strict-mode also requires every property
            # to be in `required`). For now: null only.
            "filters": {"type": "null"},
            "output_shape": {"type": ["string", "null"]},
            "sort": {"type": ["string", "null"]},
            "limit": {"type": ["integer", "null"]},
        },
    },
}


class Planner:
    """GPT-4o structured Planner — emits untrusted ``PlannerProposal``.

    Constructor takes an ``LlmConnector`` so tests can inject a fake.
    The connector's ``complete(messages, max_tokens)`` returns the raw
    assistant text; we parse it as JSON and validate against
    ``PlannerProposal``.
    """

    def __init__(self, llm_connector: LlmConnector):
        self._llm = llm_connector

    def classify(
        self,
        user_message: str,
        history: list | None = None,
        current_rfq_code: str | None = None,
    ) -> PlannerProposal:
        """One LLM call. Returns the untrusted PlannerProposal.

        Raises ``LlmUnreachable`` on connector failures (auth, network,
        timeout, malformed response). The orchestrator catches and
        routes to Path 8.5 ``llm_unavailable``.
        """
        # Build system message; prepend page-context note if present.
        system_content = _SYSTEM_PROMPT
        if current_rfq_code:
            system_content = (
                f"{_SYSTEM_PROMPT}\n"
                f"PAGE CONTEXT: the user is currently viewing RFQ "
                f"{current_rfq_code}. If they ask 'this RFQ' / 'it' / "
                f"don't name an RFQ explicitly, set target_candidates "
                f"to a single page_default entry."
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]
        if history:
            for turn in history:
                # history entries are expected to be {"role": "...", "content": "..."}
                messages.append(turn)
        messages.append({"role": "user", "content": user_message})

        # Call the LLM with Azure's structured-output enforcement
        # (Batch 9.1). response_format pins the JSON shape at the API
        # level -- the parse + Pydantic validation below become defense
        # in depth against an Azure schema bug, not the primary contract.
        #
        # Temperature + max_tokens are mirrored module-level constants
        # below so the Planner stays inside CI guard §11.5.2 (only
        # Factory + Gate may import the registry config). Source of
        # truth lives in src/config/path_registry.py PLANNER_MODEL_CONFIG;
        # an anti-drift test asserts the values stay in sync.
        try:
            raw = self._llm.complete(
                messages,
                max_tokens=_PLANNER_MAX_TOKENS,
                response_format={
                    "type": "json_schema",
                    "json_schema": _PROPOSAL_JSON_SCHEMA,
                },
                temperature=_PLANNER_TEMPERATURE,
            )
        except LlmUnreachable:
            raise  # re-raise as-is; orchestrator routes to 8.5

        # Parse JSON. Defensive: strip code fences if the model wrapped
        # its output despite the instruction.
        cleaned = _strip_json_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Planner returned non-JSON output: %s",
                exc.__class__.__name__,
            )
            raise LlmUnreachable(
                "Planner returned malformed JSON output."
            ) from exc

        try:
            return PlannerProposal.model_validate(data)
        except Exception as exc:
            logger.warning(
                "Planner output failed PlannerProposal schema: %s",
                exc.__class__.__name__,
            )
            raise LlmUnreachable(
                "Planner output did not match the PlannerProposal schema."
            ) from exc


def _strip_json_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences if the model wrapped
    its JSON output. Idempotent if no fence present."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop the first line (```json or ```) and the last fence.
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped
