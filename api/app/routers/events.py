"""Event and flag route stubs (A03). Handlers land in A18/A19."""

from fastapi import APIRouter, HTTPException

from app.schemas import Event, Flag

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[Event])
def list_events() -> list[Event]:
    """List order events (stub until A18)."""
    raise HTTPException(status_code=501, detail="Not implemented until A18.")


@router.post("", response_model=Event)
def record_event() -> Event:
    """Record a voicemail/email/system event (stub until A18)."""
    raise HTTPException(status_code=501, detail="Not implemented until A18.")


@router.get("/flags", response_model=list[Flag])
def list_flags() -> list[Flag]:
    """List rule-engine flags (stub until A19)."""
    raise HTTPException(status_code=501, detail="Not implemented until A19.")
