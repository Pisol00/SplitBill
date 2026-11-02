import pytest

# Every route that needs a user. Each one checks access itself, so each is tested.
GROUP_1_ROUTES = [
    ("GET", "/groups/1"),
    ("GET", "/groups/1/balances"),
    ("GET", "/groups/1/expenses"),
    ("POST", "/groups/1/expenses"),
    ("DELETE", "/groups/1/expenses/1"),
    ("GET", "/groups/1/payments"),
    ("POST", "/groups/1/payments"),
    ("POST", "/groups/1/payments/1/confirm"),
    ("POST", "/groups/1/payments/1/reject"),
]


@pytest.mark.parametrize(("method", "path"), [("GET", "/groups"), *GROUP_1_ROUTES])
def test_every_route_rejects_a_request_without_a_user(client, method, path):
    response = client.request(method, path, json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_user"


@pytest.mark.parametrize(("method", "path"), GROUP_1_ROUTES)
def test_every_group_route_rejects_a_non_member(client, method, path):
    response = client.request(method, path, json={}, headers={"X-User": "dan"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "group_not_found"


@pytest.mark.parametrize("headers", [{}, {"X-User": ""}, {"X-User": "   "}])
def test_request_without_a_user_is_rejected_with_401(client, headers):
    response = client.get("/groups", headers=headers)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "X-User"
    assert response.json() == {
        "error": {
            "code": "missing_user",
            "message": "The X-User header is required.",
        }
    }


@pytest.mark.parametrize("username", ["zoe", "Alice"])
def test_request_from_an_unknown_user_is_rejected_with_401(client, username):
    response = client.get("/groups", headers={"X-User": username})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "X-User"
    assert response.json() == {
        "error": {
            "code": "unknown_user",
            "message": "No user with this username exists.",
        }
    }


GROUP_NOT_FOUND = {
    "error": {
        "code": "group_not_found",
        "message": "Group not found.",
    }
}


def test_alice_cannot_read_group_2(client):
    response = client.get("/groups/2", headers={"X-User": "alice"})

    assert response.status_code == 404
    assert response.json() == GROUP_NOT_FOUND


def test_missing_group_and_non_member_group_get_identical_responses(client):
    not_a_member = client.get("/groups/2", headers={"X-User": "alice"})
    missing = client.get("/groups/999", headers={"X-User": "alice"})

    assert missing.status_code == not_a_member.status_code == 404
    assert missing.json() == not_a_member.json() == GROUP_NOT_FOUND
    assert missing.headers == not_a_member.headers


def test_invalid_request_uses_the_standard_error_format(client):
    response = client.get("/groups/abc", headers={"X-User": "alice"})

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "validation_error"


def test_alice_cannot_write_group_2(client):
    body = {
        "description": "Lunch",
        "paid_by": "bob",
        "amount": "100.00",
        "split": {"type": "equal", "members": ["bob", "dan"]},
    }

    response = client.post(
        "/groups/2/expenses",
        json=body,
        headers={"X-User": "alice", "Idempotency-Key": "alice-write-attempt"},
    )

    assert response.status_code == 404
    assert response.json() == GROUP_NOT_FOUND
    as_bob = client.get("/groups/2/expenses", headers={"X-User": "bob"})
    assert as_bob.json() == []


@pytest.mark.parametrize("path", ["/groups/2/expenses", "/groups/2/balances"])
def test_alice_cannot_read_group_2_expenses_or_balances(client, path):
    response = client.get(path, headers={"X-User": "alice"})

    assert response.status_code == 404
    assert response.json() == GROUP_NOT_FOUND


@pytest.mark.parametrize("group_id", [2147483648, 99999999999, -2147483649])
def test_group_id_outside_the_integer_range_is_not_found(client, group_id):
    response = client.get(f"/groups/{group_id}", headers={"X-User": "alice"})

    assert response.status_code == 404
    assert response.json() == GROUP_NOT_FOUND
