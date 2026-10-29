"""Route-stub contract tests (A03): docs load, stubs 501 with owning task."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

GET_STUBS = [
    "/solicitations",
    "/orders",
    "/orders/one",
    "/notices",
    "/notices/1232SA26Q0557",
    "/notices/1232SA26Q0557/fit",
    "/events",
    "/events/flags",
]

POST_STUBS = [
    "/solicitations/1232SA26Q0557/extract",
    "/solicitations/1232SA26Q0557/gap-pass",
    "/quotes/extract",
    "/demo/reset",
    "/events",
]


def test_openapi_lists_stub_routes() -> None:
    """OpenAPI docs load and include every stubbed resource."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    prefixes = ("/solicitations", "/quotes", "/sourcing-decisions", "/orders")
    prefixes += ("/notices", "/events")
    for prefix in prefixes:
        assert any(path.startswith(prefix) for path in paths), prefix


@pytest.mark.parametrize("path", GET_STUBS)
def test_get_stubs_return_501_naming_task(path: str) -> None:
    """GET stubs fail closed and name the task that implements them."""
    response = client.get(path)
    assert response.status_code == 501
    assert "A" in response.json()["detail"]


@pytest.mark.parametrize("path", POST_STUBS)
def test_post_stubs_return_501_naming_task(path: str) -> None:
    """POST stubs fail closed and name the task that implements them."""
    response = client.post(path)
    assert response.status_code == 501
    assert "A" in response.json()["detail"]
