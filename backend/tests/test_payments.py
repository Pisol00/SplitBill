import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import (
    confirm_payment,
    delete_expense,
    equal_split,
    exact_split,
    list_payments,
    post_expense,
    reject_payment,
    request_payment,
)


@pytest.fixture
def dinner(client):
    """100.00 paid by alice: alice 33.34, bob 33.33, carol 33.33."""
    body = equal_split("100.00", ["alice", "bob", "carol"], paid_by="alice")
    return post_expense(client, body).json()["id"]


def balances(client, group_id=1):
    response = client.get(f"/groups/{group_id}/balances", headers={"X-User": "alice"})
    return {row["member"]: row["balance"] for row in response.json()}


def error_code(response):
    return response.json()["error"]["code"]


def test_member_requests_a_payment_for_their_share(client, dinner):
    response = request_payment(client, dinner, user="bob")

    assert response.status_code == 201
    body = response.json()
    assert body["expense_id"] == dinner
    assert body["from_member"] == "bob"
    assert body["to_member"] == "alice"
    assert body["amount"] == "33.33"
    assert body["status"] == "pending"
    assert body["decided_at"] is None
    assert set(body) == {
        "id",
        "expense_id",
        "from_member",
        "to_member",
        "amount",
        "status",
        "created_at",
        "decided_at",
    }


def test_pending_payment_does_not_change_balances(client, dinner):
    before = balances(client)

    request_payment(client, dinner, user="bob")

    assert balances(client) == before


def test_confirmed_payment_updates_balances_and_they_still_sum_to_zero(client, dinner):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]

    response = confirm_payment(client, payment_id, user="alice")

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert response.json()["decided_at"] is not None
    after = balances(client)
    assert after == {"alice": "33.33", "bob": "0.00", "carol": "-33.33"}
    assert sum(Decimal(balance) for balance in after.values()) == Decimal("0.00")


def test_rejected_payment_does_not_change_balances(client, dinner):
    before = balances(client)
    payment_id = request_payment(client, dinner, user="bob").json()["id"]

    response = reject_payment(client, payment_id, user="alice")

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert balances(client) == before


def test_a_member_can_request_again_after_a_rejection(client, dinner):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    reject_payment(client, payment_id, user="alice")

    response = request_payment(client, dinner, user="bob")

    assert response.status_code == 201
    assert response.json()["id"] != payment_id


@pytest.mark.parametrize("decide", ["pending", "confirmed"])
def test_a_share_cannot_be_requested_twice(client, dinner, decide):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    if decide == "confirmed":
        confirm_payment(client, payment_id, user="alice")

    response = request_payment(client, dinner, user="bob")

    assert response.status_code == 409
    assert error_code(response) == "payment_already_requested"
    assert len(list_payments(client).json()) == 1


def test_the_payer_of_the_expense_cannot_pay_their_own_share(client, dinner):
    response = request_payment(client, dinner, user="alice")

    assert response.status_code == 422
    assert error_code(response) == "own_share"


def test_a_member_without_a_share_cannot_request_a_payment(client):
    body = equal_split("100.00", ["alice", "bob"], paid_by="alice")
    expense_id = post_expense(client, body).json()["id"]

    response = request_payment(client, expense_id, user="carol")

    assert response.status_code == 422
    assert error_code(response) == "no_share"


def test_a_share_of_zero_cannot_be_requested(client):
    body = exact_split("100.00", {"alice": "100.00", "bob": "0.00"}, paid_by="alice")
    expense_id = post_expense(client, body).json()["id"]

    response = request_payment(client, expense_id, user="bob")

    assert response.status_code == 422
    assert error_code(response) == "no_share"


@pytest.mark.parametrize("user", ["bob", "carol"])
def test_only_the_payer_of_the_expense_can_decide(client, dinner, user):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    before = balances(client)

    confirmed = confirm_payment(client, payment_id, user=user)
    rejected = reject_payment(client, payment_id, user=user)

    assert confirmed.status_code == rejected.status_code == 403
    assert error_code(confirmed) == error_code(rejected) == "not_payment_receiver"
    assert list_payments(client).json()[0]["status"] == "pending"
    assert balances(client) == before


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (confirm_payment, confirm_payment),
        (confirm_payment, reject_payment),
        (reject_payment, confirm_payment),
        (reject_payment, reject_payment),
    ],
)
def test_a_payment_can_be_decided_only_once(client, dinner, first, second):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    first(client, payment_id, user="alice")
    after_first = balances(client)

    response = second(client, payment_id, user="alice")

    assert response.status_code == 409
    assert error_code(response) == "payment_not_pending"
    assert balances(client) == after_first


@pytest.mark.parametrize("decide", [confirm_payment, reject_payment])
@pytest.mark.parametrize("payment_id", [999, 99999999999])
def test_deciding_a_missing_payment_returns_404(client, decide, payment_id):
    response = decide(client, payment_id, user="alice")

    assert response.status_code == 404
    assert error_code(response) == "payment_not_found"


def test_a_payment_from_another_group_is_not_found(client):
    lunch = equal_split("100.00", ["bob", "dan"], paid_by="bob")
    expense_id = post_expense(client, lunch, user="bob", group_id=2).json()["id"]
    payment_id = request_payment(client, expense_id, user="dan", group_id=2).json()[
        "id"
    ]

    response = confirm_payment(client, payment_id, user="bob", group_id=1)

    assert response.status_code == 404
    assert error_code(response) == "payment_not_found"


def test_an_expense_from_another_group_is_not_found(client):
    lunch = equal_split("100.00", ["bob", "dan"], paid_by="bob")
    expense_id = post_expense(client, lunch, user="bob", group_id=2).json()["id"]

    response = request_payment(client, expense_id, user="bob", group_id=1)

    assert response.status_code == 404
    assert error_code(response) == "expense_not_found"


def test_a_deleted_expense_cannot_be_paid(client, dinner):
    delete_expense(client, dinner, user="alice")

    response = request_payment(client, dinner, user="bob")

    assert response.status_code == 404
    assert error_code(response) == "expense_not_found"


@pytest.mark.parametrize(
    "body",
    [
        [],
        {},
        {"expense_id": "1"},
        {"expense_id": 1.5},
        {"expense_id": True},
        {"expense_id": None},
    ],
)
def test_an_invalid_body_is_rejected(client, body):
    response = client.post("/groups/1/payments", json=body, headers={"X-User": "bob"})

    assert response.status_code == 422
    assert error_code(response) == "validation_error"


def test_expense_id_outside_the_integer_range_is_not_found(client):
    response = request_payment(client, 99999999999, user="bob")

    assert response.status_code == 404
    assert error_code(response) == "expense_not_found"


@pytest.mark.parametrize("decide", ["pending", "confirmed"])
def test_an_expense_with_an_open_payment_cannot_be_deleted(client, dinner, decide):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    if decide == "confirmed":
        confirm_payment(client, payment_id, user="alice")

    response = delete_expense(client, dinner, user="alice")

    assert response.status_code == 409
    assert error_code(response) == "expense_has_payments"


def test_an_expense_with_only_rejected_payments_can_be_deleted(client, dinner):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    reject_payment(client, payment_id, user="alice")

    response = delete_expense(client, dinner, user="alice")

    assert response.status_code == 204
    assert list_payments(client).json() == []


def test_payments_are_listed_newest_first(client, dinner):
    bob = request_payment(client, dinner, user="bob").json()["id"]
    carol = request_payment(client, dinner, user="carol").json()["id"]

    response = list_payments(client)

    assert response.status_code == 200
    assert [payment["id"] for payment in response.json()] == [carol, bob]


def test_payments_of_another_group_are_not_listed(client, dinner):
    request_payment(client, dinner, user="bob")

    assert list_payments(client, user="bob", group_id=2).json() == []


def test_concurrent_requests_for_a_share_create_only_one_payment(client, dinner):
    concurrency = 5
    barrier = threading.Barrier(concurrency)

    def send(_):
        with TestClient(app) as worker:
            barrier.wait()
            return request_payment(worker, dinner, user="bob").status_code

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        statuses = list(pool.map(send, range(concurrency)))

    assert sorted(statuses) == [201, 409, 409, 409, 409]
    assert len(list_payments(client).json()) == 1


def test_concurrent_decisions_apply_exactly_one(client, dinner):
    payment_id = request_payment(client, dinner, user="bob").json()["id"]
    concurrency = 6
    barrier = threading.Barrier(concurrency)

    def send(index):
        decide = confirm_payment if index % 2 == 0 else reject_payment
        with TestClient(app) as worker:
            barrier.wait()
            return decide(worker, payment_id, user="alice")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        responses = list(pool.map(send, range(concurrency)))

    assert sorted(r.status_code for r in responses) == [200, 409, 409, 409, 409, 409]
    winner = next(r for r in responses if r.status_code == 200)
    assert list_payments(client).json()[0]["status"] == winner.json()["status"]
    assert sum(Decimal(b) for b in balances(client).values()) == Decimal("0.00")


def test_concurrent_request_and_delete_never_leave_a_payment_on_a_deleted_expense(
    client, dinner
):
    barrier = threading.Barrier(2)

    def send(action):
        with TestClient(app) as worker:
            barrier.wait()
            return action(worker)

    actions = [
        lambda worker: request_payment(worker, dinner, user="bob"),
        lambda worker: delete_expense(worker, dinner, user="alice"),
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        requested, deleted = pool.map(send, actions)

    # Whichever locks the expense first wins; the other sees the result.
    assert (requested.status_code, deleted.status_code) in [(201, 409), (404, 204)]
