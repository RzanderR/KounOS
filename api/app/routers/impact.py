"""Impact routes (A21): priced delay analysis for one order."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import impact, replay
from app.config import Settings, get_settings
from app.schemas import ImpactAnalysis

router = APIRouter(prefix="/impact", tags=["impact"])


class AnalyzeBody(BaseModel):
    """The order to analyze."""

    order_id: str


@router.post("/analyze", response_model=ImpactAnalysis)
def analyze_impact(
    body: AnalyzeBody, settings: Settings = Depends(get_settings)
) -> ImpactAnalysis:
    """Price the recovery options in code, have the model explain them."""
    try:
        return impact.analyze(body.order_id, settings)
    except impact.NoDelay as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except replay.NoReplay as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
