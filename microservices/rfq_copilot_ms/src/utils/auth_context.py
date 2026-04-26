"""Auth context — resolves the request Actor for each turn.

================================================================
DEV ONLY — IAM swap point.
================================================================

Batch 3 implementation: returns a deterministic Actor constructed from
the AUTH_BYPASS_* env vars on every request. The frontend sends no
auth header at this stage.

Production swap (when IAM lands): replace the body of resolve_actor()
to validate the Authorization: Bearer JWT against IAM and fetch the
Actor from the IAM connector. Routes, controllers, and datasources
are not affected — they already receive Actor via Depends(resolve_actor).
"""

from src.config.settings import settings
from src.models.actor import Actor


def resolve_actor() -> Actor:
    return Actor(
        user_id=settings.AUTH_BYPASS_USER_ID,
        display_name=settings.AUTH_BYPASS_USER_NAME,
        role=settings.AUTH_BYPASS_ROLE,
    )
