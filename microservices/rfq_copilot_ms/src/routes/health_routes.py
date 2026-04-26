"""GET /health — liveness check."""

from fastapi import APIRouter


router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok", "service": "rfq_copilot_ms"}
