import re
from decimal import Decimal

from app.core.errors import Failure, invalid_request

# Up to 10 integer digits and 2 decimal places: the range of NUMERIC(12,2).
# [0-9], because \d also matches digits of other scripts, such as Thai.
MONEY_PATTERN = re.compile(r"[0-9]{1,10}(\.[0-9]{1,2})?")


def parse_money(value: object, field: str) -> Decimal | Failure:
    """Accept only strings such as "1000.00".

    JSON numbers are rejected because a client may already have lost precision, and
    extra decimal places are rejected because PostgreSQL would round them silently.
    """
    if not isinstance(value, str) or not MONEY_PATTERN.fullmatch(value):
        return invalid_request(
            field, 'must be a string with at most 2 decimal places, such as "1000.00"'
        )
    return Decimal(value)
