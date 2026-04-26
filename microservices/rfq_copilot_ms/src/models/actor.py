"""Actor model — minimal user identity carried through every request.

Populated by utils/auth_context. The same Actor shape is consumed by
controllers and audit_log regardless of whether it came from the
DEV-only AUTH_BYPASS_* envs (Batch 3) or a verified JWT (post-IAM).
"""

from pydantic import BaseModel


class Actor(BaseModel):
    user_id: str
    display_name: str
    role: str
