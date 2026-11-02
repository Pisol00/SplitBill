import json
import uuid
from datetime import datetime

import pytest

from tests.helpers import equal_split, exact_split, list_expenses, post_expense


def test_equal_split_of_100_among_three_members_gives_33_34_33_33_33_33(client):
    response = post_expense(client, equal_split("100.00", ["alice", "bob", "carol"]))

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "100.00"
    assert body["split_type"] == "equal"
    assert body["shares"] == [
        {"member": "alice", "amount": "33.34"},
        {"member": "bob", "amount": "33.33"},
        {"member": "carol", "amount": "33.33"},
    ]


def test_exact_split_records_the_given_shares_in_the_given_order(client):
    shares = {"carol": "200.00", "alice": "500.00", "bob": "300.00"}

    response = post_expense(client, exact_split("1000.00", shares), user="bob")

    assert response.status_code == 201
    assert response.json()["split_type"] == "exact"
    assert response.json()["shares"] == [
        {"member": "carol", "amount": "200.00"},
        {"member": "alice", "amount": "500.00"},
        {"member": "bob", "amount": "300.00"},
    ]


def test_exact_split_not_summing_to_the_amount_is_rejected(client):
    shares = {"alice": "500.00", "bob": "300.00", "carol": "100.00"}

    response = post_expense(client, exact_split("1000.00", shares))

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "shares_mismatch",
            "message": "The shares do not add up to the total.",
        }
    }
    assert list_expenses(client).json() == []


def assert_validation_error(response):
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_amount_with_3_decimal_places_is_rejected(client):
    response = post_expense(client, equal_split("10.005", ["alice", "bob"]))

    assert_validation_error(response)
    assert list_expenses(client).json() == []


@pytest.mark.parametrize(
    "amount",
    [
        "0.00",  # not greater than zero
        "-5.00",  # negative
        "10000000000.00",  # above NUMERIC(12,2)
        "1e3",  # exponent notation
        " 10.00",  # surrounding whitespace
        "abc",
        "๑๐.๕๐",  # digits outside 0-9
        100,  # JSON number instead of string
        10.5,  # JSON float instead of string
    ],
)
def test_invalid_amount_is_rejected(client, amount):
    response = post_expense(client, equal_split(amount, ["alice", "bob"]))

    assert_validation_error(response)


def test_exact_share_with_3_decimal_places_is_rejected(client):
    shares = {"alice": "500.005", "bob": "499.995"}

    response = post_expense(client, exact_split("1000.00", shares))

    assert_validation_error(response)


def test_amounts_with_fewer_decimal_places_are_accepted(client):
    response = post_expense(client, equal_split("10.5", ["alice", "bob"]))

    assert response.status_code == 201
    assert response.json()["amount"] == "10.50"


MEMBER_NOT_IN_GROUP = {
    "error": {
        "code": "member_not_in_group",
        "message": "Every member of the expense must belong to the group.",
    }
}


@pytest.mark.parametrize(
    "body",
    [
        equal_split("90.00", ["alice", "bob"], paid_by="dan"),  # payer outside group
        equal_split("90.00", ["alice", "dan"]),  # equal split member outside group
        equal_split("90.00", ["alice", "zoe"]),  # user that does not exist
        exact_split("90.00", {"alice": "45.00", "dan": "45.00"}),  # exact split
    ],
)
def test_payer_and_split_members_must_belong_to_the_group(client, body):
    response = post_expense(client, body)

    assert response.status_code == 422
    assert response.json() == MEMBER_NOT_IN_GROUP


def test_member_may_record_an_expense_paid_by_another_member(client):
    response = post_expense(
        client, equal_split("90.00", ["alice", "bob"], paid_by="bob"), user="alice"
    )

    assert response.status_code == 201
    assert response.json()["paid_by"] == "bob"


@pytest.mark.parametrize(
    "body",
    [
        equal_split("90.00", ["alice", "alice"]),  # duplicate member
        equal_split("90.00", []),  # no members
        exact_split("90.00", {}),  # no shares
        equal_split("90.00", ["alice"], description=""),
        equal_split("90.00", ["alice"], description="   "),
        equal_split("90.00", ["alice"], description="x" * 256),
        equal_split(
            "90.00", ["alice"], description="a\u0000b"
        ),  # PostgreSQL rejects it
        exact_split("90.00", {"alice": "๙๐.๐๐"}),  # digits outside 0-9
        {**equal_split("90.00", ["alice"]), "split": {"type": "percent"}},
    ],
)
def test_invalid_expense_request_is_rejected(client, body):
    assert_validation_error(post_expense(client, body))


def test_expense_without_idempotency_key_is_rejected(client):
    response = client.post(
        "/groups/1/expenses",
        json=equal_split("90.00", ["alice", "bob"]),
        headers={"X-User": "alice"},
    )

    assert_validation_error(response)


def test_description_is_trimmed(client):
    response = post_expense(
        client, equal_split("90.00", ["alice"], description=" Taxi ")
    )

    assert response.status_code == 201
    assert response.json()["description"] == "Taxi"


def test_expenses_are_listed_newest_first_in_the_post_response_shape(client):
    dinner = post_expense(client, equal_split("1000.00", ["alice", "bob", "carol"]))
    hotel = post_expense(
        client,
        exact_split("900.00", {"alice": "300.00", "bob": "300.00", "carol": "300.00"}),
        user="bob",
    )

    response = list_expenses(client, user="carol")

    assert response.status_code == 200
    assert response.json() == [hotel.json(), dinner.json()]


def test_group_without_expenses_lists_nothing(client):
    response = list_expenses(client)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("key", ["", "k" * 256])
def test_idempotency_key_must_be_1_to_255_characters(client, key):
    response = client.post(
        "/groups/1/expenses",
        json=equal_split("90.00", ["alice", "bob"]),
        headers={"X-User": "alice", "Idempotency-Key": key},
    )

    assert_validation_error(response)


@pytest.mark.parametrize(
    "content", ['["not", "an", "object"]', '"text"', "{not json", ""]
)
def test_body_that_is_not_a_json_object_is_rejected(client, content):
    response = client.post(
        "/groups/1/expenses",
        content=content,
        headers={
            "X-User": "alice",
            "Idempotency-Key": "body-shape",
            "Content-Type": "application/json",
        },
    )

    assert_validation_error(response)


@pytest.mark.parametrize(
    "body",
    [
        {**equal_split("90.00", ["alice"]), "paid_by": 123},
        {**equal_split("90.00", ["alice"]), "description": 5},
        {**equal_split("90.00", ["alice"]), "split": "equal"},
        {
            **equal_split("90.00", ["alice"]),
            "split": {"type": "equal", "members": "alice"},
        },
        {**equal_split("90.00", ["alice"]), "split": {"type": "equal", "members": [1]}},
        exact_split("90.00", ["alice", "90.00"]),
        {
            key: value
            for key, value in equal_split("90.00", ["alice"]).items()
            if key != "paid_by"
        },
    ],
)
def test_fields_of_the_wrong_type_are_rejected(client, body):
    assert_validation_error(post_expense(client, body))


def test_created_expense_has_every_field_from_the_api_design(client):
    body = equal_split("1000.00", ["alice", "bob", "carol"], description="Dinner")

    expense = post_expense(client, body).json()

    assert set(expense) == {
        "id",
        "group_id",
        "description",
        "paid_by",
        "amount",
        "split_type",
        "shares",
        "created_at",
    }
    assert isinstance(expense["id"], int)
    assert expense["group_id"] == 1
    assert expense["description"] == "Dinner"
    assert expense["paid_by"] == "alice"
    assert expense["amount"] == "1000.00"
    assert expense["split_type"] == "equal"
    assert all(set(share) == {"member", "amount"} for share in expense["shares"])
    # ISO 8601 with a time zone, so clients can convert it to local time.
    created_at = datetime.fromisoformat(expense["created_at"])
    assert created_at.utcoffset() is not None


@pytest.mark.parametrize(
    "body",
    [
        equal_split("90.00", ["alice"], description="a\ud800b"),
        equal_split("90.00", ["alice"], paid_by="a\ud800b"),
        equal_split("90.00", ["a\ud800b"]),
        exact_split("90.00", {"a\ud800b": "90.00"}),
        equal_split("90.00", ["alice"], paid_by="a\u0000b"),
        equal_split("90.00", ["a\u0000b"]),
    ],
)
def test_text_that_cannot_be_stored_is_rejected_without_a_server_error(client, body):
    # json.dumps keeps a lone surrogate as an escape, as a client could send it.
    response = client.post(
        "/groups/1/expenses",
        content=json.dumps(body),
        headers={
            "X-User": "alice",
            "Idempotency-Key": str(uuid.uuid4()),
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 422
