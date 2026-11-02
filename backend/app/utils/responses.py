"""Build HTTP responses in one place, so every route and error looks the same.

Routes that return these must declare response_model on the decorator: FastAPI
cannot see the shape inside a JSONResponse, and Swagger UI would show no schema.
failure_response and the handlers in app/core/error_handlers.py call the error helpers
below.
"""

from typing import Any

from fastapi import Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

# Success


def ok(data: Any) -> JSONResponse:
    """200 OK with a JSON body."""
    return _json(status.HTTP_200_OK, data)


def created(data: Any) -> JSONResponse:
    """201 Created with a JSON body."""
    return _json(status.HTTP_201_CREATED, data)


def no_content() -> Response:
    """204 No Content: no body and no Content-Type."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Errors: {"error": {"code": ..., "message": ...}}


def unauthorized(code: str, message: str) -> JSONResponse:
    """401. HTTP requires a 401 to say how to authenticate: the X-User header."""
    return error(
        status.HTTP_401_UNAUTHORIZED, code, message, {"WWW-Authenticate": "X-User"}
    )


def forbidden(code: str, message: str) -> JSONResponse:
    """403: the user is known but not allowed to do this."""
    return error(status.HTTP_403_FORBIDDEN, code, message)


def not_found(
    code: str = "not_found", message: str = "The requested URL was not found."
) -> JSONResponse:
    """404. The defaults are for a URL that matches no route."""
    return error(status.HTTP_404_NOT_FOUND, code, message)


def method_not_allowed(headers: dict[str, str] | None = None) -> JSONResponse:
    """405: the URL exists but not for this method. headers carries Allow."""
    return error(
        status.HTTP_405_METHOD_NOT_ALLOWED,
        "method_not_allowed",
        "This method is not allowed for this URL.",
        headers,
    )


def unprocessable(code: str, message: str) -> JSONResponse:
    """422: the request is readable but breaks a rule."""
    return error(status.HTTP_422_UNPROCESSABLE_CONTENT, code, message)


def internal_error() -> JSONResponse:
    """500. Never includes details of the failure; those go to the server log."""
    return error(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Something went wrong on the server.",
    )


def error(
    status_code: int, code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    """Any error status, in the standard error body."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


def _json(status_code: int, data: Any) -> JSONResponse:
    # jsonable_encoder applies the response models' serializers, for example
    # money as "33.34" (see MoneyOut in app/schemas.py).
    return JSONResponse(status_code=status_code, content=jsonable_encoder(data))
