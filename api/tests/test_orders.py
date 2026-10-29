"""Seeded-order tests (A16): five orders, exact reset, detail links."""

from fastapi.testclient import TestClient

from app.main import app
from app.order_store import get_detail, list_orders, reset

client = TestClient(app)


def test_seed_holds_five_orders_with_rescaled_dates() -> None:
    """The simulated award plus four background orders (D03 rescale)."""
    assert reset() == 5
    ids = [order.order_id for order in list_orders()]
    assert ids == ["ORD-001", "ORD-002", "ORD-003", "ORD-004", "ORD-005"]
    main = get_detail("ORD-001")
    assert main is not None
    assert main.order.customer_due_date is not None
    assert main.order.customer_due_date.isoformat() == "2027-01-01"
    assert main.po is not None and main.po.po_id == "PO-001"
    assert len(main.shipments) == 1
    assert len(main.invoices) == 1


def test_reset_restores_exact_state() -> None:
    """Mutations vanish on reset; the seed file is the source of truth."""
    detail = get_detail("ORD-001")
    assert detail is not None
    detail.order.notes.append("temporary mutation")
    assert reset() == 5
    fresh = get_detail("ORD-001")
    assert fresh is not None
    assert fresh.order.notes == [
        "Simulated award: 116 LED fixtures, Tallgrass at the $91,189.92 safe bid."
    ]


def test_http_orders_and_reset() -> None:
    """GET serves orders and detail; POST /demo/reset restores five."""
    assert len(client.get("/orders").json()) == 5
    body = client.get("/orders/ORD-001").json()
    assert body["order"]["supplier"] == "Tallgrass Horticultural Supply"
    assert body["po"]["po_id"] == "PO-001"
    assert client.get("/orders/unknown").status_code == 404
    assert client.post("/demo/reset").json() == {"orders": 5}
