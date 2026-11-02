"""Database queries. No business decisions and no commits."""

from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import Select, func, select, union_all
from sqlalchemy.orm import Session, selectinload

from app.models import Expense, ExpenseShare, Group, GroupMember, Payment, User

# The range of the INTEGER id columns. PostgreSQL raises an error when compared with a
# value outside it, and no row can have such an id.
MIN_ID = -(2**31)
MAX_ID = 2**31 - 1


class PaymentRow(NamedTuple):
    payment: Payment
    to_user_id: int
    amount: Decimal


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


def get_active_expense(
    db: Session, group_id: int, expense_id: int, lock: bool = False
) -> Expense | None:
    """The expense, or None if it is missing, in another group or soft-deleted.

    With lock, the row stays locked until the transaction ends.
    """
    if not MIN_ID <= expense_id <= MAX_ID:
        return None
    statement = select(Expense).where(
        Expense.id == expense_id,
        Expense.group_id == group_id,
        Expense.deleted_at.is_(None),
    )
    if lock:
        statement = statement.with_for_update()
    return db.scalar(statement)


def get_share(db: Session, expense_id: int, user_id: int) -> ExpenseShare | None:
    return db.get(ExpenseShare, (expense_id, user_id))


def has_open_payment(db: Session, expense_id: int, user_id: int | None = None) -> bool:
    """Whether a waiting or confirmed payment exists, for one user's share or any."""
    statement = select(Payment.id).where(
        Payment.expense_id == expense_id, Payment.status != "rejected"
    )
    if user_id is not None:
        statement = statement.where(Payment.user_id == user_id)
    return db.scalar(statement.limit(1)) is not None


def _payment_rows() -> Select:
    """Each payment with its receiver and amount, from its active expense and share."""
    return (
        select(Payment, Expense.paid_by_id, ExpenseShare.amount)
        .join(
            ExpenseShare,
            (ExpenseShare.expense_id == Payment.expense_id)
            & (ExpenseShare.user_id == Payment.user_id),
        )
        .join(Expense, Expense.id == Payment.expense_id)
        .where(Expense.deleted_at.is_(None))
    )


def list_payments(db: Session, group_id: int) -> list[PaymentRow]:
    """Payments of active expenses, newest first."""
    rows = db.execute(
        _payment_rows()
        .where(Expense.group_id == group_id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
    )
    return [PaymentRow(*row) for row in rows]


def get_payment(
    db: Session, group_id: int, payment_id: int, lock: bool = False
) -> PaymentRow | None:
    """The payment, or None if it is missing, in another group or on a deleted expense.

    With lock, the payment row stays locked until the transaction ends.
    """
    if not MIN_ID <= payment_id <= MAX_ID:
        return None
    statement = _payment_rows().where(
        Payment.id == payment_id, Expense.group_id == group_id
    )
    if lock:
        statement = statement.with_for_update(of=Payment)
    row = db.execute(statement).one_or_none()
    return None if row is None else PaymentRow(*row)


def balance_by_user(db: Session, group_id: int) -> dict[int, Decimal]:
    """Paid minus owed per user, from active expenses and confirmed payments.

    One statement, so it reads one snapshot. With separate queries for paid and owed,
    an expense committed between them would count on only one side. A confirmed payment
    moves the share's amount from the receiver to the sender, so it keeps the sum at
    zero.
    """
    paid = select(
        Expense.paid_by_id.label("user_id"), Expense.amount.label("amount")
    ).where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
    owed = (
        select(ExpenseShare.user_id, (-ExpenseShare.amount).label("amount"))
        .join(Expense, Expense.id == ExpenseShare.expense_id)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
    )
    confirmed = (
        _payment_rows()
        .where(Expense.group_id == group_id, Payment.status == "confirmed")
        .subquery()
    )
    sent = select(confirmed.c.user_id, confirmed.c.amount)
    received = select(
        confirmed.c.paid_by_id.label("user_id"), (-confirmed.c.amount).label("amount")
    )
    entries = union_all(paid, owed, sent, received).subquery()
    rows = db.execute(
        select(entries.c.user_id, func.sum(entries.c.amount)).group_by(
            entries.c.user_id
        )
    )
    return {user_id: amount for user_id, amount in rows}
