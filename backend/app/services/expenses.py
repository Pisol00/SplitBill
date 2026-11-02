"""Expense business rules. Commits are made here, never in repositories."""

import hashlib
import json
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import repositories
from app.core.errors import Failure
from app.models import Expense, ExpenseShare, Group, User
from app.schemas import ExpenseOut, ShareOut
from app.services.splits import allocate_equal, check_exact
from app.validators.expenses import EqualSplit, ExpenseRequest

# Unique constraint on (group_id, idempotency_key); see docs/schema.md.
IDEMPOTENCY_CONSTRAINT = "uq_expenses_group_id_idempotency_key"


def create_expense(
    db: Session, group: Group, request: ExpenseRequest, idempotency_key: str
) -> tuple[ExpenseOut, bool] | Failure:
    """Record an expense. Returns the expense and whether it was newly created."""
    member_ids = repositories.get_member_ids(db, group.id)

    fingerprint = request_hash(request)
    existing = repositories.get_expense_by_idempotency_key(
        db, group.id, idempotency_key
    )
    if existing is not None:
        return replay(existing, fingerprint, member_ids)

    shares = compute_shares(request)
    if isinstance(shares, Failure):
        return shares
    involved = {request.paid_by, *(member for member, _ in shares)}
    if not involved <= member_ids.keys():
        return Failure(
            "member_not_in_group",
            "Every member of the expense must belong to the group.",
        )

    expense = Expense(
        group_id=group.id,
        paid_by_id=member_ids[request.paid_by],
        description=request.description,
        amount=request.amount,
        split_type=request.split.type,
        idempotency_key=idempotency_key,
        request_hash=fingerprint,
        shares=[
            ExpenseShare(user_id=member_ids[member], position=position, amount=amount)
            for position, (member, amount) in enumerate(shares)
        ],
    )
    db.add(expense)
    try:
        db.commit()
    except IntegrityError as error:
        # A concurrent request with the same key committed first. The constraint
        # guarantees only one row exists; return it like any other replay.
        db.rollback()
        if constraint_name(error) != IDEMPOTENCY_CONSTRAINT:
            raise
        winner = repositories.get_expense_by_idempotency_key(
            db, group.id, idempotency_key
        )
        return replay(winner, fingerprint, member_ids)
    db.refresh(expense)
    return to_expense_out(expense, member_ids), True


def list_expenses(db: Session, group: Group) -> list[ExpenseOut]:
    member_ids = repositories.get_member_ids(db, group.id)
    return [
        to_expense_out(expense, member_ids)
        for expense in repositories.list_active_expenses(db, group.id)
    ]


def delete_expense(
    db: Session, group: Group, user: User, expense_id: int
) -> Failure | None:
    """Soft-delete: keep the row, flag it, and exclude it from listings and balances."""
    # Locked until the commit, so a payment cannot be requested during the deletion.
    expense = repositories.get_active_expense(db, group.id, expense_id, lock=True)
    if expense is None:
        return Failure("expense_not_found", "Expense not found.")
    if expense.paid_by_id != user.id:
        return Failure("not_payer", "Only the payer can delete this expense.")
    if repositories.has_open_payment(db, expense.id):
        return Failure(
            "expense_has_payments",
            "This expense has payments that are waiting or confirmed.",
        )
    expense.deleted_at = func.now()
    db.commit()
    return None


def replay(
    existing: Expense, fingerprint: str, member_ids: dict[str, int]
) -> tuple[ExpenseOut, bool] | Failure:
    """The original expense for a repeated key, if the request is the same."""
    if existing.request_hash != fingerprint:
        return Failure(
            "idempotency_key_reused",
            "This Idempotency-Key was already used with a different request.",
        )
    return to_expense_out(existing, member_ids), False


def constraint_name(error: IntegrityError) -> str | None:
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def compute_shares(request: ExpenseRequest) -> list[tuple[str, Decimal]] | Failure:
    """Each member's share, in the order the request lists them."""
    if isinstance(request.split, EqualSplit):
        return allocate_equal(request.amount, request.split.members)
    shares = check_exact(request.amount, request.split.shares)
    if shares is None:
        return Failure("shares_mismatch", "The shares do not add up to the total.")
    return shares


def request_hash(request: ExpenseRequest) -> str:
    """SHA-256 of the validated request in canonical form. See docs/schema.md."""
    # Member order is significant: it decides who receives remainder satang.
    shares_in_order = (
        request.split.members
        if isinstance(request.split, EqualSplit)
        else [[member, f"{share:.2f}"] for member, share in request.split.shares]
    )
    canonical = {
        "description": request.description,
        "paid_by": request.paid_by,
        "amount": f"{request.amount:.2f}",
        "split": {"type": request.split.type, "shares": shares_in_order},
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def to_expense_out(expense: Expense, member_ids: dict[str, int]) -> ExpenseOut:
    usernames = {user_id: username for username, user_id in member_ids.items()}
    return ExpenseOut(
        id=expense.id,
        group_id=expense.group_id,
        description=expense.description,
        paid_by=usernames[expense.paid_by_id],
        amount=expense.amount,
        split_type=expense.split_type,
        shares=[
            ShareOut(member=usernames[share.user_id], amount=share.amount)
            for share in expense.shares
        ],
        created_at=expense.created_at,
    )
