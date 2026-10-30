"""Order and demo-reset routes (A16/A17)."""

from fastapi import APIRouter, Depends, HTTPException

from app import lineage, order_store
from app.config import Settings, get_settings
from app.schemas import ContractFile, Order, OrderDetail

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


@router.get("/{order_id}/contract-file", response_model=ContractFile)
def get_contract_file(
    order_id: str, settings: Settings = Depends(get_settings)
) -> ContractFile:
    """The whole linked picture for one order with per-figure lineage (A37)."""
    try:
        return lineage.build_contract_file(order_id, settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@demo_router.post("/reset")
def reset_demo() -> dict[str, int]:
    """Restore the exact seeded state (A16)."""
    return {"orders": order_store.reset()}
