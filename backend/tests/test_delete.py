from sqlalchemy import text

from app.core.db import engine
from tests.helpers import delete_expense, equal_split, list_expenses, post_expense

NOT_PAYER = {
    "error": {
        "code": "not_payer",
        "message": "Only the payer can delete this expense.",
    }
}

EXPENSE_NOT_FOUND = {
    "error": {
        "code": "expense_not_found",
        "message": "Expense not found.",
    }
}


def record_expense_paid_by_bob_recorded_by_alice(client):
    body = equal_split("90.00", ["alice", "bob", "carol"], paid_by="bob")
    return post_expense(client, body, user="alice").json()["id"]


def test_only_the_payer_can_delete_an_expense(client):
    expense_id = record_expense_paid_by_bob_recorded_by_alice(client)

    by_other_member = delete_expense(client, expense_id, user="carol")
    by_recorder = delete_expense(client, expense_id, user="alice")
    by_payer = delete_expense(client, expense_id, user="bob")

    assert by_other_member.status_code == 403
    assert by_other_member.json() == NOT_PAYER
    assert by_recorder.status_code == 403
    assert by_recorder.json() == NOT_PAYER
    assert by_payer.status_code == 204
    assert by_payer.content == b""


def test_deleted_expense_is_hidden_but_retained_and_flagged(client):
    expense_id = record_expense_paid_by_bob_recorded_by_alice(client)

    delete_expense(client, expense_id, user="bob")

    assert list_expenses(client).json() == []
    # Deliberate exception to testing through the API (see docs/testing.md): no
    # endpoint exposes deleted expenses, but the brief requires them to be retained.
    with engine.connect() as connection:
        deleted_at = connection.scalar(
            text("SELECT deleted_at FROM expenses WHERE id = :id"), {"id": expense_id}
        )
    assert deleted_at is not None


def test_deleting_an_already_deleted_expense_returns_404(client):
    expense_id = record_expense_paid_by_bob_recorded_by_alice(client)
    delete_expense(client, expense_id, user="bob")

    response = delete_expense(client, expense_id, user="bob")

    assert response.status_code == 404
    assert response.json() == EXPENSE_NOT_FOUND


def test_expense_from_another_group_is_not_found(client):
    lunch = equal_split("100.00", ["bob", "dan"], paid_by="bob")
    expense_id = post_expense(client, lunch, user="bob", group_id=2).json()["id"]

    response = delete_expense(client, expense_id, user="bob", group_id=1)

    assert response.status_code == 404
    assert response.json() == EXPENSE_NOT_FOUND


def test_non_member_cannot_delete_in_the_group(client):
    lunch = equal_split("100.00", ["bob", "dan"], paid_by="bob")
    expense_id = post_expense(client, lunch, user="bob", group_id=2).json()["id"]

    response = delete_expense(client, expense_id, user="alice", group_id=2)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "group_not_found"


def test_expense_id_outside_the_integer_range_is_not_found(client):
    response = delete_expense(client, 99999999999, user="alice")

    assert response.status_code == 404
    assert response.json() == EXPENSE_NOT_FOUND
