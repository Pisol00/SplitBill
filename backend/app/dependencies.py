"""The database session, and the access checks that each route calls itself."""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app import repositories
from app.core.db import get_db
from app.core.errors import Failure
from app.models import Group, User

SessionDep = Annotated[Session, Depends(get_db)]
UserHeader = Annotated[str | None, Header()]


def get_current_user(db: Session, x_user: str | None) -> User | Failure:
    """Identify the requesting user from X-User. See docs/api.md#authentication."""
    username = (x_user or "").strip()
    if not username:
        return Failure("missing_user", "The X-User header is required.")
    user = repositories.get_user_by_username(db, username)
    if user is None:
        return Failure("unknown_user", "No user with this username exists.")
    return user


def get_member_group(db: Session, group_id: int, user: User) -> Group | Failure:
    """The requested group, if the requesting user is a member.

    A missing group and a group the user does not belong to get the same 404, so
    non-members cannot discover which groups exist.
    """
    group = repositories.get_group_for_member(db, group_id, user.id)
    if group is None:
        return Failure("group_not_found", "Group not found.")
    return group
