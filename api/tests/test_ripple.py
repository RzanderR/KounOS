"""Delay ripple tests (A39): code figures for date, margin, cash, risk."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.order_store import get_detail, reset
from app.ripple import build_ripple
from app.schemas import Event

client = TestClient(app)


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


def test_no_ripple_when_on_track() -> None:
    """Reset state shows no ripple section."""
    reset()
    assert build_ripple("ORD-001") is None
    response = client.get("/orders/ORD-001/ripple")
    assert response.status_code == 200
    assert response.json() is None


def test_ripple_figures_match_engine_and_seed() -> None:
    """Date, margins, cash and risks off code, not prose."""
    apply_delay()
    ripple = build_ripple("ORD-001")
    assert ripple is not None
    assert ripple.event_id == "EVT-test"
    assert ripple.arrival_date == date(2027, 1, 3)
    assert ripple.customer_due_date == date(2027, 1, 1)
    assert ripple.days_late == 2
    assert ripple.margin_now == Decimal("10.00")
    assert ripple.margin_expedited == Decimal("8.79")
    assert ripple.expedite_cost == Decimal("1100.00")
    assert ripple.deposit_due == Decimal("41035.00")
    assert ripple.invoice_balance == Decimal("91189.92")
    assert any("2 days late" in risk for risk in ripple.risks)


def test_unknown_order_404s() -> None:
    """The router translates an unknown order to 404."""
    response = client.get("/orders/ORD-999/ripple")
    assert response.status_code == 404
