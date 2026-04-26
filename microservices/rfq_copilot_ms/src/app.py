"""FastAPI app factory for rfq_copilot_ms.

Batch 3 endpoints:
  GET  /health
  POST /rfq-copilot/v1/threads/open
  POST /rfq-copilot/v1/threads/new
  POST /rfq-copilot/v1/threads/{thread_id}/turn

Run with: uvicorn src.app:app --reload --port 8003
"""

import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.database import Base, engine
from src.routes.entry_routes import router as entry_router
from src.routes.health_routes import router as health_router
from src.routes.turn_routes import router as turn_router
from src.utils.errors import AppError

# Register ORM tables with Base.metadata so create_all sees them.
from src.models.db import AuditLogRow, ThreadRow, TurnRow  # noqa: F401


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="rfq_copilot_ms",
        version="0.3.0",
        description="RFQ Copilot conversation orchestration service.",
    )

    origins = [
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def bootstrap_schema():
        # DEV ONLY: schema bootstrap. Replace with Alembic migrations
        # before production. Schema changes will silently NOT apply to
        # an existing dev DB — delete the .db file to reset.
        Base.metadata.create_all(bind=engine)
        logger.warning(
            "DEV-ONLY auth_context active — single-actor mode reading AUTH_BYPASS_*. "
            "Replace src/utils/auth_context.py with IAM-backed resolver before production."
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, error: AppError):
        return JSONResponse(
            status_code=error.status_code,
            content={"error": error.__class__.__name__, "message": error.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        details = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err["loc"])
            details.append(f"{loc}: {err['msg']}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "UnprocessableEntityError",
                "message": "Validation failed: " + " | ".join(details),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "message": "Internal server error"},
        )

    # Health at root (load-balancer convention).
    app.include_router(health_router)

    # API v1 — mirrors rfq_manager_ms's /rfq-manager/v1 convention.
    v1 = APIRouter(prefix="/rfq-copilot/v1")
    v1.include_router(entry_router)
    v1.include_router(turn_router)
    app.include_router(v1)

    return app


app = create_app()
