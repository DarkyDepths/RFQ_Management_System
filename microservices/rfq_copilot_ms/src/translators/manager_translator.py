"""Manager translator — formats manager DTOs into prompt context sections.

Pure functions. No side effects. Renders only approved fields per the
Batch 4 / 4.1 / 4.2 spec; deliberately strips internal IDs, audit
metadata, notes, files, subtasks. Absent fields render as the literal
string "not recorded" so the LLM cannot silently skip them. Truly
optional context fields (industry, country) are omitted entirely when
null to reduce prompt noise.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.models.manager_dto import (
    ManagerPortfolioStatsDto,
    ManagerRfqDetailDto,
    ManagerRfqListItemDto,
    ManagerRfqStageDto,
)


# ── RFQ-bound mode (single RFQ context) ─────────────────────────────────────


def format_rfq_for_prompt(
    detail: ManagerRfqDetailDto,
    current_stage: ManagerRfqStageDto | None,
    all_stages: Optional[list[ManagerRfqStageDto]] = None,
) -> str:
    """Render the RFQ DATA section for rfq_bound mode."""
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

    if all_stages:
        lines.append("Stages:")
        for stage in sorted(all_stages, key=lambda s: s.order):
            lines.append(f"  {stage.order}. {stage.name} ({stage.status})")

    return "\n".join(lines)


# ── General mode (portfolio context) ────────────────────────────────────────


def format_portfolio_for_prompt(
    stats: ManagerPortfolioStatsDto,
    rfqs: list[ManagerRfqListItemDto],
) -> str:
    """Render the PORTFOLIO DATA section for general mode."""
    lines = [
        "[PORTFOLIO STATS]",
        f"Total RFQs (last 12 months): {stats.total_rfqs_12m}",
        f"Open RFQs: {stats.open_rfqs}",
        f"Critical RFQs: {stats.critical_rfqs}",
        f"Average cycle days: {stats.avg_cycle_days}",
    ]

    if not rfqs:
        lines.extend(["", "[RFQs] none returned"])
        return "\n".join(lines)

    lines.extend(["", f"[RFQs (top {len(rfqs)} by deadline ascending)]"])
    for index, rfq in enumerate(rfqs, start=1):
        lines.append(_format_rfq_list_item(index, rfq))
    return "\n".join(lines)


def _format_rfq_list_item(index: int, rfq: ManagerRfqListItemDto) -> str:
    code = rfq.rfq_code or "no-code"
    blocker = _format_list_blocker(
        rfq.current_stage_blocker_status,
        rfq.current_stage_blocker_reason_code,
    )
    stage = rfq.current_stage_name or "unknown"
    return (
        f'{index}. [{code}] "{rfq.name}" '
        f"| client={rfq.client} | owner={rfq.owner} "
        f"| deadline={rfq.deadline.isoformat()} "
        f"| stage={stage} | status={rfq.status} "
        f"| priority={rfq.priority} | blocker={blocker}"
    )


def _format_list_blocker(
    blocker_status: Optional[str],
    reason_code: Optional[str],
) -> str:
    if blocker_status == "Blocked":
        return f"ACTIVE ({reason_code or 'no reason'})"
    if blocker_status == "Resolved":
        return "resolved"
    return "none"


# ── Shared helpers ──────────────────────────────────────────────────────────


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
