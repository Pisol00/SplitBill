"""Errors that do not come from our own code still use the standard error format."""

from fastapi.testclient import TestClient

from app import repositories
from app.core.errors import Failure
from app.main import app
from app.services import expenses as expense_service


def test_unknown_url_returns_404_in_the_standard_format(client):
    response = client.get("/nope", headers={"X-User": "alice"})

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "The requested URL was not found.",
        }
    }


def test_unsupported_method_returns_405_in_the_standard_format(client):
    # Expenses cannot be edited: the expense URL supports DELETE only.
    response = client.put("/groups/1/expenses/1", headers={"X-User": "alice"})

    assert response.status_code == 405
    assert response.headers["Allow"] == "DELETE"
    assert response.json() == {
        "error": {
            "code": "method_not_allowed",
            "message": "This method is not allowed for this URL.",
        }
    }


def test_unexpected_error_returns_500_without_leaking_details(
    client, monkeypatch, caplog
):
    def fail(*args, **kwargs):
        raise RuntimeError("secret detail: password=hunter2")

    # Simulate a bug deep inside the app.
    monkeypatch.setattr(repositories, "list_groups_for_user", fail)
    unguarded_client = TestClient(app, raise_server_exceptions=False)

    response = unguarded_client.get("/groups", headers={"X-User": "alice"})

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Something went wrong on the server.",
        }
    }
    assert "hunter2" not in response.text
    # The details are not lost: they go to the server log instead.
    assert "Unhandled error on GET /groups" in caplog.text
    assert "hunter2" in caplog.text


def test_failure_without_a_mapped_status_returns_500_in_the_standard_format(
    client, monkeypatch
):
    def fail(*args, **kwargs):
        return Failure("unmapped_code", "secret detail")

    monkeypatch.setattr(expense_service, "delete_expense", fail)
    unguarded_client = TestClient(app, raise_server_exceptions=False)

    response = unguarded_client.delete(
        "/groups/1/expenses/1", headers={"X-User": "alice"}
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret detail" not in response.text
