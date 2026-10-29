"""Triage route stubs (A03). Handlers land in A34/A35."""

from fastapi import APIRouter, HTTPException

from app.schemas import FitAssessment, Notice

router = APIRouter(prefix="/notices", tags=["notices"])


@router.get("", response_model=list[Notice])
def list_notices() -> list[Notice]:
    """List the triage batch (stub until A34)."""
    raise HTTPException(status_code=501, detail="Not implemented until A34.")


@router.get("/{notice_id}", response_model=Notice)
def get_notice(notice_id: str) -> Notice:
    """One notice with extracted fit facts (stub until A34)."""
    raise HTTPException(status_code=501, detail=f"Not implemented until A34: {notice_id}.")


@router.get("/{notice_id}/fit", response_model=FitAssessment)
def get_fit(notice_id: str) -> FitAssessment:
    """Pursue-or-pass scoring against the company profile (stub until A35)."""
    raise HTTPException(status_code=501, detail=f"Not implemented until A35: {notice_id}.")
