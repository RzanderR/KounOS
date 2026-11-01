"""Impact analysis tests (A21): code prices, models only explain.

No test here calls a model: ``impact._request`` is faked. The live
MODEL_IMPACT run happens once against the API with its output stored
under data/extractions/.
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app import impact
from app.config import Settings
from app.main import app
from app.order_store import get_detail, reset
from app.schemas import Event

client = TestClient(app)

SUMMARIES = {
    "expedite_overnight": "Pay $1,100 overnight freight; arrive Jan 1 on time at 8.79% margin.",
    "request_extension": "Ask the CO for two days; margin stays 10.00% if they agree.",
    "partial_shipment": "Ship what is ready only if the order allows it; confirm first.",
    "switch_supplier": "No compliant alternate exists.",
}


def make_settings() -> Settings:
    """Explicit model ids so the repo-root .env can never skew the tests."""
    return Settings(
        model_api_key="test",
        model_read="muse-spark-1.3",
        model_impact="muse-wonder-1.0",
    )


def fake_request_ok(model: str, prompt: str, settings: Settings) -> dict[str, object]:
    """Canned strict-schema output; records nothing, calls nothing."""
    assert "82070" in prompt, "tools must put the landed cost in the prompt"
    return {"summaries": dict(SUMMARIES), "note": "Protect the delivery date first."}


def fake_request_fallback(
    model: str, prompt: str, settings: Settings
) -> dict[str, object]:
    """MODEL_IMPACT fails; MODEL_READ answers."""
    if model == "muse-wonder-1.0":
        raise RuntimeError("impact model unavailable")
    return {"summaries": dict(SUMMARIES), "note": "Fallback note."}


def apply_delay() -> None:
    """Move ORD-001 to the post-email state without the A18 module."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    detail.events.append(
        Event(
            event_id="EVT-test",
            order_id="ORD-001",
            source="email",
            summary="Tallgrass backorder.",
            supplier="Tallgrass Horticultural Supply",
            new_ship_date=date(2026, 12, 31),
            confidence=1.0,
        )
    )
    detail.shipments[0].ship_date = date(2026, 12, 31)
    detail.shipments[0].arrival_date = date(2027, 1, 3)


def snapshot() -> object:
    """JSON-able store state to prove the tools never mutate."""
    detail = get_detail("ORD-001")
    assert detail is not None
    return detail.model_dump_json()


def test_tools_are_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Facts, pricing and a full analysis change nothing stored."""
    apply_delay()
    before = snapshot()
    settings = make_settings()
    impact.order_facts("ORD-001")
    impact.priced_options("ORD-001")
    monkeypatch.setattr(impact, "_request", fake_request_ok)
    impact.analyze("ORD-001", settings)
    assert snapshot() == before


def test_expedite_math_matches_cost_engine() -> None:
    """$1,100 overnight: margin 10.00% to 8.79%, arrival Jan 1 on time."""
    apply_delay()
    options = {opt.name: opt for opt in impact.priced_options("ORD-001")}
    expedite = options["expedite_overnight"]
    assert expedite.cost_delta == Decimal("1100.00")
    assert expedite.new_margin_pct == Decimal("8.79")
    assert expedite.new_arrival_date == date(2027, 1, 1)
    assert expedite.on_time is True
    extension = options["request_extension"]
    assert extension.cost_delta == Decimal("0")
    assert extension.new_margin_pct == Decimal("10.00")
    assert extension.new_arrival_date == date(2027, 1, 3)


def test_switch_names_both_failing_suppliers() -> None:
    """Switching fails on the D03 verdicts, recomputed live."""
    reset()
    options = {opt.name: opt for opt in impact.priced_options("ORD-001")}
    summary = options["switch_supplier"].summary
    assert "Ninebark" in summary and "98 days" in summary
    assert "Larkspur" in summary and "PTB8850LS42" in summary


def test_partial_shipment_needs_confirmation() -> None:
    """The unpriceable option says so instead of guessing."""
    reset()
    options = {opt.name: opt for opt in impact.priced_options("ORD-001")}
    partial = options["partial_shipment"]
    assert partial.needs_confirmation is True
    assert partial.new_margin_pct is None


def test_analyze_keeps_code_figures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model prose lands on code-priced options; all four named."""
    apply_delay()
    monkeypatch.setattr(impact, "_request", fake_request_ok)
    analysis = impact.analyze("ORD-001", make_settings())
    assert analysis.generated_by == "muse-wonder-1.0"
    assert [opt.name for opt in analysis.options] == list(impact.OPTION_NAMES)
    expedite = analysis.options[0]
    assert expedite.summary == SUMMARIES["expedite_overnight"]
    assert expedite.new_margin_pct == Decimal("8.79")
    assert analysis.event_id == "EVT-test"


def test_analyze_falls_back_to_model_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A dead impact model still yields a labeled MODEL_READ analysis."""
    apply_delay()
    monkeypatch.setattr(impact, "_request", fake_request_fallback)
    analysis = impact.analyze("ORD-001", make_settings())
    assert analysis.generated_by == "muse-spark-1.3"
    assert len(analysis.options) == 4


def test_analyze_unknown_order_404s() -> None:
    """The router translates an unknown order to 404."""
    response = client.post("/impact/analyze", json={"order_id": "ORD-999"})
    assert response.status_code == 404


def test_analyze_without_model_key_is_503() -> None:
    """A missing MODEL_API_KEY answers 503 with a clear reason, not a bare 500."""
    from app.config import get_settings

    apply_delay()
    app.dependency_overrides[get_settings] = lambda: Settings(model_api_key=None)
    try:
        response = client.post("/impact/analyze", json={"order_id": "ORD-001"})
    finally:
        app.dependency_overrides.pop(get_settings, None)
    assert response.status_code == 503
    assert "MODEL_API_KEY" in response.json()["detail"]


def test_on_time_order_is_not_analyzed(monkeypatch: pytest.MonkeyPatch) -> None:
    """No delay, no recovery options and no model call."""
    reset()

    def no_model(*_: object) -> dict[str, object]:
        raise AssertionError("an on-time order must not call a model")

    monkeypatch.setattr(impact, "_request", no_model)
    with pytest.raises(impact.NoDelay):
        impact.analyze("ORD-001", make_settings())
    response = client.post("/impact/analyze", json={"order_id": "ORD-001"})
    assert response.status_code == 409
