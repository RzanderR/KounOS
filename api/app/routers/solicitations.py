"""Solicitation route stubs (A03). Handlers land in A05/A07/A08."""

from fastapi import APIRouter, HTTPException

from app.schemas import Solicitation

router = APIRouter(prefix="/solicitations", tags=["solicitations"])


@router.get("", response_model=list[Solicitation])
def list_solicitations() -> list[Solicitation]:
    """List ingested solicitations (stub until A05)."""
    raise HTTPException(status_code=501, detail="Not implemented until A05.")


@router.get("/{solicitation_id}", response_model=Solicitation)
def get_solicitation(solicitation_id: str) -> Solicitation:
    """One solicitation with requirements and citations (stub until A08)."""
    raise HTTPException(
        status_code=501,
        detail=f"Not implemented until A08: {solicitation_id}.",
    )


@router.post("/{solicitation_id}/extract", response_model=Solicitation)
def extract_solicitation(solicitation_id: str) -> Solicitation:
    """Run MODEL_READ extraction over the solicitation PDFs (stub until A05)."""
    raise HTTPException(
        status_code=501,
        detail=f"Not implemented until A05: {solicitation_id}.",
    )


@router.post("/{solicitation_id}/gap-pass")
def gap_pass(solicitation_id: str) -> None:
    """Run the gap and ambiguity pass (stub until A07)."""
    raise HTTPException(
        status_code=501,
        detail=f"Not implemented until A07: {solicitation_id}.",
    )
