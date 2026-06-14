"""Custom application exceptions and FastAPI exception handlers.

All API-facing errors are translated into a consistent JSON envelope:

    {
        "error": "<ErrorType>",
        "message": "<human readable message>",
        "detail": "<optional extra context>"
    }
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class VQPError(Exception):
    """Base class for all VisualQ Pilot application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class DataLoadError(VQPError):
    """Raised when a required dataset file cannot be loaded or parsed."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ResourceNotFoundError(VQPError):
    """Raised when a requested resource (chapter, question, etc.) does not exist."""

    status_code = status.HTTP_404_NOT_FOUND


class InvalidRequestError(VQPError):
    """Raised when request parameters are semantically invalid."""

    status_code = status.HTTP_400_BAD_REQUEST


class GeminiServiceError(VQPError):
    """Raised when the Gemini API fails after all retries."""

    status_code = status.HTTP_502_BAD_GATEWAY


class PaperGenerationError(VQPError):
    """Raised when the orchestrator cannot assemble a valid paper."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


def _error_response(status_code: int, error: str, message: str, detail: str | None = None) -> JSONResponse:
    body: dict[str, str] = {"error": error, "message": message}
    if detail:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(VQPError)
    async def handle_vqp_error(request: Request, exc: VQPError) -> JSONResponse:
        logger.error("%s on %s %s: %s", type(exc).__name__, request.method, request.url.path, exc.message)
        return _error_response(exc.status_code, type(exc).__name__, exc.message, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "ValidationError",
            "Request validation failed.",
            detail=str(exc.errors()),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "InternalServerError",
            "An unexpected error occurred. Please try again later.",
        )
