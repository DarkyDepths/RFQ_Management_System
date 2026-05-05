"""Shared test fixtures and fakes.

Fakes for ``LlmConnector`` and ``ManagerConnector`` so unit tests never
make real Azure / manager_ms calls. Each fake exposes the same method
surface the production class does, so they slot into
``V2TurnController`` (or any /v2 stage) via constructor injection
without monkeypatching.

Batch 9.1 changes (driven by the cross-service audit):

* ``FakeLlmConnector.complete`` accepts and records ``response_format``
  and ``temperature`` kwargs. The fake doesn't enforce the schema —
  tests still queue valid JSON — but recording lets anti-drift tests
  assert that the production callers DO pass them.

* ``FakeManagerConnector`` now keys its detail/stages stores by UUID
  (matching the real manager) with a separate code→UUID index.
  ``get_rfq_detail(uuid)`` and ``get_rfq_detail_by_code(code)`` are
  separate methods, mirroring the real connector. The previous
  by-code-only fake was the latent contract drift behind Batch 9.1.

* Default priority on ``set_rfq_detail`` is the lowercase
  ``"critical"`` to match the manager's ``Literal["normal", "critical"]``
  contract. Tests that care about case can pass an explicit value.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Iterable
from uuid import UUID, uuid4

import pytest

from src.models.actor import Actor
from src.models.manager_dto import ManagerRfqDetailDto, ManagerRfqStageDto
from src.utils.errors import (
    LlmUnreachable,
    ManagerAuthFailed,
    ManagerUnreachable,
    RfqAccessDenied,
    RfqNotFound,
)


# ── Fake LLM connector ────────────────────────────────────────────────────


class FakeLlmConnector:
    """Stand-in for ``src.connectors.llm_connector.LlmConnector``.

    Records ``response_format`` and ``temperature`` per call (Batch 9.1)
    so anti-drift tests can verify Planner / Compose / Judge actually
    pass them.
    """

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
        self,
        messages: Iterable[dict[str, str]],
        max_tokens: int = 500,
        *,
        response_format: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> str:
        self.calls.append({
            "messages": list(messages),
            "max_tokens": max_tokens,
            "response_format": response_format,
            "temperature": temperature,
        })
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
    """Stand-in for ``src.connectors.manager_ms_connector.ManagerConnector``.

    Models the real manager's identifier semantics (Batch 9.1):

    * Detail + stages are stored keyed by UUID (matches the real DB
      primary key).
    * A code -> UUID index allows by-code lookups; ``rfq_code`` is the
      friendly identifier the planner extracts from user messages.
    * ``get_rfq_detail(uuid)`` and ``get_rfq_detail_by_code(code)``
      are separate methods, mirroring the real connector. Mixing them
      (passing a code to the by-id method, or vice versa) raises a
      not-found just like the real manager would.

    Convenience for tests: ``set_rfq_detail("IF-0001", ...)`` creates a
    record with the given code AND a generated UUID; both lookups work.
    Authors can also pass ``rfq_id=<uuid>`` to fix the UUID for tests
    that need a specific value (e.g. /v1 paths that send UUIDs).
    """

    def __init__(self):
        # Internal stores keyed by UUID (string form).
        self._details_by_uuid: dict[str, ManagerRfqDetailDto] = {}
        self._stages_by_uuid: dict[str, list[ManagerRfqStageDto]] = {}
        # Friendly-code -> UUID index for by-code lookups.
        self._uuid_by_code: dict[str, str] = {}

        self._unreachable: bool = False
        # Per-identifier outage simulation.
        self._not_found_codes: set[str] = set()
        self._not_found_uuids: set[str] = set()
        self._access_denied_codes: set[str] = set()
        self._access_denied_uuids: set[str] = set()
        self._auth_failed: bool = False

        self.calls: list[tuple[str, str, str]] = []

    # ── Outage / failure simulation helpers ─────────────────────────────

    def set_unreachable(self) -> None:
        """Network-level outage: ALL calls raise ManagerUnreachable."""
        self._unreachable = True

    def set_auth_failed(self) -> None:
        """Manager rejects auth (HTTP 401): ALL calls raise ManagerAuthFailed."""
        self._auth_failed = True

    def mark_not_found(self, identifier: str) -> None:
        """Make the given identifier (code OR UUID string) raise
        RfqNotFound on lookup -- AND any aliased identifier the same
        RFQ might be looked up by.

        The real manager returns 404 on both the by-id and the by-code
        endpoints for the same RFQ. The fake mirrors this: marking
        ``IF-0001`` as not-found also marks the UUID it aliases (and
        vice versa) so a UUID-path lookup of the same RFQ doesn't
        silently succeed and hide regressions (Batch 9.1 PR review).
        """
        self._not_found_codes.add(identifier)
        self._not_found_uuids.add(identifier)
        self._mark_aliases(identifier, self._not_found_codes, self._not_found_uuids)

    def mark_access_denied(self, identifier: str) -> None:
        """Make the given identifier (code OR UUID string) raise
        RfqAccessDenied (HTTP 403) on lookup -- AND any aliased
        identifier. Same alias-symmetry as ``mark_not_found``."""
        self._access_denied_codes.add(identifier)
        self._access_denied_uuids.add(identifier)
        self._mark_aliases(
            identifier, self._access_denied_codes, self._access_denied_uuids,
        )

    def _mark_aliases(
        self,
        identifier: str,
        codes_set: set[str],
        uuids_set: set[str],
    ) -> None:
        """Cross-populate code <-> UUID for a given identifier so a
        single mark_*() call covers both endpoint shapes the same RFQ
        is reachable at. Reused by mark_not_found / mark_access_denied."""
        # If identifier is a CODE we know about, also mark its UUID.
        uuid_alias = self._uuid_by_code.get(identifier)
        if uuid_alias is not None:
            uuids_set.add(uuid_alias)
        # If identifier is a UUID we know about, also mark every CODE
        # that aliases it (typically one).
        for code, uid in self._uuid_by_code.items():
            if uid == identifier:
                codes_set.add(code)

    # ── Seed helpers ────────────────────────────────────────────────────

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
        priority: str = "critical",  # Batch 9.1: lowercase to match manager
        owner: str = "Mohamed",
        description: str | None = None,
    ) -> ManagerRfqDetailDto:
        uid = rfq_id or uuid4()
        detail = ManagerRfqDetailDto(
            id=uid,
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
        self._details_by_uuid[str(uid)] = detail
        if rfq_code:
            self._uuid_by_code[rfq_code] = str(uid)
        return detail

    def set_rfq_stages(
        self,
        rfq_code: str,
        stages: list[dict],
    ) -> list[ManagerRfqStageDto]:
        """Seed stages for an RFQ. ``rfq_code`` must have been seeded
        via ``set_rfq_detail`` first so the code -> UUID index exists.

        Tests that don't care about details can call ``set_rfq_detail``
        with default values.
        """
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
        if rfq_code not in self._uuid_by_code:
            # Auto-seed a detail with default values so by-code stage
            # lookups succeed without forcing every test to seed both.
            self.set_rfq_detail(rfq_code)
        uid = self._uuid_by_code[rfq_code]
        self._stages_by_uuid[uid] = objs
        return objs

    # ── Lookup methods (mirror the real connector) ──────────────────────

    def get_rfq_detail(self, rfq_id: str, actor: Actor) -> ManagerRfqDetailDto:
        """By-UUID lookup. Mirrors GET /rfqs/{uuid}.

        Note: passing a friendly code (e.g. 'IF-0001') here will NOT
        resolve — same as the real manager. Use
        ``get_rfq_detail_by_code`` for code-based lookups.
        """
        self.calls.append(("get_rfq_detail", rfq_id, actor.user_id))
        self._raise_if_outage(rfq_id, by_code=False)
        if rfq_id not in self._details_by_uuid:
            raise RfqNotFound(f"Fake manager has no detail for UUID {rfq_id}.")
        return self._details_by_uuid[rfq_id]

    def get_rfq_detail_by_code(
        self, rfq_code: str, actor: Actor,
    ) -> ManagerRfqDetailDto:
        """By-code lookup. Mirrors GET /rfqs/by-code/{code} (Batch 9.1)."""
        self.calls.append(("get_rfq_detail_by_code", rfq_code, actor.user_id))
        self._raise_if_outage(rfq_code, by_code=True)
        uid = self._uuid_by_code.get(rfq_code)
        if uid is None:
            raise RfqNotFound(f"Fake manager has no RFQ with code {rfq_code!r}.")
        return self._details_by_uuid[uid]

    def get_rfq_stages(
        self, rfq_id: str, actor: Actor
    ) -> list[ManagerRfqStageDto]:
        """By-UUID stages lookup. Mirrors GET /rfqs/{uuid}/stages."""
        self.calls.append(("get_rfq_stages", rfq_id, actor.user_id))
        self._raise_if_outage(rfq_id, by_code=False)
        if rfq_id not in self._details_by_uuid:
            raise RfqNotFound(f"Fake manager has no RFQ for UUID {rfq_id}.")
        return list(self._stages_by_uuid.get(rfq_id, []))

    def get_rfq_stages_by_code(
        self, rfq_code: str, actor: Actor,
    ) -> list[ManagerRfqStageDto]:
        """By-code stages lookup. Mirrors GET /rfqs/by-code/{code}/stages
        (Batch 9.1)."""
        self.calls.append(("get_rfq_stages_by_code", rfq_code, actor.user_id))
        self._raise_if_outage(rfq_code, by_code=True)
        uid = self._uuid_by_code.get(rfq_code)
        if uid is None:
            raise RfqNotFound(f"Fake manager has no RFQ with code {rfq_code!r}.")
        return list(self._stages_by_uuid.get(uid, []))

    # ── Internals ───────────────────────────────────────────────────────

    def _raise_if_outage(self, identifier: str, *, by_code: bool) -> None:
        """Apply the configured outage / not-found / access-denied
        behavior in the priority order: network outage > auth fail >
        per-identifier denial > per-identifier not-found."""
        if self._unreachable:
            raise ManagerUnreachable("Fake manager marked unreachable.")
        if self._auth_failed:
            raise ManagerAuthFailed("Fake manager: auth rejected (401).")
        denied = (
            self._access_denied_codes if by_code else self._access_denied_uuids
        )
        if identifier in denied:
            raise RfqAccessDenied(
                f"Fake manager: access denied for {identifier!r} (403)."
            )
        not_found = (
            self._not_found_codes if by_code else self._not_found_uuids
        )
        if identifier in not_found:
            raise RfqNotFound(f"Fake manager: {identifier} not found (404).")


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


# ── In-memory SQLite fixture for persistence tests ───────────────────────


@pytest.fixture
def db_session():
    """Yield a SQLAlchemy session bound to a fresh in-memory SQLite DB.

    Uses ``StaticPool`` so all sessions in the test share one connection
    (otherwise ``:memory:`` SQLite gives each connection its own private
    DB and the schema vanishes).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from src.database import Base
    # Import every ORM model so Base.metadata.create_all sees them.
    from src.models.db import (  # noqa: F401
        AuditLogRow,
        ExecutionRecordRow,
        ThreadRow,
        TurnRow,
    )

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionFactory = sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
