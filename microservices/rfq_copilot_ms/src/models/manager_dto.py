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
    deadline: date
    current_stage_name: Optional[str] = None
    current_stage_id: Optional[UUID] = None
    priority: str
    owner: str
    description: Optional[str] = None
    outcome_reason: Optional[str] = None
    updated_at: datetime


class ManagerRfqStageDto(BaseModel):
    """Subset of manager's RfqStageResponse needed for blocker extraction."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    order: int
    status: str
    blocker_status: Optional[str] = None
    blocker_reason_code: Optional[str] = None
