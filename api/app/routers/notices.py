"""Triage routes (A34/A35): stored notices with code-scored fit."""

from fastapi import APIRouter, HTTPException

from app import fit, score
from app.schemas import FitAssessment, Notice

router = APIRouter(prefix="/notices", tags=["notices"])


@router.get("", response_model=list[Notice])
def list_notices() -> list[Notice]:
    """List the triage batch (empty until the H16 batch lands)."""
    return [fit.load_notice(notice_id) for notice_id in fit.list_notice_ids()]


@router.get("/{notice_id}", response_model=Notice)
def get_notice(notice_id: str) -> Notice:
    """One notice with extracted fit facts (A34)."""
    try:
        return fit.load_notice(notice_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{notice_id}/fit", response_model=FitAssessment)
def get_fit(notice_id: str) -> FitAssessment:
    """Pursue-or-pass scoring against the company profile (A35)."""
    try:
        notice = fit.load_notice(notice_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        profile = score.load_profile()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return score.score_notice(notice, profile)
