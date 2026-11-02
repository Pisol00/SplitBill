"""Body of POST /groups/{group_id}/expenses. See docs/api.md."""

import re
from dataclasses import dataclass
from decimal import Decimal

from app.core.errors import Failure, invalid_request
from app.validators.money import parse_money

MAX_DESCRIPTION_LENGTH = 255
# NUL and lone surrogates, which JSON can carry but PostgreSQL text cannot store.
UNSTORABLE_TEXT = re.compile(r"[\x00\ud800-\udfff]")


@dataclass(frozen=True)
class EqualSplit:
    members: list[str]
    type: str = "equal"


@dataclass(frozen=True)
class ExactSplit:
    shares: list[tuple[str, Decimal]]  # in the order the client listed them
    type: str = "exact"


@dataclass(frozen=True)
class ExpenseRequest:
    description: str
    paid_by: str
    amount: Decimal
    split: EqualSplit | ExactSplit


def validate_expense_request(data: object) -> ExpenseRequest | Failure:
    if not isinstance(data, dict):
        return invalid_request("body", "must be a JSON object")

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        return invalid_request("description", "is required")
    description = description.strip()
    if UNSTORABLE_TEXT.search(description):
        return invalid_request("description", "contains invalid characters")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return invalid_request(
            "description", f"must be at most {MAX_DESCRIPTION_LENGTH} characters"
        )

    paid_by = data.get("paid_by")
    if not isinstance(paid_by, str) or not paid_by:
        return invalid_request("paid_by", "must be a username")

    amount = parse_money(data.get("amount"), "amount")
    if isinstance(amount, Failure):
        return amount
    if amount <= 0:
        return invalid_request("amount", "must be greater than 0")

    split = validate_split(data.get("split"))
    if isinstance(split, Failure):
        return split

    return ExpenseRequest(
        description=description,
        paid_by=paid_by,
        amount=amount,
        split=split,
    )


def validate_split(split: object) -> EqualSplit | ExactSplit | Failure:
    if not isinstance(split, dict):
        return invalid_request("split", "must be an object")

    if split.get("type") == "equal":
        members = split.get("members")
        if not isinstance(members, list) or not members:
            return invalid_request("split.members", "must be a non-empty list")
        if not all(isinstance(member, str) and member for member in members):
            return invalid_request("split.members", "must contain usernames")
        if len(set(members)) != len(members):
            return invalid_request("split.members", "each member may appear only once")
        return EqualSplit(members=members)

    if split.get("type") == "exact":
        shares = split.get("shares")
        if not isinstance(shares, dict) or not shares:
            return invalid_request("split.shares", "must be a non-empty object")
        # JSON object keys are unique strings, and dict keeps the client's order.
        parsed: list[tuple[str, Decimal]] = []
        for member, share in shares.items():
            amount = parse_money(share, f"split.shares.{member}")
            if isinstance(amount, Failure):
                return amount
            parsed.append((member, amount))
        return ExactSplit(shares=parsed)

    return invalid_request("split.type", 'must be "equal" or "exact"')
