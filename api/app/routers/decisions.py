"""Sourcing-decision route stubs (A03). Handlers land in A13/A14."""

from fastapi import APIRouter, HTTPException

from app.schemas import SourcingDecision

router = APIRouter(prefix="/sourcing-decisions", tags=["sourcing-decisions"])


@router.get("", response_model=list[SourcingDecision])
def list_decisions() -> list[SourcingDecision]:
    """List sourcing decisions (stub until A14)."""
    raise HTTPException(status_code=501, detail="Not implemented until A14.")


@router.post("", response_model=SourcingDecision)
def make_decision() -> SourcingDecision:
    """Recommend pursue-at-price or pass, computed in code (stub until A14)."""
    raise HTTPException(status_code=501, detail="Not implemented until A14.")
