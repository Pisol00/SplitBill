"""Body of POST /groups/{group_id}/payments. See docs/api.md."""

from app.core.errors import Failure, invalid_request


def validate_payment_request(data: object) -> int | Failure:
    """The ID of the expense being paid."""
    if not isinstance(data, dict):
        return invalid_request("body", "must be a JSON object")

    expense_id = data.get("expense_id")
    # bool is a subclass of int in Python, but true is not an ID.
    if not isinstance(expense_id, int) or isinstance(expense_id, bool):
        return invalid_request("expense_id", "must be an integer")
    return expense_id
