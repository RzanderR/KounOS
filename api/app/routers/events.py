"""Event and flag routes (A18/A19)."""

from fastapi import APIRouter, HTTPException

from app import order_store
from app.rules import evaluate_all
from app.schemas import Event, Flag

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[Event])
def list_events() -> list[Event]:
    """Events across every tracked order (none seeded; A18 records them)."""
    events: list[Event] = []
    for order in order_store.list_orders():
        detail = order_store.get_detail(order.order_id)
        if detail is not None:
            events.extend(detail.events)
    return events


@router.post("", response_model=Event)
def record_event() -> Event:
    """Record a voicemail/email/system event (stub until A18)."""
    raise HTTPException(status_code=501, detail="Not implemented until A18.")


@router.get("/flags", response_model=list[Flag])
def list_flags() -> list[Flag]:
    """Rule-engine flags across every tracked order (A19)."""
    return evaluate_all()
