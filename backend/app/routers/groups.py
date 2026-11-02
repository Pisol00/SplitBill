from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app import repositories
from app.core.error_handlers import failure_response
from app.core.errors import Failure
from app.dependencies import (
    SessionDep,
    UserHeader,
    get_current_user,
    get_member_group,
)
from app.schemas import BalanceOut, GroupDetail, GroupSummary
from app.services.balances import group_balances
from app.utils.responses import ok

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupSummary])
def list_groups(db: SessionDep, x_user: UserHeader = None) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)

    groups = repositories.list_groups_for_user(db, user.id)
    return ok([GroupSummary(id=group.id, name=group.name) for group in groups])


@router.get("/{group_id}", response_model=GroupDetail)
def get_group(group_id: int, db: SessionDep, x_user: UserHeader = None) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    members = repositories.list_member_usernames(db, group.id)
    return ok(GroupDetail(id=group.id, name=group.name, members=members))


@router.get("/{group_id}/balances", response_model=list[BalanceOut])
def get_balances(
    group_id: int, db: SessionDep, x_user: UserHeader = None
) -> JSONResponse:
    user = get_current_user(db, x_user)
    if isinstance(user, Failure):
        return failure_response(user)
    group = get_member_group(db, group_id, user)
    if isinstance(group, Failure):
        return failure_response(group)

    return ok(group_balances(db, group))
