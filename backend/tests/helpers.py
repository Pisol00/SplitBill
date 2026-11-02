"""Request builders shared by the API tests."""

import uuid


def post_expense(client, body, user="alice", group_id=1, key=None):
    """POST an expense with a fresh Idempotency-Key unless one is given."""
    headers = {"X-User": user, "Idempotency-Key": key or str(uuid.uuid4())}
    return client.post(f"/groups/{group_id}/expenses", json=body, headers=headers)


def equal_split(amount, members, paid_by="alice", description="Dinner"):
    return {
        "description": description,
        "paid_by": paid_by,
        "amount": amount,
        "split": {"type": "equal", "members": members},
    }


def exact_split(amount, shares, paid_by="bob", description="Hotel room"):
    return {
        "description": description,
        "paid_by": paid_by,
        "amount": amount,
        "split": {"type": "exact", "shares": shares},
    }


def list_expenses(client, user="alice", group_id=1):
    return client.get(f"/groups/{group_id}/expenses", headers={"X-User": user})


def delete_expense(client, expense_id, user, group_id=1):
    return client.delete(
        f"/groups/{group_id}/expenses/{expense_id}", headers={"X-User": user}
    )
