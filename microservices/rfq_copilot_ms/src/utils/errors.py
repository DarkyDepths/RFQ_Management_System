"""Application error classes mapped to HTTP responses by the global exception handler in app.py."""


class AppError(Exception):
    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class BadRequestError(AppError):
    status_code = 400
    message = "Bad request"


class ServiceUnavailableError(AppError):
    status_code = 503
    message = "Service unavailable"


class RfqNotFound(NotFoundError):
    """Manager returned 404 for the requested RFQ id."""

    message = "RFQ not found in the platform"


class RfqAccessDenied(AppError):
    """Manager returned 403 — the actor authenticated but is not
    permitted to read this RFQ.

    Distinct from ``RfqNotFound`` (404 — does not exist) and from
    ``ManagerUnreachable`` (5xx / network — source is down). The
    Path 4 access stage routes this to Path 8.4
    ``access_denied_explicit`` so the user gets "you can't see that
    RFQ" rather than "the data source is down" (Batch 9.1).
    """

    status_code = 403
    message = "Access denied to that RFQ"


class ManagerAuthFailed(ServiceUnavailableError):
    """Manager returned 401 — the copilot's credentials/headers were
    rejected.

    Distinct from ``ManagerUnreachable`` (network/5xx) and from
    ``RfqAccessDenied`` (403, actor authed but lacks permission).
    A 401 is a deployment-config bug (e.g. manager has
    AUTH_BYPASS_ENABLED=false but copilot didn't send a bearer
    token); operators need to see a different reason_code than
    "source down" so the misconfig is visible (Batch 9.1).
    """

    message = "RFQ data service rejected the copilot's credentials"


class ManagerUnreachable(ServiceUnavailableError):
    """rfq_manager_ms is unreachable, timed out, or returned an unexpected status."""

    message = "Could not reach the RFQ data service"


class LlmUnreachable(ServiceUnavailableError):
    """Azure OpenAI is unreachable, returned an auth error, or timed out."""

    message = "Language model is unavailable"
