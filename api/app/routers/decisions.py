"""Sourcing-decision routes (A14): pursue-at-price or pass, computed in code."""

from fastapi import APIRouter

from app.recommend import current_decision, read_award
from app.schemas import AwardRecord, SourcingDecision

router = APIRouter(prefix="/sourcing-decisions", tags=["sourcing-decisions"])


@router.get("/award", response_model=AwardRecord)
def get_award() -> AwardRecord:
    """The actual award the recommendation is measured against (A14)."""
    return read_award()


@router.get("", response_model=list[SourcingDecision])
def list_decisions() -> list[SourcingDecision]:
    """The current bid recommendation (A14)."""
    return [current_decision()]


@router.post("", response_model=SourcingDecision)
def make_decision() -> SourcingDecision:
    """Recompute the bid recommendation (A14)."""
    return current_decision()
