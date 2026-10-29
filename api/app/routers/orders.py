"""Order and demo-reset route stubs (A03). Handlers land in A16/A17."""

from fastapi import APIRouter, HTTPException

from app.schemas import Order

router = APIRouter(prefix="/orders", tags=["orders"])
demo_router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("", response_model=list[Order])
def list_orders() -> list[Order]:
    """List tracked orders (stub until A16)."""
    raise HTTPException(status_code=501, detail="Not implemented until A16.")


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    """One order with its timeline (stub until A17)."""
    raise HTTPException(status_code=501, detail=f"Not implemented until A17: {order_id}.")


@demo_router.post("/reset")
def reset_demo() -> None:
    """Restore the exact seeded state (stub until A16)."""
    raise HTTPException(status_code=501, detail="Not implemented until A16.")
