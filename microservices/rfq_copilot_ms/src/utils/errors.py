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


class ThreadNotFoundError(NotFoundError):
    """The requested /v2 thread doesn't exist OR doesn't belong to
    the requesting actor (Batch 10).

    Same error class for both cases by design — a 403 on
    "not your thread" would let an attacker enumerate other actors'
    thread IDs by looking for which IDs return 403 vs 404. Returning
    404 in both cases collapses the signal.

    Raised by ``V2ThreadController`` and ``V2TurnController`` when
    ``V2ThreadDatasource.get_by_id(thread_id, actor_id)`` returns
    None (row missing OR owner mismatch). Mapped to HTTP 404 by the
    global ``AppError`` handler in ``src/app.py``.
    """

    message = "Thread not found or not accessible"


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
