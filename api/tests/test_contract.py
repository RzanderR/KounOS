"""Route contract test (A03): the OpenAPI docs load and list every resource."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_openapi_lists_every_resource() -> None:
    """OpenAPI docs load and include every resource the web app calls."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    prefixes = ("/solicitations", "/quotes", "/sourcing-decisions", "/orders")
    prefixes += ("/notices", "/events", "/impact")
    for prefix in prefixes:
        assert any(path.startswith(prefix) for path in paths), prefix
