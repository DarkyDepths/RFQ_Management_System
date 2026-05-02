"""DI container — datasources/controllers per-request, expensive connectors as singletons.

/v2 wiring (Batch 5+) lives below the /v1 wiring; tests use FastAPI
``dependency_overrides`` to inject ``FakeLlmConnector`` /
``FakeManagerConnector`` so no real Azure/Manager calls happen in
unit tests.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from src.connectors.llm_connector import LlmConnector
from src.connectors.manager_ms_connector import ManagerConnector
from src.controllers.thread_controller import ThreadController
from src.controllers.turn_controller import TurnController
from src.controllers.v2_turn_controller import V2TurnController
from src.database import get_session
from src.datasources.audit_log_datasource import AuditLogDatasource
from src.datasources.thread_datasource import ThreadDatasource
from src.datasources.turn_datasource import TurnDatasource
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner import Planner
from src.pipeline.planner_validator import PlannerValidator
from src.services.portfolio_grounded_reply import PortfolioGroundedReplyService
from src.services.rfq_grounded_reply import RfqGroundedReplyService
from src.utils.errors import LlmUnreachable


# ── Singletons (no per-request state, safe and cheap to share) ──────────────

_manager_connector: ManagerConnector | None = None
_llm_connector: LlmConnector | None = None
_grounded_reply_service: RfqGroundedReplyService | None = None
_portfolio_reply_service: PortfolioGroundedReplyService | None = None

# /v2 singletons
_factory: ExecutionPlanFactory | None = None
_validator: PlannerValidator | None = None
_gate: EscalationGate | None = None
_planner: Planner | None = None
_planner_init_attempted: bool = False
_v2_controller: V2TurnController | None = None


def get_manager_connector() -> ManagerConnector:
    global _manager_connector
    if _manager_connector is None:
        _manager_connector = ManagerConnector()
    return _manager_connector


def get_llm_connector() -> LlmConnector:
    global _llm_connector
    if _llm_connector is None:
        _llm_connector = LlmConnector()
    return _llm_connector


def get_grounded_reply_service() -> RfqGroundedReplyService:
    global _grounded_reply_service
    if _grounded_reply_service is None:
        _grounded_reply_service = RfqGroundedReplyService(
            manager_connector=get_manager_connector(),
            llm_connector=get_llm_connector(),
        )
    return _grounded_reply_service


def get_portfolio_reply_service() -> PortfolioGroundedReplyService:
    global _portfolio_reply_service
    if _portfolio_reply_service is None:
        _portfolio_reply_service = PortfolioGroundedReplyService(
            manager_connector=get_manager_connector(),
            llm_connector=get_llm_connector(),
        )
    return _portfolio_reply_service


# ── Per-request providers ────────────────────────────────────────────────────

def get_thread_datasource(db: Session = Depends(get_session)) -> ThreadDatasource:
    return ThreadDatasource(db)


def get_turn_datasource(db: Session = Depends(get_session)) -> TurnDatasource:
    return TurnDatasource(db)


def get_audit_log_datasource(db: Session = Depends(get_session)) -> AuditLogDatasource:
    return AuditLogDatasource(db)


def get_thread_controller(
    thread_ds: ThreadDatasource = Depends(get_thread_datasource),
    turn_ds: TurnDatasource = Depends(get_turn_datasource),
    audit_ds: AuditLogDatasource = Depends(get_audit_log_datasource),
    db: Session = Depends(get_session),
) -> ThreadController:
    return ThreadController(thread_ds, turn_ds, audit_ds, db)


def get_turn_controller(
    thread_ds: ThreadDatasource = Depends(get_thread_datasource),
    turn_ds: TurnDatasource = Depends(get_turn_datasource),
    audit_ds: AuditLogDatasource = Depends(get_audit_log_datasource),
    db: Session = Depends(get_session),
    grounded_service: RfqGroundedReplyService = Depends(get_grounded_reply_service),
    portfolio_service: PortfolioGroundedReplyService = Depends(get_portfolio_reply_service),
) -> TurnController:
    return TurnController(
        thread_ds,
        turn_ds,
        audit_ds,
        db,
        grounded_service,
        portfolio_service,
    )


# ── /v2 wiring (Batch 5) ────────────────────────────────────────────────────


def get_factory() -> ExecutionPlanFactory:
    global _factory
    if _factory is None:
        _factory = ExecutionPlanFactory()
    return _factory


def get_validator() -> PlannerValidator:
    global _validator
    if _validator is None:
        _validator = PlannerValidator()
    return _validator


def get_gate() -> EscalationGate:
    global _gate
    if _gate is None:
        _gate = EscalationGate(factory=get_factory())
    return _gate


def get_planner() -> Planner | None:
    """Returns a Planner if Azure OpenAI is configured, else None.

    Slice 1 production deployments may run without LLM credentials —
    in that case the V2TurnController routes any non-FastIntake message
    to Path 8.5 ``llm_unavailable`` automatically. Tests inject a fake
    Planner via dependency_overrides.
    """
    global _planner, _planner_init_attempted
    if _planner is not None:
        return _planner
    if _planner_init_attempted:
        return None
    _planner_init_attempted = True
    try:
        _planner = Planner(llm_connector=get_llm_connector())
        return _planner
    except LlmUnreachable:
        # Azure OpenAI not configured. The V2 controller handles None
        # by routing to Path 8.5.
        return None


def get_v2_turn_controller(
    factory: ExecutionPlanFactory = Depends(get_factory),
    validator: PlannerValidator = Depends(get_validator),
    gate: EscalationGate = Depends(get_gate),
    planner: Planner | None = Depends(get_planner),
    manager: ManagerConnector = Depends(get_manager_connector),
    db: Session = Depends(get_session),
) -> V2TurnController:
    """Per-request /v2 controller. ``db`` is per-request so each turn
    gets its own SQLAlchemy session for the Persist write."""
    from src.config.path_registry import REGISTRY_VERSION
    return V2TurnController(
        factory=factory,
        validator=validator,
        gate=gate,
        planner=planner,
        manager=manager,
        session=db,
        registry_version=REGISTRY_VERSION,
    )
