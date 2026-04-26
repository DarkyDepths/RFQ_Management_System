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
