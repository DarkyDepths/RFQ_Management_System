"""Shared test fixtures and fakes.

Fakes for ``LlmConnector`` and ``ManagerConnector`` so unit tests never
make real Azure / manager_ms calls. Each fake exposes the same method
surface the production class does, so they slot into
``V2TurnController`` (or any /v2 stage) via constructor injection
without monkeypatching.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Iterable
from uuid import UUID, uuid4

import pytest

from src.models.actor import Actor
from src.models.manager_dto import ManagerRfqDetailDto, ManagerRfqStageDto
from src.utils.errors import LlmUnreachable, ManagerUnreachable, RfqNotFound


# ── Fake LLM connector ────────────────────────────────────────────────────


class FakeLlmConnector:
    """Stand-in for ``src.connectors.llm_connector.LlmConnector``."""

    def __init__(self):
        self.calls: list[dict] = []
        self._responses: list[str] = []
        self._unreachable: bool = False

    def set_response(self, response: str) -> None:
        self._responses = [response]

    def set_responses(self, responses: list[str]) -> None:
        self._responses = list(responses)

    def set_unreachable(self) -> None:
        self._unreachable = True

    def complete(
        self, messages: Iterable[dict[str, str]], max_tokens: int = 500
    ) -> str:
        self.calls.append({"messages": list(messages), "max_tokens": max_tokens})
        if self._unreachable:
            raise LlmUnreachable("Fake LLM marked unreachable.")
        if not self._responses:
            raise AssertionError(
                "FakeLlmConnector.complete() called but no response queued. "
                "Call .set_response(...) before invoking."
            )
        return self._responses.pop(0)


def planner_proposal_json(
    *,
    path: str = "path_4",
    intent_topic: str = "deadline",
    target_candidates: list[dict] | None = None,
    requested_fields: list[str] | None = None,
    confidence: float = 0.9,
    classification_rationale: str = "test fixture",
    multi_intent_detected: bool = False,
    filters: dict | None = None,
    output_shape: str | None = None,
    sort: str | None = None,
    limit: int | None = None,
) -> str:
    """Build a JSON string matching the PlannerProposal schema."""
    if target_candidates is None:
        target_candidates = [
            {"raw_reference": "IF-0001", "proposed_kind": "rfq_code"}
        ]
    payload = {
        "path": path,
        "intent_topic": intent_topic,
        "target_candidates": target_candidates,
        "requested_fields": requested_fields or [],
        "confidence": confidence,
        "classification_rationale": classification_rationale,
        "multi_intent_detected": multi_intent_detected,
        "filters": filters,
        "output_shape": output_shape,
        "sort": sort,
        "limit": limit,
    }
    return json.dumps(payload)


# ── Fake manager connector ───────────────────────────────────────────────


class FakeManagerConnector:
    """Stand-in for ``src.connectors.manager_ms_connector.ManagerConnector``."""

    def __init__(self):
        self._details: dict[str, ManagerRfqDetailDto] = {}
        self._stages: dict[str, list[ManagerRfqStageDto]] = {}
        self._unreachable: bool = False
        self._not_found: set[str] = set()
        self.calls: list[tuple[str, str, str]] = []

    def set_unreachable(self) -> None:
        self._unreachable = True

    def mark_not_found(self, rfq_code: str) -> None:
        self._not_found.add(rfq_code)

    def set_rfq_detail(
        self,
        rfq_code: str,
        *,
        rfq_id: UUID | None = None,
        name: str = "Test RFQ",
        client: str = "Test Client",
        status: str = "In preparation",
        progress: int = 50,
        deadline: date | None = None,
        current_stage_name: str | None = "Cost estimation",
        current_stage_id: UUID | None = None,
        workflow_name: str | None = "Standard Workflow",
        priority: str = "Critical",
        owner: str = "Mohamed",
        description: str | None = None,
    ) -> ManagerRfqDetailDto:
        detail = ManagerRfqDetailDto(
            id=rfq_id or uuid4(),
            rfq_code=rfq_code,
            name=name,
            client=client,
            status=status,
            progress=progress,
            deadline=deadline or date(2026, 6, 15),
            current_stage_name=current_stage_name,
            current_stage_id=current_stage_id or uuid4(),
            workflow_name=workflow_name,
            priority=priority,
            owner=owner,
            description=description,
            updated_at=datetime(2026, 5, 1, 12, 0, 0),
        )
        self._details[rfq_code] = detail
        return detail

    def set_rfq_stages(
        self,
        rfq_code: str,
        stages: list[dict],
    ) -> list[ManagerRfqStageDto]:
        objs = []
        for s in stages:
            objs.append(
                ManagerRfqStageDto(
                    id=s.get("id", uuid4()),
                    name=s["name"],
                    order=s["order"],
                    status=s["status"],
                    blocker_status=s.get("blocker_status"),
                    blocker_reason_code=s.get("blocker_reason_code"),
                )
            )
        self._stages[rfq_code] = objs
        return objs

    def get_rfq_detail(self, rfq_id: str, actor: Actor) -> ManagerRfqDetailDto:
        self.calls.append(("get_rfq_detail", rfq_id, actor.user_id))
        if self._unreachable:
            raise ManagerUnreachable("Fake manager marked unreachable.")
        if rfq_id in self._not_found:
            raise RfqNotFound(f"Fake manager: {rfq_id} not found.")
        if rfq_id not in self._details:
            raise RfqNotFound(f"Fake manager has no detail set for {rfq_id}.")
        return self._details[rfq_id]

    def get_rfq_stages(
        self, rfq_id: str, actor: Actor
    ) -> list[ManagerRfqStageDto]:
        self.calls.append(("get_rfq_stages", rfq_id, actor.user_id))
        if self._unreachable:
            raise ManagerUnreachable("Fake manager marked unreachable.")
        if rfq_id in self._not_found:
            raise RfqNotFound(f"Fake manager: {rfq_id} not found.")
        return list(self._stages.get(rfq_id, []))


# ── pytest fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def fake_llm() -> FakeLlmConnector:
    return FakeLlmConnector()


@pytest.fixture
def fake_manager() -> FakeManagerConnector:
    return FakeManagerConnector()


@pytest.fixture
def actor() -> Actor:
    return Actor(user_id="u1", display_name="User One", role="estimator")
