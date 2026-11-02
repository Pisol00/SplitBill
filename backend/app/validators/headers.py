from app.core.errors import Failure, invalid_request

MAX_IDEMPOTENCY_KEY_LENGTH = 255  # expenses.idempotency_key is VARCHAR(255)


def validate_idempotency_key(value: str | None) -> str | Failure:
    if value is None or value == "":
        return invalid_request("Idempotency-Key", "header is required")
    if len(value) > MAX_IDEMPOTENCY_KEY_LENGTH:
        return invalid_request(
            "Idempotency-Key",
            f"must be at most {MAX_IDEMPOTENCY_KEY_LENGTH} characters",
        )
    return value
