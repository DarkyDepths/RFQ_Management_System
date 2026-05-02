"""GET /health — liveness check.

GET /health/readiness — passive configuration readiness (Batch 9).
Returns whether the service has the env wiring to *attempt* its
operational paths. Intentionally passive — no live network calls,
no DB write, no Azure call. Booting and answering this endpoint
must NEVER fail because of an upstream being down. See
``docs/SLICE_1_APP_TESTING.md``.
"""

from fastapi import APIRouter

from src.config.settings import settings


router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok", "service": "rfq_copilot_ms"}


@router.get("/health/readiness", include_in_schema=False)
def readiness_check():
    """Passive readiness probe.

    Reports whether configuration is *present* — not whether the
    upstream is *reachable*. A 200 here does NOT mean Azure or
    manager_ms will respond; it only means the env wiring is in place.

    No secrets returned. ``manager_base_url`` is the configured
    base URL string (safe — no API key embedded), nothing else from
    the Azure / IAM / DB credentials surface.
    """
    return {
        "service": "rfq_copilot_ms",
        "azure_planner_configured": bool(
            settings.AZURE_OPENAI_API_KEY
            and settings.AZURE_OPENAI_ENDPOINT
            and settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        ),
        "manager_base_url_configured": bool(settings.MANAGER_BASE_URL),
        "manager_base_url": settings.MANAGER_BASE_URL,
        "persistence_configured": bool(settings.DATABASE_URL),
    }
