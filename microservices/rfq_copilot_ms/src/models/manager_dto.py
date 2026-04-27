"""Pydantic DTOs for rfq_manager_ms HTTP responses.

Snake_case mirrors manager's wire format. We declare only the fields we
consume; extra fields from manager are silently ignored so manager schema
extensions don't break the copilot.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ManagerRfqDetailDto(BaseModel):
    """Subset of manager's RfqDetail consumed by Batch 4 grounding."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    rfq_code: Optional[str] = None
    name: str
    client: str
    status: str
    progress: int = 0
    deadline: date
    current_stage_name: Optional[str] = None
    current_stage_id: Optional[UUID] = None
    workflow_name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    priority: str
    owner: str
    description: Optional[str] = None
    source_package_available: bool = False
    source_package_updated_at: Optional[datetime] = None
    workbook_available: bool = False
    workbook_updated_at: Optional[datetime] = None
    outcome_reason: Optional[str] = None
    updated_at: datetime


class ManagerRfqStageDto(BaseModel):
    """Subset of manager's RfqStageResponse needed for blocker extraction and stage list rendering."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    order: int
    status: str
    blocker_status: Optional[str] = None
    blocker_reason_code: Optional[str] = None


# ── General-mode (portfolio) DTOs ────────────────────────────────────────────


class ManagerPortfolioStatsDto(BaseModel):
    """Subset of manager's RfqStats consumed by Batch 4.2 portfolio grounding."""

    model_config = ConfigDict(extra="ignore")

    total_rfqs_12m: int
    open_rfqs: int
    critical_rfqs: int
    avg_cycle_days: int


class ManagerRfqListItemDto(BaseModel):
    """Subset of manager's RfqSummary for the /rfqs list grounding context."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    rfq_code: Optional[str] = None
    name: str
    client: str
    country: Optional[str] = None
    owner: str
    priority: str
    status: str
    deadline: date
    current_stage_name: Optional[str] = None
    current_stage_blocker_status: Optional[str] = None
    current_stage_blocker_reason_code: Optional[str] = None
