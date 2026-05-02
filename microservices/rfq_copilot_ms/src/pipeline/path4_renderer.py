"""Path 4 grounded renderer — deterministic short-form answers from
manager evidence.

This is **NOT** the LLM Compose stage. It's a per-intent string-builder
that reads the EvidencePacket fields and produces a short, grounded
answer with no synthesis, no inference, and no claims beyond what the
manager DTO actually said.

When LLM Compose ships in a later batch, it'll handle the summary intent
(multi-field synthesis) and richer free-form rendering. The
single-field intents here will likely stay deterministic per §12.6
template-first eligibility.

Slice 1 / Batch 5 supports the 8 Path 4 intents declared in
PATH_CONFIGS:

* deadline       — single field
* owner          — single field
* status         — single field
* current_stage  — single field (current_stage_name)
* priority       — single field
* blockers       — composite (active_blocker structure or "no blocker")
* stages         — composite (ordered name/order/status list)
* summary        — multi-field synthesis (deterministic for Slice 1)

Hard discipline:

* No LLM call.
* No "probably" / "likely" / "seems" — evidence-only language.
* If a field is missing or empty, return None and let the caller route
  to Path 8.5 ``no_evidence`` (Evidence Check should have caught it
  upstream; this is a defensive secondary check).
* Never expose internal labels like "Path 4" or "reason_code" in the
  rendered text.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.models.execution_state import EvidencePacket, ExecutionState


def render_path_4(state: ExecutionState) -> str | None:
    """Render the grounded Path 4 answer or return None if evidence is
    insufficient. The caller (orchestrator) is responsible for
    converting None to a Path 8.5 ``no_evidence`` route.

    Returns the user-facing answer string. Sets nothing on state — that
    happens via the Finalizer (which sees ``state.final_text`` already
    populated and passes through).
    """
    if not state.evidence_packets:
        return None

    intent_topic = state.plan.intent_topic
    packet = state.evidence_packets[0]  # Path 4 = exactly one target
    label = packet.target_label

    renderer = _INTENT_RENDERERS.get(intent_topic)
    if renderer is None:
        # Unknown intent for Path 4 — fall through; orchestrator will
        # route to Path 8.5 no_evidence (defensive). The factory
        # should have rejected at F1 if the intent_topic isn't in
        # PATH_CONFIGS.
        return None

    return renderer(label, packet)


# ── Per-intent renderers ──────────────────────────────────────────────────


def _format_value(value: Any) -> str:
    """Convert manager DTO field values to display strings.

    Dates / datetimes -> ISO-format string. Everything else -> str().
    No locale conversion in Slice 1 — ISO is the unambiguous default.
    """
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _render_deadline(label: str, packet: EvidencePacket) -> str | None:
    value = packet.fields.get("deadline")
    if value is None:
        return None
    return f"{label} deadline is {_format_value(value)}."


def _render_owner(label: str, packet: EvidencePacket) -> str | None:
    value = packet.fields.get("owner")
    if value is None:
        return None
    return f"{label} is owned by {_format_value(value)}."


def _render_status(label: str, packet: EvidencePacket) -> str | None:
    value = packet.fields.get("status")
    if value is None:
        return None
    return f"{label} status is {_format_value(value)}."


def _render_current_stage(label: str, packet: EvidencePacket) -> str | None:
    value = packet.fields.get("current_stage_name")
    if value is None:
        return None
    return f"{label} is currently in {_format_value(value)}."


def _render_priority(label: str, packet: EvidencePacket) -> str | None:
    value = packet.fields.get("priority")
    if value is None:
        return None
    return f"{label} priority is {_format_value(value)}."


def _render_blockers(label: str, packet: EvidencePacket) -> str | None:
    """Three sub-cases:

    * ``active_blocker`` is a dict -> "<label> has a blocker: <reason>"
    * ``active_blocker`` is None  -> "I don't see an active blocker for <label>."
    * key missing                 -> None (caller routes to no_evidence)
    """
    if "active_blocker" not in packet.fields:
        return None
    blocker = packet.fields["active_blocker"]
    if blocker is None:
        return f"I don't see an active blocker for {label}."

    if isinstance(blocker, dict):
        reason = blocker.get("blocker_reason_code") or blocker.get("blocker_status")
        stage_name = blocker.get("stage_name")
        if reason and stage_name:
            return f"{label} has a blocker at the {stage_name} stage: {reason}."
        if reason:
            return f"{label} has a blocker: {reason}."
        return f"{label} has a blocker."
    return None


def _render_stages(label: str, packet: EvidencePacket) -> str | None:
    """Concise ordered list of stage names + statuses."""
    stages = packet.fields.get("stages")
    if not stages or not isinstance(stages, list):
        return None
    lines = [f"{label} stages:"]
    sorted_stages = sorted(
        stages, key=lambda s: s.get("order", 0) if isinstance(s, dict) else 0
    )
    for stage in sorted_stages:
        if not isinstance(stage, dict):
            continue
        name = stage.get("name", "?")
        status = stage.get("status", "?")
        lines.append(f"  - {name} ({status})")
    if len(lines) == 1:
        return None  # no usable stage entries
    return "\n".join(lines)


def _render_summary(label: str, packet: EvidencePacket) -> str | None:
    """4-6 line concise summary using only allowed fields. Fields that
    are missing are skipped — we never invent. The summary is grounded
    in whatever the manager actually surfaced."""
    fields = packet.fields
    lines = [f"{label} summary:"]
    if fields.get("name"):
        lines.append(f"  name: {fields['name']}")
    if fields.get("client"):
        lines.append(f"  client: {fields['client']}")
    if fields.get("status"):
        lines.append(f"  status: {fields['status']}")
    if fields.get("priority"):
        lines.append(f"  priority: {fields['priority']}")
    if fields.get("deadline"):
        lines.append(f"  deadline: {_format_value(fields['deadline'])}")
    if fields.get("current_stage_name"):
        lines.append(f"  current stage: {fields['current_stage_name']}")
    if len(lines) == 1:
        return None  # no fields surfaced — let caller route to no_evidence
    return "\n".join(lines)


_INTENT_RENDERERS = {
    "deadline": _render_deadline,
    "owner": _render_owner,
    "status": _render_status,
    "current_stage": _render_current_stage,
    "priority": _render_priority,
    "blockers": _render_blockers,
    "stages": _render_stages,
    "summary": _render_summary,
}
