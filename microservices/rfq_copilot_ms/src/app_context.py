"""DI container — provides per-request datasources and controllers via FastAPI Depends."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.controllers.thread_controller import ThreadController
from src.controllers.turn_controller import TurnController
from src.database import get_session
from src.datasources.audit_log_datasource import AuditLogDatasource
from src.datasources.thread_datasource import ThreadDatasource
from src.datasources.turn_datasource import TurnDatasource


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
) -> TurnController:
    return TurnController(thread_ds, turn_ds, audit_ds, db)
