"""Delay ripple (A39): what one delay changes, computed in code.

Date, margin, deposit/cash and risk for the order's latest delay event.
Standalone on purpose: it reuses only costs/rules/store so the ripple
works without the A21 module. The overnight figure below must match
impact.EXPEDITE_OVERNIGHT; both are pinned to the same margin math.
"""

from decimal import Decimal

from app import costs, order_store
from app.rules import evaluate
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
    ship = detail.shipments[0] if detail.shipments else None
    arrival = ship.arrival_date if ship else None
    due = order.customer_due_date
    days_late = (
        (arrival - due).days
        if arrival is not None and due is not None and arrival > due
        else 0
    )
    bid = order.bid_price or Decimal("0")
    landed = order.landed_cost or Decimal("0")
    expedite_landed = landed + Decimal("1100.00")
    balance = sum(
        (inv.amount for inv in detail.invoices if not inv.paid), Decimal("0")
    )
    return Ripple(
        order_id=order_id,
        event_id=event.event_id,
        arrival_date=arrival,
        customer_due_date=due,
        days_late=days_late,
        margin_now=costs.margin_at_price(landed, bid) if bid > 0 else Decimal("0"),
        margin_expedited=costs.margin_at_price(expedite_landed, bid)
        if bid > 0
        else Decimal("0"),
        expedite_cost=Decimal("1100.00"),
        deposit_due=detail.po.deposit_due if detail.po else Decimal("0"),
        invoice_balance=balance,
        risks=[flag.message for flag in evaluate(detail)],
    )



