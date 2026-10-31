"""Quote routes: the curated demo quotes and their comparison (A10/A13)."""

from fastapi import APIRouter, HTTPException

from app.checks import load_quote_fixture
from app.compare import QUOTE_IDS, build_comparison
from app.schemas import Quote, QuoteComparison

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("", response_model=list[Quote])
def list_quotes() -> list[Quote]:
    """The three curated demo quote records (A10)."""
    return [load_quote_fixture(quote_id) for quote_id in QUOTE_IDS]


@router.get("/comparison", response_model=list[QuoteComparison])
def get_comparison() -> list[QuoteComparison]:
    """Each quote with its checks and code-computed costs (A13)."""
    return build_comparison()


@router.get("/{quote_id}", response_model=Quote)
def get_quote(quote_id: str) -> Quote:
    """One supplier quote record; unknown ids 404."""
    if quote_id not in QUOTE_IDS:
        raise HTTPException(status_code=404, detail=f"Unknown quote: {quote_id}.")
    return load_quote_fixture(quote_id)
