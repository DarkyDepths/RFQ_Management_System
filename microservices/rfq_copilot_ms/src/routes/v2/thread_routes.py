"""/v2 thread management endpoints (Batch 10).

Thin route layer over :class:`V2ThreadController`. Mirrors the /v1
``entry_routes`` shape so the future frontend cutover (PR-D, separate
batch) is small.

Endpoints:

* ``POST /v2/threads/new``       -- always creates a fresh thread
* ``POST /v2/threads/open``      -- open-or-resume the latest fresh
                                    thread for (actor, mode); creates
                                    new if stale or absent
* ``POST /v2/threads/list``      -- list threads for (actor, mode)
* ``GET  /v2/threads/{id}``      -- load a thread by id (ownership-gated)

The ``POST /v2/threads/{id}/turn`` endpoint stays in
``turn_routes.py``; this module only owns lifecycle.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app_context import get_v2_thread_controller
from src.controllers.v2_thread_controller import V2ThreadController
from src.models.actor import Actor
from src.models.v2_thread import (
    V2ListThreadsRequest,
    V2ListThreadsResponse,
    V2NewThreadRequest,
    V2NewThreadResponse,
    V2OpenThreadRequest,
    V2OpenThreadResponse,
    V2ThreadDetailResponse,
)
from src.utils.auth_context import resolve_actor


router = APIRouter(prefix="/threads", tags=["v2"])


@router.post("/new", response_model=V2NewThreadResponse)
def post_new_thread(
    body: V2NewThreadRequest,
    actor: Actor = Depends(resolve_actor),
    controller: V2ThreadController = Depends(get_v2_thread_controller),
) -> V2NewThreadResponse:
    """Always creates a new v2_threads row. Returns its id."""
    return controller.create_new(actor, body.mode)


@router.post("/open", response_model=V2OpenThreadResponse)
def post_open_thread(
    body: V2OpenThreadRequest,
    actor: Actor = Depends(resolve_actor),
    controller: V2ThreadController = Depends(get_v2_thread_controller),
) -> V2OpenThreadResponse:
    """Open-or-resume: if a fresh thread for ``(actor, mode)`` exists,
    return it with reconstructed messages. Otherwise create a new one."""
    return controller.open_or_resume(actor, body.mode)


@router.post("/list", response_model=V2ListThreadsResponse)
def post_list_threads(
    body: V2ListThreadsRequest,
    actor: Actor = Depends(resolve_actor),
    controller: V2ThreadController = Depends(get_v2_thread_controller),
) -> V2ListThreadsResponse:
    """List threads for ``(actor, mode)``, newest first. Stale threads
    included (UI may grey them) but flagged via ``is_stale``."""
    return controller.list_threads(actor, body.mode)


@router.get("/{thread_id}", response_model=V2ThreadDetailResponse)
def get_thread(
    thread_id: str,
    actor: Actor = Depends(resolve_actor),
    controller: V2ThreadController = Depends(get_v2_thread_controller),
) -> V2ThreadDetailResponse:
    """Load a thread by id with reconstructed messages. Ownership-gated:
    a thread that isn't yours OR doesn't exist returns 404
    ``ThreadNotFoundError`` (same code so an attacker can't enumerate
    other actors' thread IDs)."""
    return controller.load_thread(actor, thread_id)
