"""DI container — datasources/controllers per-request, expensive connectors as singletons."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from src.connectors.llm_connector import LlmConnector
from src.connectors.manager_ms_connector import ManagerConnector
from src.controllers.thread_controller import ThreadController
from src.controllers.turn_controller import TurnController
from src.database import get_session
from src.datasources.audit_log_datasource import AuditLogDatasource
from src.datasources.thread_datasource import ThreadDatasource
from src.datasources.turn_datasource import TurnDatasource
from src.services.portfolio_grounded_reply import PortfolioGroundedReplyService
from src.services.rfq_grounded_reply import RfqGroundedReplyService


# ── Singletons (no per-request state, safe and cheap to share) ──────────────

_manager_connector: ManagerConnector | None = None
_llm_connector: LlmConnector | None = None
_grounded_reply_service: RfqGroundedReplyService | None = None
_portfolio_reply_service: PortfolioGroundedReplyService | None = None


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
