"""Rules-engine tests (A19): slip, floor and cash, computed in code."""

from datetime import date

from app.order_store import get_detail, reset
from app.rules import check_cash, check_delivery, check_margin, evaluate, evaluate_all
from app.schemas import OrderDetail


def delayed_main() -> OrderDetail:
    """ORD-001 with the Tallgrass delay applied (ship Dec 31, arrive Jan 3)."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    moved = detail.model_copy(deep=True)
    moved.shipments[0].ship_date = date(2026, 12, 31)
    moved.shipments[0].arrival_date = date(2027, 1, 3)
    return moved


def test_delay_lands_two_days_late_with_blocking_flag() -> None:
    """Arrival Jan 3 vs due Jan 1: two days late, blocking (D03 rescale)."""
    detail = delayed_main()
    flag = check_delivery(detail)
    assert flag is not None
    assert flag.severity == "blocking"
    assert "2 days late" in flag.message
    assert "2027-01-03" in flag.message
    assert any(f.code == "delivery-slip" for f in evaluate(detail))


def test_healthy_seed_has_no_delivery_flag() -> None:
    """Dec 3 arrival against Jan 1 due is on track."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    assert check_delivery(detail) is None


def test_margin_floor_and_cash_exposure() -> None:
    """Tallgrass margin 10.68% clears 10%; its $41,035 deposit flags cash."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    assert check_margin(detail) is None
    cash = check_cash(detail)
    assert cash is not None
    assert cash.severity == "warning"
    assert "41035" in cash.message
    thin = detail.model_copy(deep=True)
    thin.order.bid_price = thin.order.landed_cost
    margin_flag = check_margin(thin)
    assert margin_flag is not None
    assert "below" in margin_flag.message


def test_evaluate_all_covers_every_order() -> None:
    """The flags endpoint sees all five orders without failing."""
    reset()
    assert isinstance(evaluate_all(), list)
