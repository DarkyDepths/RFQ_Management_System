"""TurnController — persists one turn and emits the assistant reply.

Batch 3 flow: persist user turn -> generate canned reply -> persist
assistant turn -> touch thread activity -> audit-log -> return.

Batch 5 will replace the canned-reply import with the LLM-backed
pipeline. The controller's shape does not change.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.datasources.audit_log_datasource import AuditLogDatasource
from src.datasources.thread_datasource import ThreadDatasource
from src.datasources.turn_datasource import TurnDatasource
from src.models.actor import Actor
from src.models.thread import GeneralMode, RfqBoundMode
from src.models.turn import MessageView, TurnResponse
from src.utils.canned_reply import generate_canned_reply
from src.utils.errors import NotFoundError


class TurnController:
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

    def process_turn(
        self,
        actor: Actor,
        thread_id: str,
        user_message: str,
    ) -> TurnResponse:
        thread = self.thread_ds.get_by_id(thread_id)
        if thread is None:
            raise NotFoundError(f"Thread '{thread_id}' not found")

        user_row = self.turn_ds.append(thread.id, "user", user_message)
        self.audit_ds.record(
            actor.user_id,
            "turn.user",
            "turn",
            user_row.id,
            payload={"thread_id": thread.id},
        )

        if thread.mode_kind == "general":
            mode = GeneralMode(kind="general")
        else:
            mode = RfqBoundMode(
                kind="rfq_bound",
                rfq_id=thread.rfq_id,
                rfq_label=thread.rfq_label,
            )

        reply_text = generate_canned_reply(mode)

        assistant_row = self.turn_ds.append(thread.id, "assistant", reply_text)
        self.audit_ds.record(
            actor.user_id,
            "turn.assistant",
            "turn",
            assistant_row.id,
            payload={"thread_id": thread.id},
        )

        self.thread_ds.touch_activity(thread)
        self.session.commit()

        return TurnResponse(
            message_id=user_row.id,
            assistant_message=MessageView(
                id=assistant_row.id,
                role="assistant",
                content=assistant_row.content,
                created_at=assistant_row.created_at,
            ),
        )
