"""Order and demo-reset routes (A16/A17)."""

from fastapi import APIRouter, HTTPException

from app import order_store
from app.schemas import Order, OrderDetail

router = APIRouter(prefix="/orders", tags=["orders"])
demo_router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("", response_model=list[Order])
def list_orders() -> list[Order]:
    """All tracked orders under the simulated award (A16)."""
    return order_store.list_orders()


@router.get("/{order_id}", response_model=OrderDetail)
def get_order(order_id: str) -> OrderDetail:
    """One order with its PO, shipments, invoices and events (A17)."""
    detail = order_store.get_detail(order_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Unknown order: {order_id}.")
    return detail


@demo_router.post("/reset")
def reset_demo() -> dict[str, int]:
    """Restore the exact seeded state (A16)."""
    return {"orders": order_store.reset()}
