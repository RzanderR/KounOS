"""Event routes (A18): voicemail/email intake plus stored events and flags."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import order_store
from app.config import ModelKeyMissing, Settings, get_settings
from app.rules import evaluate_all
from app.schemas import Event, Flag
from app.voicemail import ingest_file

router = APIRouter(prefix="/events", tags=["events"])


class IngestBody(BaseModel):
    """One delay message to ingest from data/voicemail/."""

    order_id: str
    source: Literal["voicemail", "email"]
    filename: str


@router.get("", response_model=list[Event])
def list_events() -> list[Event]:
    """Events across every tracked order (A18 records them)."""
    events: list[Event] = []
    for order in order_store.list_orders():
        detail = order_store.get_detail(order.order_id)
        if detail is not None:
            events.extend(detail.events)
    return events


@router.post("/ingest", response_model=Event)
def ingest_event(body: IngestBody, settings: Settings = Depends(get_settings)) -> Event:
    """Ingest one voicemail or backup email into an order event (A18)."""
    detail = order_store.get_detail(body.order_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Unknown order: {body.order_id}.")
    try:
        return ingest_file(body.order_id, body.source, body.filename, settings, detail)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModelKeyMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/flags", response_model=list[Flag])
def list_flags() -> list[Flag]:
    """Rule-engine flags across every tracked order (A19)."""
    return evaluate_all()
