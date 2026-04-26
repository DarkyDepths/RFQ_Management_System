"""ThreadController — thread lifecycle: open-or-resume, create-new.

Batch 3: no freshness rule. /open returns the latest thread for
(actor, mode); if none exists, creates one. Freshness check lands in
Batch 4.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.datasources.audit_log_datasource import AuditLogDatasource
from src.datasources.thread_datasource import ThreadDatasource
from src.datasources.turn_datasource import TurnDatasource
from src.models.actor import Actor
from src.models.db import TurnRow
from src.models.thread import (
    GeneralMode,
    NewThreadResponse,
    OpenThreadResponse,
    RfqBoundMode,
)
from src.models.turn import MessageView


ThreadMode = GeneralMode | RfqBoundMode


class ThreadController:
    def __init__(
        self,
        thread_ds: ThreadDatasource,
        turn_ds: TurnDatasource,
        audit_ds: AuditLogDatasource,
        session: Session,
    ):
        self.thread_ds = thread_ds
        self.turn_ds = turn_ds
        self.audit_ds = audit_ds
        self.session = session

    def open_or_resume(self, actor: Actor, mode: ThreadMode) -> OpenThreadResponse:
        rfq_id, rfq_label = _unpack_mode(mode)
        thread = self.thread_ds.get_latest(actor.user_id, mode.kind, rfq_id)

        if thread is None:
            thread = self.thread_ds.create(
                actor.user_id, mode.kind, rfq_id, rfq_label,
            )
            self.audit_ds.record(
                actor.user_id,
                "thread.open_create",
                "thread",
                thread.id,
                payload={"mode_kind": mode.kind, "rfq_id": rfq_id},
            )
            messages: list[MessageView] = []
        else:
            self.audit_ds.record(
                actor.user_id,
                "thread.open_resume",
                "thread",
                thread.id,
                payload={"mode_kind": mode.kind, "rfq_id": rfq_id},
            )
            turns = self.turn_ds.list_for_thread(thread.id)
            messages = [_to_message_view(turn) for turn in turns]

        self.session.commit()
        return OpenThreadResponse(thread_id=thread.id, messages=messages)

    def create_new(self, actor: Actor, mode: ThreadMode) -> NewThreadResponse:
        rfq_id, rfq_label = _unpack_mode(mode)
        thread = self.thread_ds.create(
            actor.user_id, mode.kind, rfq_id, rfq_label,
        )
        self.audit_ds.record(
            actor.user_id,
            "thread.new",
            "thread",
            thread.id,
            payload={"mode_kind": mode.kind, "rfq_id": rfq_id},
        )
        self.session.commit()
        return NewThreadResponse(thread_id=thread.id)


def _unpack_mode(mode: ThreadMode) -> tuple[str | None, str | None]:
    if isinstance(mode, RfqBoundMode):
        return mode.rfq_id, mode.rfq_label
    return None, None


def _to_message_view(turn: TurnRow) -> MessageView:
    return MessageView(
        id=turn.id,
        role=turn.role,
        content=turn.content,
        created_at=turn.created_at,
    )
