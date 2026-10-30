"""Seeded order store (A16): versioned JSON seed, in-memory runtime state.

``POST /demo/reset`` reloads the seed file, so the demo always returns
to the exact seeded state. No database: five orders fit in memory, and
the seed file is the visible source of truth.
"""

import json
from datetime import date, datetime
from decimal import Decimal

from app.config import REPO_ROOT
from app.schemas import Event, Invoice, Order, OrderDetail, Shipment, SupplierPO

SEED_PATH = REPO_ROOT / "data" / "orders" / "seed.json"


def _parse_date(raw: str | None) -> date | None:
    return date.fromisoformat(raw) if raw else None


def _parse_datetime(raw: str | None) -> datetime | None:
    return datetime.fromisoformat(raw) if raw else None


def load_seed() -> dict[str, OrderDetail]:
    """Load every seeded order with its linked records."""
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    details: dict[str, OrderDetail] = {}
    for item in raw["orders"]:
        po_raw = item.get("po")
        details[item["order_id"]] = OrderDetail(
            order=Order(
                order_id=item["order_id"],
                solicitation_id=item["solicitation_id"],
                supplier=item["supplier"],
                status=item["status"],
                customer_due_date=_parse_date(item.get("customer_due_date")),
                supplier_ship_date=_parse_date(item.get("supplier_ship_date")),
                bid_price=Decimal(item["bid_price"]) if item.get("bid_price") else None,
                landed_cost=Decimal(item["landed_cost"]) if item.get("landed_cost") else None,
                notes=item.get("notes", []),
            ),
            po=SupplierPO(
                po_id=po_raw["po_id"],
                order_id=po_raw["order_id"],
                supplier=po_raw["supplier"],
                amount=Decimal(po_raw["amount"]),
                deposit_due=Decimal(po_raw.get("deposit_due", "0")),
                status=po_raw["status"],
            )
            if po_raw
            else None,
            shipments=[
                Shipment(
                    shipment_id=entry["shipment_id"],
                    order_id=entry["order_id"],
                    ship_date=_parse_date(entry.get("ship_date")),
                    arrival_date=_parse_date(entry.get("arrival_date")),
                    carrier=entry.get("carrier"),
                )
                for entry in item.get("shipments", [])
            ],
            invoices=[
                Invoice(
                    invoice_id=entry["invoice_id"],
                    order_id=entry["order_id"],
                    amount=Decimal(entry["amount"]),
                    due_date=_parse_date(entry.get("due_date")),
                    paid=entry.get("paid", False),
                )
                for entry in item.get("invoices", [])
            ],
            events=[
                Event(
                    event_id=entry["event_id"],
                    order_id=entry["order_id"],
                    source=entry["source"],
                    summary=entry["summary"],
                    supplier=entry.get("supplier"),
                    new_ship_date=_parse_date(entry.get("new_ship_date")),
                    confidence=entry.get("confidence"),
                    received_at=_parse_datetime(entry.get("received_at")),
                )
                for entry in item.get("events", [])
            ],
        )
    return details


_STORE: dict[str, OrderDetail] = load_seed()


def reset() -> int:
    """Reload the seed file; returns the restored order count."""
    global _STORE
    _STORE = load_seed()
    return len(_STORE)


def list_orders() -> list[Order]:
    """All tracked orders."""
    return [detail.order for detail in _STORE.values()]


def get_detail(order_id: str) -> OrderDetail | None:
    """One order with its linked records, or None."""
    return _STORE.get(order_id)
