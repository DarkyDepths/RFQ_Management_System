"""Judge — Stage 11 of the v4 canonical pipeline (Batch 8).

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Judge row) and §7
Risk 2 ("LLM-as-validator paradox" — Judge runs after deterministic
guardrails, not before).

Slice 1 / Batch 8: Judge runs only when Compose ran (i.e., for Path 4
synthesis intents). It verifies the composed draft against the
provided evidence — does NOT rewrite. The orchestrator owns
promote-or-route based on the verdict.

Verdict mapping (when verdict=fail, first violation wins):

* ``fabrication``         -> reason_code ``judge_verdict_fabrication``
* ``forbidden_inference`` -> ``judge_verdict_forbidden_inference``
* ``unsourced_citation``  -> ``judge_verdict_unsourced_citation``
* ``target_isolation``    -> ``target_isolation_violation``
* ``comparison_violation`` -> ``judge_verdict_comparison_violation``

All routed to Path 8.5 by the EscalationGate (Batch 5 matrix). The
Finalizer renders the appropriate template (Batch 8 added these).

Hard discipline:

* No tool selection. No manager calls. No registry config import.
* Verifies; does NOT rewrite.
* Sets ``state.judge_verdict``; raises StageError on fail.
* On LLM unavailable -> StageError ``llm_unavailable`` (Path 8.5).
* On malformed output -> treated as Judge fail (refuse to trust an
  unparseable verdict — fail closed).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from src.connectors.llm_connector import LlmConnector
from src.models.execution_state import ExecutionState, JudgeVerdict, JudgeViolation
from src.models.judge import JUDGE_TRIGGER_TO_REASON_CODE, JudgeInput
from src.models.path_registry import JudgeTriggerName, ReasonCode
from src.pipeline.errors import StageError
from src.utils.errors import LlmUnreachable


logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """\
You are RFQ Copilot Judge for the Gulf Heavy Industries estimation
team. You verify a DRAFT answer against the EVIDENCE.

Your ONLY job: emit a verdict. You do NOT rewrite the answer. You do
NOT improve it. You return JSON.

Check the DRAFT for these violations:

  fabrication             — DRAFT claims a fact not present in EVIDENCE
                            (e.g., a deadline date the evidence
                            doesn't have).
  forbidden_inference     — DRAFT makes a judgment claim like
                            "win probability", "we should bid",
                            "high readiness" — not a factual claim
                            present in EVIDENCE.
  unsourced_citation      — DRAFT cites a specific source / paragraph
                            / standard that isn't in EVIDENCE source
                            refs.
  target_isolation        — DRAFT mixes information across multiple
                            targets when only one was asked about.
  comparison_violation    — DRAFT compares targets in a way the
                            evidence doesn't support.

If you find any violation, set verdict="fail" and add it to violations.
Otherwise verdict="pass" with empty violations.

Output ONLY this JSON. No prose outside it. No markdown fences.

JSON SCHEMA:
{
  "verdict": "pass" | "fail",
  "violations": [
    {
      "trigger": "fabrication" | "forbidden_inference" | "unsourced_citation" | "target_isolation" | "comparison_violation",
      "excerpt": "<the offending phrase from DRAFT>"
    }
  ],
  "rationale": "<one short sentence explaining the verdict>"
}
"""


def judge_path_4(
    state: ExecutionState,
    llm_connector: LlmConnector,
) -> None:
    """Verify ``state.draft_text`` against ``state.evidence_packets``.

    Sets ``state.judge_verdict`` on success. Raises ``StageError`` on
    fail or LLM unavailability — orchestrator routes via gate.

    Must be called AFTER Compose (state.draft_text is required input).
    """
    if not state.draft_text:
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="judge",
            details={"reason": "judge_path_4 called with no state.draft_text"},
        )

    if not state.evidence_packets:
        raise StageError(
            trigger="evidence_empty",
            reason_code=ReasonCode("no_evidence"),
            source_stage="judge",
            details={"reason": "judge_path_4 called with no evidence_packets"},
        )

    target_rfq_code = state.evidence_packets[0].target_label
    triggers_to_check = [
        str(t) for t in (state.plan.judge_policy.triggers if state.plan.judge_policy else [])
    ] or list(JUDGE_TRIGGER_TO_REASON_CODE.keys())

    judge_input = JudgeInput(
        path=state.plan.path.value,
        intent_topic=state.plan.intent_topic,
        target_rfq_code=target_rfq_code,
        draft_text=state.draft_text,
        canonical_requested_fields=list(state.plan.canonical_requested_fields),
        forbidden_fields=list(state.plan.forbidden_fields),
        evidence_packets=[p.model_dump(mode="json") for p in state.evidence_packets],
        triggers_to_check=triggers_to_check,
    )

    user_content = _render_user_prompt(judge_input)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    started = datetime.now(timezone.utc)
    try:
        raw = llm_connector.complete(messages, max_tokens=400)
    except LlmUnreachable as exc:
        logger.warning("Judge LLM unreachable: %s", exc)
        raise StageError(
            trigger="llm_unavailable",
            reason_code=ReasonCode("llm_unavailable"),
            source_stage="judge",
            details={"cause": str(exc)},
        ) from exc

    cleaned = _strip_json_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Fail closed — can't trust an unparseable verdict.
        logger.warning("Judge returned non-JSON output: %s", exc.__class__.__name__)
        raise StageError(
            trigger="judge_verdict_fabrication",
            reason_code=ReasonCode("judge_verdict_fabrication"),
            source_stage="judge",
            details={"reason": "judge returned malformed JSON; failing closed"},
        ) from exc

    raw_verdict = parsed.get("verdict")
    if raw_verdict not in ("pass", "fail"):
        raise StageError(
            trigger="judge_verdict_fabrication",
            reason_code=ReasonCode("judge_verdict_fabrication"),
            source_stage="judge",
            details={"reason": f"judge verdict invalid: {raw_verdict!r}"},
        )

    raw_violations = parsed.get("violations") or []
    violations: list[JudgeViolation] = []
    for v in raw_violations:
        trigger_name = v.get("trigger")
        if trigger_name not in JUDGE_TRIGGER_TO_REASON_CODE:
            # Unknown trigger — treat as fabrication (fail closed).
            trigger_name = "fabrication"
        reason_code_str = JUDGE_TRIGGER_TO_REASON_CODE[trigger_name]
        violations.append(
            JudgeViolation(
                trigger=JudgeTriggerName(trigger_name),
                reason_code=ReasonCode(reason_code_str),
                excerpt=v.get("excerpt"),
            )
        )

    latency_ms = max(
        1,
        int((datetime.now(timezone.utc) - started).total_seconds() * 1000),
    )

    verdict = JudgeVerdict(
        verdict=raw_verdict,
        triggers_checked=[JudgeTriggerName(t) for t in triggers_to_check],
        violations=violations,
        rationale=parsed.get("rationale", ""),
        latency_ms=latency_ms,
    )
    state.judge_verdict = verdict

    if raw_verdict == "fail":
        # First violation drives routing per spec. Use the reason_code
        # value as the StageError trigger so the EscalationGate's
        # trigger->Path map (keyed on reason_code-style names like
        # "judge_verdict_fabrication" / "target_isolation_violation")
        # routes correctly. The JudgeViolation entries on the verdict
        # still carry both the source trigger ("fabrication") and the
        # routed reason_code for forensics.
        if violations:
            first = violations[0]
            raise StageError(
                trigger=str(first.reason_code),
                reason_code=first.reason_code,
                source_stage="judge",
                details={
                    "verdict": "fail",
                    "violations_count": len(violations),
                    "first_judge_trigger": str(first.trigger),
                    "first_excerpt": first.excerpt,
                },
            )
        # verdict=fail with no violations — treat as fabrication.
        raise StageError(
            trigger="judge_verdict_fabrication",
            reason_code=ReasonCode("judge_verdict_fabrication"),
            source_stage="judge",
            details={"reason": "judge verdict=fail but no violations listed"},
        )


def _render_user_prompt(judge_input: JudgeInput) -> str:
    """Build the user-message body — DRAFT, EVIDENCE, CHECK LIST."""
    lines: list[str] = []
    lines.append("DRAFT TO VERIFY:")
    lines.append(judge_input.draft_text)
    lines.append("")
    lines.append("EVIDENCE FIELDS (the only grounded facts):")
    for packet in judge_input.evidence_packets:
        lines.append(f"  Target: {packet.get('target_label', '?')}")
        for field_name, value in (packet.get("fields") or {}).items():
            lines.append(f"    {field_name}: {value}")
        for ref in packet.get("source_refs") or []:
            lines.append(
                f"    [source: {ref.get('source_type', '?')}/"
                f"{ref.get('source_id', '?')}]"
            )
    lines.append("")
    lines.append(
        f"FORBIDDEN FIELDS (these must not appear in DRAFT): "
        f"{', '.join(judge_input.forbidden_fields) or '(none)'}"
    )
    lines.append(
        f"TRIGGERS TO CHECK: {', '.join(judge_input.triggers_to_check)}"
    )
    lines.append("")
    lines.append("Return the verdict JSON now.")
    return "\n".join(lines)


def _strip_json_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped
