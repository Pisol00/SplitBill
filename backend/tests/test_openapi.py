import pytest
from fastapi.testclient import TestClient

from app.main import app

# Every endpoint that returns a body must document its shape for Swagger UI.
# Routers return JSONResponse via app.utils.responses, so FastAPI only knows the
# shape if the route declares response_model.
DOCUMENTED_RESPONSES = [
    ("get", "/health", "200", "HealthOut"),
    ("get", "/groups", "200", "GroupSummary"),
    ("get", "/groups/{group_id}", "200", "GroupDetail"),
    ("get", "/groups/{group_id}/balances", "200", "BalanceOut"),
    ("post", "/groups/{group_id}/expenses", "201", "ExpenseOut"),
    ("post", "/groups/{group_id}/expenses", "200", "ExpenseOut"),
    ("get", "/groups/{group_id}/expenses", "200", "ExpenseOut"),
    ("post", "/groups/{group_id}/payments", "201", "PaymentOut"),
    ("get", "/groups/{group_id}/payments", "200", "PaymentOut"),
    ("post", "/groups/{group_id}/payments/{payment_id}/confirm", "200", "PaymentOut"),
    ("post", "/groups/{group_id}/payments/{payment_id}/reject", "200", "PaymentOut"),
]


@pytest.fixture(scope="module")
def spec():
    return TestClient(app).get("/openapi.json").json()


@pytest.mark.parametrize(("method", "path", "status", "schema"), DOCUMENTED_RESPONSES)
def test_endpoint_documents_its_response_schema(spec, method, path, status, schema):
    content = spec["paths"][path][method]["responses"][status]["content"]
    documented = content["application/json"]["schema"]

    # A list response wraps the schema reference in "items".
    reference = documented.get("items", documented).get("$ref", "")
    assert reference == f"#/components/schemas/{schema}"


def test_delete_documents_an_empty_204_response(spec):
    responses = spec["paths"]["/groups/{group_id}/expenses/{expense_id}"]["delete"][
        "responses"
    ]

    assert "204" in responses
    assert "content" not in responses["204"]
