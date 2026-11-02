"""Database queries. No business decisions and no commits."""

from decimal import Decimal

from sqlalchemy import func, select, union_all
from sqlalchemy.orm import Session, selectinload

from app.models import Expense, ExpenseShare, Group, GroupMember, User

# The range of the INTEGER id columns. PostgreSQL raises an error when compared with a
# value outside it, and no row can have such an id.
MIN_ID = -(2**31)
MAX_ID = 2**31 - 1


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def list_groups_for_user(db: Session, user_id: int) -> list[Group]:
    return list(
        db.scalars(
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .where(GroupMember.user_id == user_id)
            .order_by(Group.id)
        )
    )


def get_group_for_member(db: Session, group_id: int, user_id: int) -> Group | None:
    """The group, or None if it does not exist or the user is not a member."""
    if not MIN_ID <= group_id <= MAX_ID:
        return None
    return db.scalar(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(Group.id == group_id, GroupMember.user_id == user_id)
    )


def list_member_usernames(db: Session, group_id: int) -> list[str]:
    return list(
        db.scalars(
            select(User.username)
            .join(GroupMember, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id)
            .order_by(User.username)
        )
    )


def get_member_ids(db: Session, group_id: int) -> dict[str, int]:
    """Username to user ID for every member of the group."""
    rows = db.execute(
        select(User.username, User.id)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
    )
    return {username: user_id for username, user_id in rows}


def get_expense_by_idempotency_key(
    db: Session, group_id: int, idempotency_key: str
) -> Expense | None:
    return db.scalar(
        select(Expense).where(
            Expense.group_id == group_id, Expense.idempotency_key == idempotency_key
        )
    )


def list_active_expenses(db: Session, group_id: int) -> list[Expense]:
    """Expenses that are not soft-deleted, newest first, with their shares loaded."""
    return list(
        db.scalars(
            select(Expense)
            .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
            .order_by(Expense.created_at.desc(), Expense.id.desc())
            .options(selectinload(Expense.shares))
        )
    )


def get_active_expense(db: Session, group_id: int, expense_id: int) -> Expense | None:
    """The expense, or None if it is missing, in another group or soft-deleted."""
    if not MIN_ID <= expense_id <= MAX_ID:
        return None
    return db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.group_id == group_id,
            Expense.deleted_at.is_(None),
        )
    )


def balance_by_user(db: Session, group_id: int) -> dict[int, Decimal]:
    """Paid minus owed per user, from active expenses.

    One statement, so it reads one snapshot. With separate queries for paid and owed,
    an expense committed between them would count on only one side.
    """
    paid = select(
        Expense.paid_by_id.label("user_id"), Expense.amount.label("amount")
    ).where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
    owed = (
        select(ExpenseShare.user_id, (-ExpenseShare.amount).label("amount"))
        .join(Expense, Expense.id == ExpenseShare.expense_id)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
    )
    entries = union_all(paid, owed).subquery()
    rows = db.execute(
        select(entries.c.user_id, func.sum(entries.c.amount)).group_by(
            entries.c.user_id
        )
    )
    return {user_id: amount for user_id, amount in rows}
