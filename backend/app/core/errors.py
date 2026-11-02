"""Expected failures, returned as values. core/error_handlers.py picks the status."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    code: str
    message: str


def invalid_request(field: str, problem: str) -> Failure:
    """Client input failed validation."""
    return Failure("validation_error", f"Invalid request: {field}: {problem}.")
