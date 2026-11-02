"""Net balance of each group member."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app import repositories
from app.models import Group
from app.schemas import BalanceOut

ZERO = Decimal("0.00")


def group_balances(db: Session, group: Group) -> list[BalanceOut]:
    """Paid minus owed per member, ordered by username; positive means owed money.

    Each expense's shares sum to its amount, so the balances sum to exactly zero.
    """
    member_ids = repositories.get_member_ids(db, group.id)
    balances = repositories.balance_by_user(db, group.id)
    return [
        BalanceOut(member=username, balance=balances.get(user_id, ZERO))
        for username, user_id in sorted(member_ids.items())
    ]
