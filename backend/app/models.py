"""Database models. See docs/schema.md for the design and its rationale."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

# NUMERIC(12,2): up to 9,999,999,999.99, exact to the satang.
Money = Numeric(12, 2)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True, index=True
    )


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        # The payer must be a member of the expense's group.
        ForeignKeyConstraint(
            ["group_id", "paid_by_id"],
            ["group_members.group_id", "group_members.user_id"],
        ),
        UniqueConstraint("group_id", "idempotency_key"),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("split_type IN ('equal', 'exact')", name="split_type_valid"),
        Index(None, "group_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    paid_by_id: Mapped[int]
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Money)
    split_type: Mapped[str] = mapped_column(String(10))
    idempotency_key: Mapped[str] = mapped_column(String(255))
    request_hash: Mapped[str] = mapped_column(CHAR(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    shares: Mapped[list[ExpenseShare]] = relationship(order_by="ExpenseShare.position")


class ExpenseShare(Base):
    __tablename__ = "expense_shares"
    __table_args__ = (
        # Position decides who receives the remainder satang in an equal split.
        UniqueConstraint("expense_id", "position"),
        CheckConstraint("position >= 0", name="position_non_negative"),
        CheckConstraint("amount >= 0", name="amount_non_negative"),
    )

    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    position: Mapped[int] = mapped_column(SmallInteger)
    amount: Mapped[Decimal] = mapped_column(Money)
