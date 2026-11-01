"""Delay ripple (A39): what one delay changes, computed in code.

Date, margin, deposit/cash and risk for the order's latest delay event.
The expedite figure is the same one the impact analysis prices (A21).
"""

from decimal import Decimal

from app import costs, order_store
from app.impact import EXPEDITE_OVERNIGHT
from app.rules import days_late, evaluate, latest_arrival
from app.schemas import OrderDetail, Ripple


def _detail(order_id: str) -> OrderDetail:
    detail = order_store.get_detail(order_id)
    if detail is None:
        raise ValueError(f"Unknown order: {order_id}.")
    return detail


def build_ripple(order_id: str) -> Ripple | None:
    """The ripple of the latest delay event, or None when order is on track.

    A delay event is a stored event with a new ship date. Without one the
    screen shows no ripple section at all.
    """
    detail = _detail(order_id)
    order = detail.order
    delayed = [event for event in detail.events if event.new_ship_date is not None]
    if not delayed:
        return None
    event = delayed[-1]
    bid = order.bid_price or Decimal("0")
    landed = order.landed_cost or Decimal("0")
    expedite_landed = landed + EXPEDITE_OVERNIGHT
    balance = sum(
        (inv.amount for inv in detail.invoices if not inv.paid), Decimal("0")
    )
    return Ripple(
        order_id=order_id,
        event_id=event.event_id,
        arrival_date=latest_arrival(detail),
        customer_due_date=order.customer_due_date,
        days_late=days_late(detail),
        margin_now=costs.margin_at_price(landed, bid) if bid > 0 else Decimal("0"),
        margin_expedited=costs.margin_at_price(expedite_landed, bid)
        if bid > 0
        else Decimal("0"),
        expedite_cost=EXPEDITE_OVERNIGHT,
        deposit_due=detail.po.deposit_due if detail.po else Decimal("0"),
        invoice_balance=balance,
        risks=[flag.message for flag in evaluate(detail)],
    )



