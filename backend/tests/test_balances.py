import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import delete_expense, equal_split, exact_split, post_expense


def get_balances(client, user="alice", group_id=1):
    return client.get(f"/groups/{group_id}/balances", headers={"X-User": user})


def total(balances):
    return sum(Decimal(entry["balance"]) for entry in balances)


def test_equal_split_of_100_among_three_balances_sum_to_zero(client):
    post_expense(client, equal_split("100.00", ["alice", "bob", "carol"]))

    response = get_balances(client)

    assert response.status_code == 200
    assert response.json() == [
        {"member": "alice", "balance": "66.66"},
        {"member": "bob", "balance": "-33.33"},
        {"member": "carol", "balance": "-33.33"},
    ]
    assert total(response.json()) == Decimal("0.00")


def test_group_without_expenses_has_zero_balances(client):
    response = get_balances(client, user="dan", group_id=2)

    assert response.status_code == 200
    assert response.json() == [
        {"member": "bob", "balance": "0.00"},
        {"member": "dan", "balance": "0.00"},
    ]


def test_balances_combine_split_types_and_exclude_deleted_expenses(client):
    trio = ["alice", "bob", "carol"]
    hotel = {"alice": "500.00", "bob": "300.00", "carol": "100.00"}
    post_expense(client, equal_split("1000.00", trio, paid_by="alice"))
    post_expense(client, exact_split("900.00", hotel, paid_by="bob"))
    taxi = post_expense(
        client, equal_split("100.00", ["carol", "alice"], paid_by="carol"), user="carol"
    )
    post_expense(client, equal_split("0.01", trio, paid_by="bob"))
    delete_expense(client, taxi.json()["id"], user="carol")

    response = get_balances(client)

    # Worked out by hand; the deleted taxi expense does not count.
    assert response.json() == [
        {"member": "alice", "balance": "166.65"},
        {"member": "bob", "balance": "266.68"},
        {"member": "carol", "balance": "-433.33"},
    ]
    assert total(response.json()) == Decimal("0.00")


def test_balances_sum_to_zero_while_expenses_are_being_recorded(client):
    trio = ["alice", "bob", "carol"]
    recording = threading.Event()
    recording.set()

    def record():
        writer = TestClient(app)
        try:
            for _ in range(40):
                post_expense(writer, equal_split("100.00", trio))
        finally:
            recording.clear()

    def read(_):
        reader = TestClient(app)
        totals = []
        while recording.is_set():
            totals.append(total(get_balances(reader).json()))
        return totals

    with ThreadPoolExecutor(max_workers=4) as pool:
        readers = [pool.submit(read, i) for i in range(3)]
        record()
        totals = [value for reader in readers for value in reader.result()]

    assert totals
    assert set(totals) == {Decimal("0.00")}
