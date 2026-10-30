"""Rules engine in code (A19): delivery slip, margin floor, cash exposure.

Every flag is computed from the stored records; no model call. A flag is
a finding a person must look at, never an action taken.
"""

from decimal import Decimal

from app.compare import MARGIN_FLOOR
from app.costs import margin_at_price
from app.order_store import get_detail, list_orders
from app.schemas import Flag, OrderDetail


def check_delivery(detail: OrderDetail) -> Flag | None:
    """A dated arrival past the customer date is a blocking slip."""
    due = detail.order.customer_due_date
    arrivals = [
        shipment.arrival_date
        for shipment in detail.shipments
        if shipment.arrival_date is not None
    ]
    if due is None or not arrivals:
        return None
    latest = max(arrivals)
    if latest <= due:
        return None
    late = (latest - due).days
    return Flag(
        flag_id=f"{detail.order.order_id}-delivery-slip",
        order_id=detail.order.order_id,
        code="delivery-slip",
        message=f"Arrival {latest.isoformat()} is {late} days late "
        f"(due {due.isoformat()}).",
        severity="blocking",
    )


def check_margin(detail: OrderDetail, floor: Decimal = MARGIN_FLOOR) -> Flag | None:
    """Margin below the floor at the bid price needs a person to look."""
    bid = detail.order.bid_price
    landed = detail.order.landed_cost
    if bid is None or landed is None:
        return None
    margin = margin_at_price(landed, bid)
    if margin >= floor * 100:
        return None
    return Flag(
        flag_id=f"{detail.order.order_id}-margin-floor",
        order_id=detail.order.order_id,
        code="margin-floor",
        message=f"Margin {margin}% at bid {bid} is below the {floor * 100:.0f}% floor.",
        severity="warning",
    )


def check_cash(detail: OrderDetail) -> Flag | None:
    """An outstanding PO deposit ties up cash before the customer pays."""
    po = detail.po
    if po is None or po.deposit_due <= 0 or po.status != "placed":
        return None
    return Flag(
        flag_id=f"{detail.order.order_id}-cash-exposure",
        order_id=detail.order.order_id,
        code="cash-exposure",
        message=f"Deposit {po.deposit_due} due with {po.po_id} before delivery.",
        severity="warning",
    )


def evaluate(detail: OrderDetail) -> list[Flag]:
    """All flags for one order."""
    return [
        flag
        for flag in (
            check_delivery(detail),
            check_margin(detail),
            check_cash(detail),
        )
        if flag is not None
    ]


def evaluate_all() -> list[Flag]:
    """Flags across every tracked order."""
    flags: list[Flag] = []
    for order in list_orders():
        detail = get_detail(order.order_id)
        if detail is not None:
            flags.extend(evaluate(detail))
    return flags
