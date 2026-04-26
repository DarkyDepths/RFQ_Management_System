"""Manager translator — formats manager DTOs into the RFQ DATA section of the LLM prompt.

Pure function. No side effects. Renders only the approved fields per the
Batch 4 / 4.1 spec; deliberately strips internal IDs, audit metadata,
notes, files, subtasks. Absent fields render as the literal string
"not recorded" so the LLM cannot silently skip them. Truly optional
fields (industry, country) are omitted entirely when null to reduce
prompt noise.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.models.manager_dto import ManagerRfqDetailDto, ManagerRfqStageDto


def format_rfq_for_prompt(
    detail: ManagerRfqDetailDto,
    current_stage: ManagerRfqStageDto | None,
    all_stages: Optional[list[ManagerRfqStageDto]] = None,
) -> str:
    """Render the RFQ DATA section. See module docstring for rules."""
    description = (detail.description or "").strip() or "not recorded"

    lines = [
        f"RFQ Code: {detail.rfq_code or 'not recorded'}",
        f"Title: {detail.name}",
        f"Client: {detail.client}",
        f"Status: {detail.status}",
        f"Progress: {detail.progress}%",
        f"Priority: {detail.priority}",
        f"Owner: {detail.owner}",
        f"Deadline: {detail.deadline.isoformat()}",
        f"Current Stage: {detail.current_stage_name or 'not recorded'}",
        f"Workflow: {detail.workflow_name or 'not recorded'}",
    ]

    # Optional context fields — skip entirely when null to keep prompt tight.
    if detail.industry:
        lines.append(f"Industry: {detail.industry}")
    if detail.country:
        lines.append(f"Country: {detail.country}")

    lines.extend([
        f"Source package: {_format_artifact(detail.source_package_available, detail.source_package_updated_at)}",
        f"Workbook: {_format_artifact(detail.workbook_available, detail.workbook_updated_at)}",
        f"Outcome reason: {detail.outcome_reason or 'not recorded'}",
        f"Last updated: {detail.updated_at.date().isoformat()}",
        f"Description: {description}",
        f"Blocker: {_format_blocker(current_stage)}",
    ])

    # Full stage list (Batch 4.1) — name + status only, one line each.
    # Cheap context that lets the LLM answer "what stages?" / "how many done?".
    if all_stages:
        lines.append("Stages:")
        for stage in sorted(all_stages, key=lambda s: s.order):
            lines.append(f"  {stage.order}. {stage.name} ({stage.status})")

    return "\n".join(lines)


def _format_artifact(available: bool, updated_at: Optional[datetime]) -> str:
    if not available:
        return "not yet received"
    if updated_at is None:
        return "available"
    return f"available since {updated_at.date().isoformat()}"


def _format_blocker(current_stage: ManagerRfqStageDto | None) -> str:
    if current_stage is None:
        return "data not available"
    status = current_stage.blocker_status
    reason = current_stage.blocker_reason_code
    if status == "Blocked":
        return f"ACTIVE ({reason or 'no reason recorded'})"
    if status == "Resolved":
        return "previously blocked, now resolved"
    return "none recorded"
