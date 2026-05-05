"""Path 4 Access stage tests (Batch 5)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.models.execution_state import ResolvedTarget
from src.pipeline.access import check_path_4_access
from src.pipeline.errors import StageError
from tests.conftest import FakeManagerConnector


def _target(rfq_code: str = "IF-0001") -> ResolvedTarget:
    return ResolvedTarget(
        rfq_id=uuid4(),
        rfq_code=rfq_code,
        rfq_label=rfq_code,
        resolution_method="search_by_code",
    )


def test_manager_detail_found_grants_access(actor, fake_manager: FakeManagerConnector):
    fake_manager.set_rfq_detail("IF-0001")
    decision, detail = check_path_4_access(
        target=_target("IF-0001"), actor=actor, manager=fake_manager,
    )
    assert decision.granted is True
    assert detail.rfq_code == "IF-0001"


def test_manager_not_found_routes_to_8_4(actor, fake_manager: FakeManagerConnector):
    fake_manager.mark_not_found("IF-9999")
    with pytest.raises(StageError) as exc_info:
        check_path_4_access(
            target=_target("IF-9999"), actor=actor, manager=fake_manager,
        )
    err = exc_info.value
    assert err.trigger == "access_denied_explicit"
    assert err.source_stage == "access"


def test_manager_unavailable_routes_to_8_5(actor, fake_manager: FakeManagerConnector):
    fake_manager.set_unreachable()
    with pytest.raises(StageError) as exc_info:
        check_path_4_access(
            target=_target("IF-0001"), actor=actor, manager=fake_manager,
        )
    err = exc_info.value
    assert err.trigger == "manager_unreachable"
    assert err.reason_code == "source_unavailable"
    assert err.source_stage == "access"


def test_access_does_not_invent_rfq_data(actor, fake_manager: FakeManagerConnector):
    """Access uses ONLY what the manager returns. No defaulting."""
    fake_manager.set_rfq_detail("IF-0001", deadline=None)  # type: ignore[arg-type]
    # Pydantic will reject deadline=None at DTO construction; this just
    # confirms the fake honors what we set. Test with a valid date instead.
    from datetime import date
    fake_manager.set_rfq_detail("IF-0001", deadline=date(2026, 7, 1), owner="Alice")
    _, detail = check_path_4_access(
        target=_target("IF-0001"), actor=actor, manager=fake_manager,
    )
    assert detail.owner == "Alice"
    assert detail.deadline.isoformat() == "2026-07-01"


# ── Fake alias-symmetry regression (Batch 9.1 PR review fix) ────────────


def test_fake_mark_not_found_propagates_code_to_uuid(actor, fake_manager: FakeManagerConnector):
    """When a test calls ``mark_not_found("IF-0001")`` against an
    already-seeded RFQ, the fake must ALSO raise RfqNotFound on the
    by-id lookup of the same RFQ's UUID. Otherwise UUID-path tests
    silently pass while the real manager would 404 both endpoints."""
    detail = fake_manager.set_rfq_detail("IF-0001")
    fake_manager.mark_not_found("IF-0001")

    # by-code lookup -> not found (the obvious case).
    with pytest.raises(StageError):
        check_path_4_access(
            target=_target("IF-0001"), actor=actor, manager=fake_manager,
        )

    # by-uuid lookup -> ALSO not found (the fix).
    with pytest.raises(StageError):
        check_path_4_access(
            target=_target(str(detail.id)), actor=actor, manager=fake_manager,
        )


def test_fake_mark_not_found_propagates_uuid_to_code(actor, fake_manager: FakeManagerConnector):
    """Symmetric: marking the UUID also marks every code that aliases
    it. Without this, a by-code lookup would silently succeed while
    the real manager would 404."""
    detail = fake_manager.set_rfq_detail("IF-0001")
    fake_manager.mark_not_found(str(detail.id))

    with pytest.raises(StageError):
        check_path_4_access(
            target=_target(str(detail.id)), actor=actor, manager=fake_manager,
        )
    with pytest.raises(StageError):
        check_path_4_access(
            target=_target("IF-0001"), actor=actor, manager=fake_manager,
        )


def test_fake_mark_access_denied_propagates_code_to_uuid(
    actor, fake_manager: FakeManagerConnector,
):
    """Same alias symmetry for mark_access_denied (HTTP 403)."""
    detail = fake_manager.set_rfq_detail("IF-0001")
    fake_manager.mark_access_denied("IF-0001")

    with pytest.raises(StageError) as exc_info:
        check_path_4_access(
            target=_target("IF-0001"), actor=actor, manager=fake_manager,
        )
    assert exc_info.value.trigger == "access_denied_explicit"

    with pytest.raises(StageError) as exc_info:
        check_path_4_access(
            target=_target(str(detail.id)), actor=actor, manager=fake_manager,
        )
    assert exc_info.value.trigger == "access_denied_explicit"
