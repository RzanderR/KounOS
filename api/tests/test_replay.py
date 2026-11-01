"""Replay mode tests (A27): the scripted path runs with no model and no key."""

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import impact, replay, voicemail
from app.config import Settings, get_settings
from app.main import app
from app.order_store import get_detail, reset
from app.rules import evaluate

client = TestClient(app)


def replay_settings() -> Settings:
    """Replay mode with no API key: any model call would fail."""
    return Settings(
        model_api_key=None,
        model_read="muse-spark-1.3",
        model_impact="muse-wonder-1.0",
        demo_mode="replay",
    )


@pytest.fixture(autouse=True)
def no_models(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Fail the test if anything builds a model client."""

    def refuse(*_: object, **__: object) -> None:
        raise AssertionError("replay mode must not call a model")

    monkeypatch.setattr(voicemail, "OpenAI", refuse)
    monkeypatch.setattr(impact, "OpenAI", refuse)
    app.dependency_overrides[get_settings] = replay_settings
    yield
    app.dependency_overrides.pop(get_settings, None)
    reset()


def ingest_tallgrass() -> None:
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    voicemail.ingest_file(
        "ORD-001", "email", "tallgrass_backorder.txt", replay_settings(), detail
    )


def test_replayed_email_moves_the_order_like_a_live_read() -> None:
    """The stored read feeds the same event code: new dates, the delay flag."""
    ingest_tallgrass()
    detail = get_detail("ORD-001")
    assert detail is not None
    event = detail.events[-1]
    assert event.supplier == "Tallgrass Horticultural Supply"
    assert event.new_ship_date == date(2026, 12, 31)
    assert detail.shipments[0].arrival_date == date(2027, 1, 3)
    messages = [flag.message for flag in evaluate(detail)]
    assert "Arrival 2027-01-03 is 2 days late (due 2027-01-01)." in messages


def test_replayed_options_are_grounded_and_labeled() -> None:
    """Code prices the options; the stored prose passes the same figure check."""
    ingest_tallgrass()
    analysis = impact.analyze("ORD-001", replay_settings())
    assert analysis.generated_by == "muse-wonder-1.0 (replay)"
    assert analysis.grounded is True
    expedite = analysis.options[0]
    assert expedite.name == "expedite_overnight"
    assert expedite.cost_delta == Decimal("1100.00")
    assert expedite.new_margin_pct == Decimal("8.79")
    stored = replay.stored("impact_ORD-001")["response"]
    assert expedite.summary == stored["summaries"]["expedite_overnight"]
    assert analysis.note == stored["note"]


def test_scripted_path_over_http() -> None:
    """Reset, ingest, analyze: every route answers without a model."""
    assert client.post("/demo/reset").status_code == 200
    ingest = client.post(
        "/events/ingest",
        json={"order_id": "ORD-001", "source": "email", "filename": "tallgrass_backorder.txt"},
    )
    assert ingest.status_code == 200
    response = client.post("/impact/analyze", json={"order_id": "ORD-001"})
    assert response.status_code == 200
    assert response.json()["generated_by"] == "muse-wonder-1.0 (replay)"


def test_step_without_a_stored_response_is_503(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Off the scripted path, replay refuses instead of calling a model."""
    monkeypatch.setattr(replay, "REPLAY_DIR", tmp_path)
    response = client.post(
        "/events/ingest",
        json={"order_id": "ORD-001", "source": "email", "filename": "tallgrass_backorder.txt"},
    )
    assert response.status_code == 503
    assert "no stored response" in response.json()["detail"]
