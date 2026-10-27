"""Health route tests (A01)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("mode", ["live", "replay"])
def test_health_reflects_demo_mode(monkeypatch, mode: str) -> None:
    """GET /health returns 200 with status ok for both demo modes."""
    monkeypatch.setenv("DEMO_MODE", mode)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo_mode": mode}


def test_health_defaults_to_live_without_env(monkeypatch) -> None:
    """GET /health defaults to live when DEMO_MODE is unset."""
    monkeypatch.delenv("DEMO_MODE", raising=False)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo_mode": "live"}
