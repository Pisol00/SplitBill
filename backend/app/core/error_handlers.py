"""Turn failures and errors into the standard JSON error response.

Routes pass the Failure values they receive to failure_response. The handlers cover what
is still raised: the framework's own errors (unknown URL, wrong method, malformed
request) and unexpected crashes. Everything ends up in the same
{"error": {"code", "message"}} shape, built by app/utils/responses.py.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import Failure
from app.utils.responses import (
    error,
    forbidden,
    internal_error,
    method_not_allowed,
    not_found,
    unauthorized,
    unprocessable,
)

logger = logging.getLogger(__name__)

# Response for each expected failure.
FAILURE_RESPONSES = {
    "missing_user": unauthorized,
    "unknown_user": unauthorized,
    "not_payer": forbidden,
    "group_not_found": not_found,
    "expense_not_found": not_found,
    "validation_error": unprocessable,
    "idempotency_key_reused": unprocessable,
    "member_not_in_group": unprocessable,
    "shares_mismatch": unprocessable,
}


def failure_response(failure: Failure) -> JSONResponse:
    return FAILURE_RESPONSES[failure.code](failure.code, failure.message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return unprocessable("validation_error", _describe(exc))

    @app.exception_handler(StarletteHTTPException)
    def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # Raised by the framework itself, before any of our code runs.
        if exc.status_code == 404:
            return not_found()
        if exc.status_code == 405:
            return method_not_allowed(exc.headers)
        return error(exc.status_code, "http_error", str(exc.detail), exc.headers)

    @app.exception_handler(Exception)
    def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # A bug. Log everything for us; tell the client nothing about it. Pass the
        # exception explicitly: the handler runs after the except block has ended.
        logger.error(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return internal_error()


def _describe(exc: RequestValidationError) -> str:
    """One readable sentence for the first validation problem."""
    first = exc.errors()[0]
    # The location starts with "path", "query", "header" or "body"; drop it.
    field = ".".join(str(part) for part in first["loc"][1:])
    return f"Invalid request: {field}: {first['msg']}." if field else first["msg"]
