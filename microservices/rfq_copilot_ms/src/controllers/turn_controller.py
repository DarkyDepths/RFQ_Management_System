"""TurnController — persists one turn and emits the assistant reply.

Batch 4.2 flow:
- general mode    -> PortfolioGroundedReplyService (manager stats + list + LLM)
- rfq_bound mode  -> RfqGroundedReplyService (manager detail + stages + LLM)
- defensive fallback (rfq_bound w/ missing rfq_id) -> canned_reply

Persistence + audit + activity-touch are mode-agnostic. The controller
stays thin: prompt construction, RFQ fetching, and LLM calls all live
in the service / connector layers.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.datasources.audit_log_datasource import AuditLogDatasource
from src.datasources.thread_datasource import ThreadDatasource
from src.datasources.turn_datasource import TurnDatasource
from src.models.actor import Actor
from src.models.thread import RfqBoundMode
from src.models.turn import MessageView, TurnResponse
from src.services.portfolio_grounded_reply import PortfolioGroundedReplyService
from src.services.rfq_grounded_reply import RfqGroundedReplyService
from src.utils.canned_reply import generate_canned_reply
from src.utils.errors import NotFoundError


class TurnController:
    def __init__(
        self,
        thread_ds: ThreadDatasource,
        turn_ds: TurnDatasource,
        audit_ds: AuditLogDatasource,
        session: Session,
        grounded_reply_service: RfqGroundedReplyService,
        portfolio_reply_service: PortfolioGroundedReplyService,
    ):
        self.thread_ds = thread_ds
        self.turn_ds = turn_ds
        self.audit_ds = audit_ds
        self.session = session
        self.grounded_reply_service = grounded_reply_service
        self.portfolio_reply_service = portfolio_reply_service

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

        # Real prior history (excluding the user_row we just appended).
        # The service will window this to the last N pairs.
        all_turns = self.turn_ds.list_for_thread(thread.id)
        history = all_turns[:-1]

        if thread.mode_kind == "rfq_bound" and thread.rfq_id:
            reply_text = self.grounded_reply_service.generate(
                actor=actor,
                rfq_id=thread.rfq_id,
                user_message=user_message,
                history=history,
            )
        elif thread.mode_kind == "general":
            reply_text = self.portfolio_reply_service.generate(
                actor=actor,
                user_message=user_message,
                history=history,
            )
        else:
            # Defensive fallback for rfq_bound thread missing rfq_id.
            mode = RfqBoundMode(
                kind="rfq_bound",
                rfq_id=thread.rfq_id or "",
                rfq_label=thread.rfq_label or "",
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
