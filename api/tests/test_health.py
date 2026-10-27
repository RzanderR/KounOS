"""Health route tests (A01)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok(monkeypatch) -> None:
    """GET /health returns 200 with status ok in live mode."""
    monkeypatch.setenv("DEMO_MODE", "live")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo_mode": "live"}


def test_health_replay_mode(monkeypatch) -> None:
    """GET /health reflects DEMO_MODE=replay."""
    monkeypatch.setenv("DEMO_MODE", "replay")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo_mode": "replay"}
