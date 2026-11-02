from typing import Annotated, Any

from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse

from app.core.error_handlers import failure_response
from app.core.errors import Failure
from app.dependencies import (
    SessionDep,
    UserHeader,
    get_current_user,
    get_member_group,
)
from app.schemas import PaymentOut
from app.services import payments as payment_service
from app.utils.responses import created, ok
from app.validators.payments import validate_payment_request

router = APIRouter(prefix="/groups/{group_id}/payments", tags=["payments"])


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def request_payment(
    group_id: int,
    body: Annotated[Any, Body(examples=[{"expense_id": 1}])],
    db: SessionDep,
    x_user: UserHeader = None,
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)
    expense_id = validate_payment_request(body)
    if isinstance(expense_id, Failure):
        return failure_response(expense_id)

    result = payment_service.request_payment(db, group, user, expense_id)
    if isinstance(result, Failure):
        return failure_response(result)
    return created(result)


@router.get("", response_model=list[PaymentOut])
def list_payments(
    group_id: int, db: SessionDep, x_user: UserHeader = None
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    return ok(payment_service.list_payments(db, group))


@router.post("/{payment_id}/confirm", response_model=PaymentOut)
def confirm_payment(
    group_id: int, payment_id: int, db: SessionDep, x_user: UserHeader = None
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    result = payment_service.decide_payment(db, group, user, payment_id, "confirmed")
    if isinstance(result, Failure):
        return failure_response(result)
    return ok(result)


@router.post("/{payment_id}/reject", response_model=PaymentOut)
def reject_payment(
    group_id: int, payment_id: int, db: SessionDep, x_user: UserHeader = None
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    result = payment_service.decide_payment(db, group, user, payment_id, "rejected")
    if isinstance(result, Failure):
        return failure_response(result)
    return ok(result)
