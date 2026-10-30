"""Quote route stubs (A03). Handlers land in A09/A10."""

from fastapi import APIRouter, HTTPException

from app.schemas import Quote

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("", response_model=list[Quote])
def list_quotes() -> list[Quote]:
    """List ingested supplier quotes (stub until A10)."""
    raise HTTPException(status_code=501, detail="Not implemented until A10.")


@router.get("/{quote_id}", response_model=Quote)
def get_quote(quote_id: str) -> Quote:
    """One supplier quote with checks (stub until A10)."""
    raise HTTPException(status_code=501, detail=f"Not implemented until A10: {quote_id}.")


@router.post("/extract", response_model=Quote)
def extract_quote() -> Quote:
    """Run multimodal quote intake over PDF, photo and email image (stub until A10)."""
    raise HTTPException(status_code=501, detail="Not implemented until A10.")
