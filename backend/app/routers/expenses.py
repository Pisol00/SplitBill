from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, Response, status
from fastapi.responses import JSONResponse

from app.core.error_handlers import failure_response
from app.core.errors import Failure
from app.dependencies import (
    SessionDep,
    UserHeader,
    get_current_user,
    get_member_group,
)
from app.schemas import ExpenseOut
from app.services import expenses as expense_service
from app.utils.responses import created, no_content, ok
from app.validators.expenses import validate_expense_request
from app.validators.headers import validate_idempotency_key

router = APIRouter(prefix="/groups/{group_id}/expenses", tags=["expenses"])

# Shown in Swagger UI. The body is validated by validate_expense_request, not by a
# schema, so this example is the documentation of its shape (see docs/api.md).
EXAMPLE_BODY = {
    "description": "Dinner at the night market",
    "paid_by": "alice",
    "amount": "1000.00",
    "split": {"type": "equal", "members": ["alice", "bob", "carol"]},
}


@router.post(
    "",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "model": ExpenseOut,
            "description": "Repeated Idempotency-Key: the original expense",
        }
    },
)
def create_expense(
    group_id: int,
    body: Annotated[Any, Body(examples=[EXAMPLE_BODY])],
    db: SessionDep,
    x_user: UserHeader = None,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)
    request = validate_expense_request(body)
    if isinstance(request, Failure):
        return failure_response(request)
    key = validate_idempotency_key(idempotency_key)
    if isinstance(key, Failure):
        return failure_response(key)

    result = expense_service.create_expense(db, group, request, key)
    if isinstance(result, Failure):
        return failure_response(result)
    expense, is_new = result
    if is_new:
        return created(expense)
    # A replay of an earlier request: the original expense, nothing new was created.
    return ok(expense)


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    group_id: int, db: SessionDep, x_user: UserHeader = None
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    return ok(expense_service.list_expenses(db, group))


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    group_id: int, expense_id: int, db: SessionDep, x_user: UserHeader = None
) -> Response:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    failure = expense_service.delete_expense(db, group, user, expense_id)
    if failure is not None:
        return failure_response(failure)
    return no_content()
