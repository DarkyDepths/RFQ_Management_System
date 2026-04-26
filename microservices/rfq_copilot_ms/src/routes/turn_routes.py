"""POST /threads/{thread_id}/turn — single endpoint that drives one turn through the pipeline.

Batch 3 'pipeline' is just persist user -> canned reply -> persist assistant.
"""

from fastapi import APIRouter, Depends

from src.app_context import get_turn_controller
from src.controllers.turn_controller import TurnController
from src.models.actor import Actor
from src.models.turn import TurnRequest, TurnResponse
from src.utils.auth_context import resolve_actor


router = APIRouter(prefix="/threads", tags=["Turns"])


@router.post("/{thread_id}/turn", response_model=TurnResponse)
def post_turn(
    thread_id: str,
    body: TurnRequest,
    actor: Actor = Depends(resolve_actor),
    ctrl: TurnController = Depends(get_turn_controller),
):
    return ctrl.process_turn(actor, thread_id, body.user_message)
