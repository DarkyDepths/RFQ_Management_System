"""Tests for the by-code lookup endpoints + supporting layers.

Covers:

* ``RfqDatasource.get_by_code`` — returns row / None / handles empty input.
* ``RfqController.get_by_code`` — raises NotFoundError on miss; returns
  the same ``RfqDetail`` shape as the by-id ``get`` method.
* ``RfqStageController.list_by_code`` — raises NotFoundError on miss;
  returns the same shape as ``list``.
* HTTP routes:
    - ``GET /rfqs/by-code/{rfq_code}`` returns 200 with the RFQ detail.
    - ``GET /rfqs/by-code/{rfq_code}`` returns 404 for an unknown code.
    - ``GET /rfqs/by-code/{rfq_code}/stages`` returns 200 with stages.
    - ``GET /rfqs/by-code/{rfq_code}/stages`` returns 404 for an unknown code.
    - Route ordering: ``/by-code/...`` must NOT collide with ``/{rfq_id}``
      (regression — FastAPI routes match in declaration order).

The by-code endpoints are added so callers that only know an RFQ's
human-readable code (e.g. the rfq_copilot_ms planner extracts
``IF-0001`` from a user message) can fetch detail + stages without a
prior list-and-filter to discover the UUID. They share storage and
return the same Pydantic schemas as the existing UUID-based endpoints.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.controllers.rfq_controller import RfqController
from src.controllers.rfq_stage_controller import RfqStageController
from src.datasources.rfq_datasource import RfqDatasource
from src.datasources.rfq_stage_datasource import RfqStageDatasource
from src.datasources.workflow_datasource import WorkflowDatasource
from src.models.rfq import RFQ
from src.models.rfq_stage import RFQStage
from src.models.workflow import Workflow
from src.utils.errors import NotFoundError


# ── Fixtures ─────────────────────────────────────────────────────────────


def _create_workflow(db_session, code: str = "WF-BY-CODE") -> Workflow:
    workflow = Workflow(
        name="By-Code Test Workflow", code=code, description="test workflow"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    return workflow


def _insert_rfq(
    db_session,
    workflow_id,
    *,
    rfq_code: str,
    name: str = "Test RFQ",
    client: str = "Test Client",
    priority: str = "normal",
    status: str = "In preparation",
) -> RFQ:
    rfq = RFQ(
        name=name,
        client=client,
        deadline=date(2030, 1, 1),
        owner="Test Owner",
        workflow_id=workflow_id,
        rfq_code=rfq_code,
        status=status,
        progress=0,
        priority=priority,
    )
    db_session.add(rfq)
    db_session.commit()
    db_session.refresh(rfq)
    return rfq


def _insert_stage(
    db_session,
    rfq_id,
    *,
    name: str,
    order: int,
    status: str = "Pending",
    blocker_status: str | None = None,
    blocker_reason_code: str | None = None,
) -> RFQStage:
    stage = RFQStage(
        rfq_id=rfq_id,
        name=name,
        order=order,
        status=status,
        progress=0,
        blocker_status=blocker_status,
        blocker_reason_code=blocker_reason_code,
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)
    return stage


# ── Datasource layer ────────────────────────────────────────────────────


def test_datasource_get_by_code_returns_row_when_present(db_session):
    workflow = _create_workflow(db_session)
    rfq = _insert_rfq(db_session, workflow.id, rfq_code="IF-0001")

    ds = RfqDatasource(db_session)
    found = ds.get_by_code("IF-0001")

    assert found is not None
    assert found.id == rfq.id
    assert found.rfq_code == "IF-0001"


def test_datasource_get_by_code_returns_none_for_unknown_code(db_session):
    _create_workflow(db_session)
    ds = RfqDatasource(db_session)
    assert ds.get_by_code("IF-9999") is None


def test_datasource_get_by_code_returns_none_for_empty_string(db_session):
    """Defensive: empty string short-circuits without hitting the DB."""
    ds = RfqDatasource(db_session)
    assert ds.get_by_code("") is None


def test_datasource_get_by_code_is_exact_match_not_prefix(db_session):
    """No accidental LIKE/STARTS-WITH semantics — ``IF-001`` must not
    match ``IF-0001`` even though it's a prefix in some sense."""
    workflow = _create_workflow(db_session)
    _insert_rfq(db_session, workflow.id, rfq_code="IF-0001")
    ds = RfqDatasource(db_session)
    assert ds.get_by_code("IF-001") is None
    assert ds.get_by_code("IF-0001") is not None


# ── RfqController.get_by_code ────────────────────────────────────────────


def test_controller_get_by_code_returns_detail_when_found(db_session):
    workflow = _create_workflow(db_session)
    rfq = _insert_rfq(db_session, workflow.id, rfq_code="IF-0042")

    ctrl = RfqController(
        rfq_datasource=RfqDatasource(db_session),
        workflow_datasource=WorkflowDatasource(db_session),
        rfq_stage_datasource=RfqStageDatasource(db_session),
        session=db_session,
    )
    detail = ctrl.get_by_code("IF-0042")

    assert detail.id == rfq.id
    assert detail.rfq_code == "IF-0042"
    assert detail.name == "Test RFQ"
    assert detail.priority == "normal"


def test_controller_get_by_code_raises_not_found_for_unknown_code(db_session):
    _create_workflow(db_session)
    ctrl = RfqController(
        rfq_datasource=RfqDatasource(db_session),
        workflow_datasource=WorkflowDatasource(db_session),
        rfq_stage_datasource=RfqStageDatasource(db_session),
        session=db_session,
    )
    with pytest.raises(NotFoundError) as exc_info:
        ctrl.get_by_code("IF-9999")
    assert "IF-9999" in str(exc_info.value)


def test_controller_get_by_code_returns_same_shape_as_get_by_id(db_session):
    """Wire-shape regression: by-code and by-id MUST emit the same
    Pydantic schema (RfqDetail). Callers that switch between them
    cannot tolerate field divergence."""
    workflow = _create_workflow(db_session)
    rfq = _insert_rfq(
        db_session,
        workflow.id,
        rfq_code="IF-0100",
        priority="critical",
        status="Awarded",
    )
    ctrl = RfqController(
        rfq_datasource=RfqDatasource(db_session),
        workflow_datasource=WorkflowDatasource(db_session),
        rfq_stage_datasource=RfqStageDatasource(db_session),
        session=db_session,
    )

    by_id = ctrl.get(rfq.id).model_dump()
    by_code = ctrl.get_by_code("IF-0100").model_dump()
    assert by_id == by_code


# ── RfqStageController.list_by_code ─────────────────────────────────────


def test_stage_controller_list_by_code_returns_stages(db_session):
    workflow = _create_workflow(db_session)
    rfq = _insert_rfq(db_session, workflow.id, rfq_code="IF-0200")
    _insert_stage(db_session, rfq.id, name="Discovery", order=1, status="Done")
    _insert_stage(
        db_session, rfq.id, name="Cost estimation", order=2, status="Active",
        blocker_status="Blocked", blocker_reason_code="missing_quotes",
    )

    ctrl = RfqStageController(
        stage_datasource=RfqStageDatasource(db_session),
        rfq_datasource=RfqDatasource(db_session),
        session=db_session,
    )
    payload = ctrl.list_by_code("IF-0200")

    assert "data" in payload
    names = [s.name for s in payload["data"]]
    assert names == ["Discovery", "Cost estimation"]
    blocker = next(s for s in payload["data"] if s.name == "Cost estimation")
    assert blocker.blocker_status == "Blocked"
    assert blocker.blocker_reason_code == "missing_quotes"


def test_stage_controller_list_by_code_raises_not_found_for_unknown_code(
    db_session,
):
    ctrl = RfqStageController(
        stage_datasource=RfqStageDatasource(db_session),
        rfq_datasource=RfqDatasource(db_session),
        session=db_session,
    )
    with pytest.raises(NotFoundError):
        ctrl.list_by_code("IF-9999")


def test_stage_controller_list_by_code_returns_same_shape_as_list(db_session):
    """Same Pydantic schema as the by-id list endpoint."""
    workflow = _create_workflow(db_session)
    rfq = _insert_rfq(db_session, workflow.id, rfq_code="IF-0300")
    _insert_stage(db_session, rfq.id, name="Discovery", order=1)
    _insert_stage(db_session, rfq.id, name="Cost estimation", order=2)

    ctrl = RfqStageController(
        stage_datasource=RfqStageDatasource(db_session),
        rfq_datasource=RfqDatasource(db_session),
        session=db_session,
    )
    by_id_data = [s.model_dump() for s in ctrl.list(rfq.id)["data"]]
    by_code_data = [s.model_dump() for s in ctrl.list_by_code("IF-0300")["data"]]
    assert by_id_data == by_code_data


# ── HTTP routes ─────────────────────────────────────────────────────────


def test_route_get_by_code_returns_200_with_detail(client, db_session):
    workflow = _create_workflow(db_session)
    _insert_rfq(
        db_session,
        workflow.id,
        rfq_code="IF-0001",
        name="SEC Auxiliary Skid Bid",
        client="Saudi Electricity Company",
        priority="critical",
    )
    response = client.get("/rfq-manager/v1/rfqs/by-code/IF-0001")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rfq_code"] == "IF-0001"
    assert body["name"] == "SEC Auxiliary Skid Bid"
    assert body["client"] == "Saudi Electricity Company"
    assert body["priority"] == "critical"
    # Sanity: same key surface as the by-id route advertises.
    for required in (
        "id", "rfq_code", "name", "client", "status", "progress",
        "deadline", "priority", "owner", "workflow_id",
        "created_at", "updated_at",
    ):
        assert required in body, f"missing {required!r} in by-code response"


def test_route_get_by_code_returns_404_for_unknown_code(client, db_session):
    _create_workflow(db_session)
    response = client.get("/rfq-manager/v1/rfqs/by-code/IF-9999")
    assert response.status_code == 404, response.text
    assert "IF-9999" in response.text


def test_route_get_by_code_stages_returns_200_with_stages(client, db_session):
    workflow = _create_workflow(db_session)
    rfq = _insert_rfq(db_session, workflow.id, rfq_code="IF-0500")
    _insert_stage(db_session, rfq.id, name="Discovery", order=1, status="Done")
    _insert_stage(
        db_session, rfq.id, name="Cost estimation", order=2, status="Active",
        blocker_status="Blocked", blocker_reason_code="missing_quotes",
    )

    response = client.get("/rfq-manager/v1/rfqs/by-code/IF-0500/stages")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "data" in body
    names = [s["name"] for s in body["data"]]
    assert names == ["Discovery", "Cost estimation"]
    blocked = next(s for s in body["data"] if s["name"] == "Cost estimation")
    assert blocked["blocker_status"] == "Blocked"
    assert blocked["blocker_reason_code"] == "missing_quotes"


def test_route_get_by_code_stages_returns_404_for_unknown_code(
    client, db_session,
):
    response = client.get("/rfq-manager/v1/rfqs/by-code/IF-9999/stages")
    assert response.status_code == 404, response.text


# ── Route-ordering regression ───────────────────────────────────────────


def test_route_ordering_by_code_does_not_collide_with_uuid_route(
    client, db_session,
):
    """``/rfqs/{rfq_id}`` is registered with ``rfq_id: UUID``; if the
    by-code route weren't declared first (or weren't a sibling of
    /stats and /analytics), FastAPI would try to coerce 'by-code' into
    a UUID and return 422 before our handler runs."""
    _create_workflow(db_session)
    response = client.get("/rfq-manager/v1/rfqs/by-code/IF-NOPE")
    # 404 (handler reached, code not found) — NOT 422 (path-coercion failure).
    assert response.status_code == 404, response.text


def test_route_ordering_stats_still_works(client):
    """Sibling sanity: /stats existed before /by-code/ and must still
    resolve. Catches accidental router-include order regressions in app.py."""
    response = client.get("/rfq-manager/v1/rfqs/stats")
    assert response.status_code == 200, response.text
    body = response.json()
    for required in ("total_rfqs_12m", "open_rfqs", "critical_rfqs", "avg_cycle_days"):
        assert required in body
