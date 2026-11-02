"""Repayment business rules. Commits are made here, never in repositories."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import repositories
from app.core.errors import Failure
from app.models import Group, Payment, User
from app.repositories import PaymentRow
from app.schemas import PaymentOut


def request_payment(
    db: Session, group: Group, user: User, expense_id: int
) -> PaymentOut | Failure:
    """Report that the user transferred their share; the expense's payer decides."""
    # Locked until the commit, so a concurrent request for the same share, or a
    # concurrent deletion of the expense, waits and then sees this payment.
    expense = repositories.get_active_expense(db, group.id, expense_id, lock=True)
    if expense is None:
        return Failure("expense_not_found", "Expense not found.")
    if expense.paid_by_id == user.id:
        return Failure("own_share", "The payer of an expense has nothing to repay.")
    share = repositories.get_share(db, expense.id, user.id)
    if share is None or share.amount == 0:
        return Failure("no_share", "You have no share to pay in this expense.")
    if repositories.has_open_payment(db, expense.id, user.id):
        return Failure(
            "payment_already_requested",
            "A payment for this share is already waiting or confirmed.",
        )

    payment = Payment(expense_id=expense.id, user_id=user.id, status="pending")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return to_payment_out(
        PaymentRow(payment, expense.paid_by_id, share.amount),
        repositories.get_member_ids(db, group.id),
    )


def list_payments(db: Session, group: Group) -> list[PaymentOut]:
    member_ids = repositories.get_member_ids(db, group.id)
    return [
        to_payment_out(row, member_ids)
        for row in repositories.list_payments(db, group.id)
    ]


def decide_payment(
    db: Session, group: Group, user: User, payment_id: int, status: str
) -> PaymentOut | Failure:
    """Confirm or reject a waiting payment. Only the expense's payer may decide."""
    # Locked until the commit, so concurrent decisions apply one at a time.
    row = repositories.get_payment(db, group.id, payment_id, lock=True)
    if row is None:
        return Failure("payment_not_found", "Payment not found.")
    if row.to_user_id != user.id:
        return Failure(
            "not_payment_receiver",
            "Only the member who paid the expense can decide this payment.",
        )
    if row.payment.status != "pending":
        return Failure("payment_not_pending", "This payment was already decided.")

    row.payment.status = status
    row.payment.decided_at = func.now()
    db.commit()
    db.refresh(row.payment)
    return to_payment_out(row, repositories.get_member_ids(db, group.id))


def to_payment_out(row: PaymentRow, member_ids: dict[str, int]) -> PaymentOut:
    usernames = {user_id: username for username, user_id in member_ids.items()}
    return PaymentOut(
        id=row.payment.id,
        expense_id=row.payment.expense_id,
        from_member=usernames[row.payment.user_id],
        to_member=usernames[row.to_user_id],
        amount=row.amount,
        status=row.payment.status,
        created_at=row.payment.created_at,
        decided_at=row.payment.decided_at,
    )
