import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import equal_split, list_expenses, post_expense

DINNER = equal_split("1000.00", ["alice", "bob", "carol"])


def test_repeated_idempotency_key_creates_only_one_expense(client):
    first = post_expense(client, DINNER, key="7f3c2a10-dinner-0001")
    second = post_expense(client, DINNER, key="7f3c2a10-dinner-0001")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len(list_expenses(client).json()) == 1


KEY_REUSED = {
    "error": {
        "code": "idempotency_key_reused",
        "message": "This Idempotency-Key was already used with a different request.",
    }
}


def test_repeated_key_with_a_different_request_is_rejected(client):
    post_expense(client, DINNER, key="reused-key")
    taxi = equal_split("200.00", ["alice", "bob"], description="Taxi")

    response = post_expense(client, taxi, key="reused-key")

    assert response.status_code == 422
    assert response.json() == KEY_REUSED
    assert [expense["description"] for expense in list_expenses(client).json()] == [
        "Dinner"
    ]


def test_repeated_key_with_members_in_a_different_order_is_rejected(client):
    post_expense(client, DINNER, key="reordered-key")
    reordered = equal_split("1000.00", ["carol", "bob", "alice"])

    response = post_expense(client, reordered, key="reordered-key")

    assert response.status_code == 422
    assert response.json() == KEY_REUSED


def test_repeated_key_with_an_equivalent_amount_is_the_same_request(client):
    first = post_expense(client, DINNER, key="equivalent-key")
    equivalent = equal_split("1000.0", ["alice", "bob", "carol"])

    second = post_expense(client, equivalent, key="equivalent-key")

    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_same_key_in_different_groups_creates_separate_expenses(client):
    lunch = equal_split("100.00", ["bob", "dan"], paid_by="bob")

    in_group_1 = post_expense(client, DINNER, user="bob", group_id=1, key="shared")
    in_group_2 = post_expense(client, lunch, user="bob", group_id=2, key="shared")

    assert in_group_1.status_code == in_group_2.status_code == 201
    assert in_group_1.json()["id"] != in_group_2.json()["id"]


def test_concurrent_requests_with_the_same_key_create_only_one_expense(client):
    concurrency = 8
    barrier = threading.Barrier(concurrency)

    def send(_):
        thread_client = TestClient(app)
        barrier.wait()  # release every request at the same moment
        return post_expense(thread_client, DINNER, key="concurrent-key")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        responses = list(pool.map(send, range(concurrency)))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [200] * (concurrency - 1) + [201]
    assert len({response.json()["id"] for response in responses}) == 1
    assert len(list_expenses(client).json()) == 1


def test_repeated_key_after_deletion_returns_the_original_expense(client):
    # Documented assumption (README): the brief says a repeated key returns the
    # expense originally created; that holds even after it was deleted.
    first = post_expense(client, DINNER, key="deleted-key")
    client.delete(
        f"/groups/1/expenses/{first.json()['id']}", headers={"X-User": "alice"}
    )

    replay = post_expense(client, DINNER, key="deleted-key")

    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert list_expenses(client).json() == []
