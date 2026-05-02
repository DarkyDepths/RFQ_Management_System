"""Deterministic guardrails — Stage 10 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Guardrails row) and
§7 Risk 4 ("the agreeable LLM trap").

Slice 1 / Batch 7 implements 5 deterministic guardrails for Path 4:

* ``evidence``       — answer must be backed by EvidencePacket data;
                       fail to ``no_evidence`` if final_text is non-empty
                       but no evidence was packed.
* ``forbidden_field``— answer must not surface forbidden field names
                       (``margin``, ``win_probability``, etc. from
                       ``plan.forbidden_fields``).
* ``internal_label`` — answer must not leak architecture internals like
                       ``path_4`` / ``reason_code`` /
                       ``ExecutionPlanFactory`` etc.
* ``scope``          — Path 4 answer must stay about operational manager
                       data; no readiness / win-prediction / workbook-
                       review / cost-prediction / bid-strategy claims.
* ``shape``          — answer must be concise, non-empty, and free of
                       raw JSON / Python repr / stack traces / debug
                       dumps.

Hard discipline:

* No LLM call. No manager call. No registry config import.
* No ``TurnExecutionPlan`` instantiation.
* Read-only on EvidencePacket — never modifies, never invents facts.
* On pass: silent (no return value mutation).
* On fail: raise :class:`StageError` with the right trigger /
  reason_code so the orchestrator routes via the Escalation Gate to
  Path 8.5.

Failure routing (per freeze §6 escalation matrix):

* evidence -> ``no_evidence`` (8.5)
* forbidden_field / internal_label / scope / shape ->
  ``forbidden_inference_detected_deterministic`` (8.5)

The dispatcher honors ``state.plan.active_guardrails`` — only guardrails
the registry declared for this path run. PATH_CONFIGS Path 4 declares
all 5 in Batch 7 so they all execute. Adding a guardrail requires
adding the registry entry AND the function below.
"""

from __future__ import annotations

import re
from typing import Callable

from src.models.execution_state import ExecutionState
from src.models.path_registry import GuardrailId, ReasonCode
from src.pipeline.errors import StageError


# ── Forbidden tokens ─────────────────────────────────────────────────────


# Internal architecture labels that must NEVER appear in user-facing text.
# Each entry is a substring (case-sensitive — internal labels use specific
# casing). Watch out for false positives: keep tokens specific.
_INTERNAL_LABEL_TOKENS: tuple[str, ...] = (
    "path_1", "path_2", "path_3", "path_4",
    "path_5", "path_6", "path_7",
    "path_8_1", "path_8_2", "path_8_3", "path_8_4", "path_8_5",
    "PATH_1", "PATH_2", "PATH_3", "PATH_4",
    "PATH_8_1", "PATH_8_2", "PATH_8_3", "PATH_8_4", "PATH_8_5",
    "PathId",
    "TurnExecutionPlan",
    "FactoryRejection",
    "EvidencePacket",
    "EscalationRequest",
    "EscalationGate",
    "ExecutionPlanFactory",
    "PlannerValidator",
    "PlannerProposal",
    "ValidatedPlannerProposal",
    "IntakeSource",
    "IntakeDecision",
    "ExecutionState",
    "reason_code",
    "finalizer_template_key",
    "intent_topic",
    "factory_rule",
)


# Out-of-scope intelligence / judgment phrases that Path 4 must never
# produce. Path 4 is operational manager-grounded data ONLY.
# Lower-cased substring matches; word boundaries enforced for words
# that have legitimate operational uses.
_SCOPE_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "win probability",
    "win prediction",
    "win likelihood",
    "bid strategy",
    "bid quality",
    "workbook review",
    "workbook readiness",
    "cost prediction",
    "cost forecast",
    "estimation quality",
    "readiness assessment",
    "readiness score",
    "intelligence summary",
    "briefing summary",
    "competitive ranking",
    "we should bid",
    "we should not bid",
    "you should bid",
    "you should not bid",
    "recommended bid",
    "predicted winner",
)


# Debug-dump indicators in the answer body. Even one of these is a
# strong signal the renderer leaked an exception trace or repr.
_SHAPE_FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Traceback \(most recent call last\):"),
    re.compile(r'\bFile ".*", line \d+, in '),
    re.compile(r"<[\w\.]+ object at 0x[0-9a-fA-F]+>"),
    re.compile(r"<class '[\w\.]+'>"),
    re.compile(r"\bpydantic_core\b"),
    re.compile(r"\bValidationError\b"),
    re.compile(r"\bNotImplementedError\b"),
    re.compile(r"\bAttributeError\b"),
    re.compile(r"\bKeyError\b"),
)


# Maximum reasonable Path 4 answer length. Longer than this is almost
# certainly a debug dump. Path 4 answers are short by design (single
# field or short summary). Bumped generously to allow stages list /
# multi-line summary.
_MAX_PATH_4_ANSWER_CHARS: int = 3000


# ── Per-guardrail implementations ────────────────────────────────────────


def evidence_guardrail(state: ExecutionState) -> None:
    """Fail if Path 4 produced a non-empty answer without evidence.

    The renderer should already have returned None on missing evidence
    (and Evidence Check would have raised) — this is a defense-in-depth
    backstop. If somehow ``state.final_text`` is set but no
    EvidencePacket was packed, the answer is ungrounded by definition.
    """
    if not state.final_text:
        return  # nothing to guard
    if not state.evidence_packets:
        raise StageError(
            trigger="evidence_empty",
            reason_code=ReasonCode("no_evidence"),
            source_stage="guardrail",
            details={
                "guardrail": "evidence",
                "reason": "final_text populated but no evidence_packets",
            },
        )


def forbidden_field_guardrail(state: ExecutionState) -> None:
    """Fail if final_text mentions any forbidden field name.

    Reads the forbidden list from ``state.plan.forbidden_fields`` (the
    factory copied this from the registry). For Path 4 the default
    list includes ``margin``, ``bid_amount``, ``internal_cost``,
    ``win_probability``, ``ranking``, ``winner``, ``estimation_quality``.

    Uses word-boundary regex so e.g. "margin" doesn't match inside
    a longer legitimate word. Case-insensitive.
    """
    if not state.final_text:
        return
    text = state.final_text
    for field_name in state.plan.forbidden_fields:
        if not field_name:
            continue
        # Word-boundary, case-insensitive. Treat underscores as word
        # chars so "win_probability" matches as one token.
        pattern = re.compile(rf"\b{re.escape(field_name)}\b", re.IGNORECASE)
        match = pattern.search(text)
        if match is not None:
            raise StageError(
                trigger="forbidden_inference_detected_deterministic",
                reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
                source_stage="guardrail",
                details={
                    "guardrail": "forbidden_field",
                    "field_name": field_name,
                    "match_position": match.start(),
                },
            )


def internal_label_guardrail(state: ExecutionState) -> None:
    """Fail if final_text leaks internal architecture labels.

    Examples: ``path_4``, ``PATH_8_5``, ``reason_code``,
    ``ExecutionPlanFactory``, ``TurnExecutionPlan``, etc.

    Case-sensitive substring match: internal labels have specific
    casing (snake_case lowercase or PascalCase). Case-insensitive
    matching would create false positives ("path" appears in legitimate
    answers like "the workflow path").
    """
    if not state.final_text:
        return
    text = state.final_text
    for token in _INTERNAL_LABEL_TOKENS:
        if token in text:
            raise StageError(
                trigger="forbidden_inference_detected_deterministic",
                reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
                source_stage="guardrail",
                details={
                    "guardrail": "internal_label",
                    "token": token,
                },
            )


def scope_guardrail(state: ExecutionState) -> None:
    """Fail if final_text drifts into intelligence / judgment territory.

    Path 4 is operational manager-grounded data ONLY. Readiness,
    win-prediction, workbook-review, cost-prediction, bid-strategy
    are all out of scope (Path 5 / Path 7 territory in the freeze).
    """
    if not state.final_text:
        return
    text_lower = state.final_text.lower()
    for phrase in _SCOPE_FORBIDDEN_PHRASES:
        if phrase in text_lower:
            raise StageError(
                trigger="forbidden_inference_detected_deterministic",
                reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
                source_stage="guardrail",
                details={
                    "guardrail": "scope",
                    "phrase": phrase,
                },
            )


def shape_guardrail(state: ExecutionState) -> None:
    """Fail if final_text shape indicates debug leakage.

    Checks:
    * Empty / whitespace-only.
    * Starts with raw JSON ('{' or '[').
    * Contains stack traces, Python repr, or known debug patterns.
    * Excessive length (almost certainly a dump).
    """
    if state.final_text is None:
        # Other guardrails skip on None text; shape catches it as
        # "empty answer" — Path 4 must always produce an answer.
        raise StageError(
            trigger="forbidden_inference_detected_deterministic",
            reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
            source_stage="guardrail",
            details={
                "guardrail": "shape",
                "reason": "final_text is None",
            },
        )
    text = state.final_text
    if not text.strip():
        raise StageError(
            trigger="forbidden_inference_detected_deterministic",
            reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
            source_stage="guardrail",
            details={
                "guardrail": "shape",
                "reason": "final_text is empty / whitespace only",
            },
        )

    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        raise StageError(
            trigger="forbidden_inference_detected_deterministic",
            reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
            source_stage="guardrail",
            details={
                "guardrail": "shape",
                "reason": "final_text begins with raw JSON",
            },
        )

    if len(text) > _MAX_PATH_4_ANSWER_CHARS:
        raise StageError(
            trigger="forbidden_inference_detected_deterministic",
            reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
            source_stage="guardrail",
            details={
                "guardrail": "shape",
                "reason": "final_text exceeds max length",
                "length": len(text),
                "max_length": _MAX_PATH_4_ANSWER_CHARS,
            },
        )

    for pattern in _SHAPE_FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            raise StageError(
                trigger="forbidden_inference_detected_deterministic",
                reason_code=ReasonCode("forbidden_inference_detected_deterministic"),
                source_stage="guardrail",
                details={
                    "guardrail": "shape",
                    "reason": "final_text contains debug-dump pattern",
                    "pattern": pattern.pattern,
                },
            )


# ── Dispatcher ───────────────────────────────────────────────────────────


_GUARDRAIL_REGISTRY: dict[str, Callable[[ExecutionState], None]] = {
    "evidence": evidence_guardrail,
    "forbidden_field": forbidden_field_guardrail,
    "internal_label": internal_label_guardrail,
    "scope": scope_guardrail,
    "shape": shape_guardrail,
}


def run_path_4_guardrails(state: ExecutionState) -> None:
    """Run the guardrails declared on ``state.plan.active_guardrails``,
    in declaration order. First failure raises ``StageError``.

    A guardrail name in ``active_guardrails`` that has no
    implementation in ``_GUARDRAIL_REGISTRY`` is silently skipped
    (defense in depth — adding a guardrail to the registry config
    without a function shouldn't crash the pipeline).
    """
    for guardrail_id in state.plan.active_guardrails:
        name = str(guardrail_id)
        guardrail_fn = _GUARDRAIL_REGISTRY.get(name)
        if guardrail_fn is None:
            continue
        guardrail_fn(state)


# Public registry accessor for tests / introspection.
def known_guardrails() -> list[str]:
    """Return the sorted list of guardrail names this module implements."""
    return sorted(_GUARDRAIL_REGISTRY.keys())
