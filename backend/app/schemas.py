"""Response models: the JSON shapes the API returns. Input is in validators/."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

# Money leaves the API as a string with exactly two decimal places.
MoneyOut = Annotated[Decimal, PlainSerializer(lambda value: f"{value:.2f}", str)]


class HealthOut(BaseModel):
    status: str


class GroupSummary(BaseModel):
    id: int
    name: str


class GroupDetail(BaseModel):
    id: int
    name: str
    members: list[str]


class ShareOut(BaseModel):
    member: str
    amount: MoneyOut


class ExpenseOut(BaseModel):
    id: int
    group_id: int
    description: str
    paid_by: str
    amount: MoneyOut
    split_type: str
    shares: list[ShareOut]
    created_at: datetime


class BalanceOut(BaseModel):
    member: str
    balance: MoneyOut


class PaymentOut(BaseModel):
    id: int
    expense_id: int
    from_member: str
    to_member: str
    amount: MoneyOut
    status: str
    created_at: datetime
    decided_at: datetime | None
