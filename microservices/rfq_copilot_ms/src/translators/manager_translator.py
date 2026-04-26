"""Manager translator — formats manager DTOs into the RFQ DATA section of the LLM prompt.

Pure function. No side effects. Renders only the approved fields per the
Batch 4 spec; deliberately strips internal IDs, audit metadata, workflow
internals, source/workbook flags, and full notes/files/subtasks. Absent
fields render as the literal string "not recorded" so the LLM cannot
silently skip them.
"""

from __future__ import annotations

from src.models.manager_dto import ManagerRfqDetailDto, ManagerRfqStageDto


def format_rfq_for_prompt(
    detail: ManagerRfqDetailDto,
    current_stage: ManagerRfqStageDto | None,
) -> str:
    """Render the RFQ DATA section. See module docstring for rules."""
    description = (detail.description or "").strip() or "not recorded"

    lines = [
        f"RFQ Code: {detail.rfq_code or 'not recorded'}",
        f"Title: {detail.name}",
        f"Client: {detail.client}",
        f"Status: {detail.status}",
        f"Current Stage: {detail.current_stage_name or 'not recorded'}",
        f"Priority: {detail.priority}",
        f"Owner: {detail.owner}",
        f"Deadline: {detail.deadline.isoformat()}",
        f"Outcome reason: {detail.outcome_reason or 'not recorded'}",
        f"Last updated: {detail.updated_at.date().isoformat()}",
        f"Description: {description}",
        f"Blocker: {_format_blocker(current_stage)}",
    ]
    return "\n".join(lines)


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
