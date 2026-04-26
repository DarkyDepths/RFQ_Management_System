"""Thread entry routes — POST /threads/open, POST /threads/new.

Thin route layer; lifecycle decisions live in ThreadController.
"""

from fastapi import APIRouter, Depends

from src.app_context import get_thread_controller
from src.controllers.thread_controller import ThreadController
from src.models.actor import Actor
from src.models.thread import (
    NewThreadRequest,
    NewThreadResponse,
    OpenThreadRequest,
    OpenThreadResponse,
)
from src.utils.auth_context import resolve_actor


router = APIRouter(prefix="/threads", tags=["Threads"])


@router.post("/open", response_model=OpenThreadResponse)
def open_thread(
    body: OpenThreadRequest,
    actor: Actor = Depends(resolve_actor),
    ctrl: ThreadController = Depends(get_thread_controller),
):
    return ctrl.open_or_resume(actor, body.mode)


@router.post("/new", response_model=NewThreadResponse)
def new_thread(
    body: NewThreadRequest,
    actor: Actor = Depends(resolve_actor),
    ctrl: ThreadController = Depends(get_thread_controller),
):
    return ctrl.create_new(actor, body.mode)
