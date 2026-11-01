"""Quote comparison for the screen (A13): records, checks and costs together.

Joins the curated quote fixtures with the A11 verdicts and the A12 cost
engine, plus the real award total the bid is measured against. Pure code;
no model call, so the screen recomputes margins live from these figures.
"""

import json
from decimal import Decimal
from typing import Any

from app.checks import demo_verdicts, load_quote_fixture
from app.config import REPO_ROOT
from app.costs import deposit_due, landed_cost, lowest_safe_bid, margin_at_price
from app.schemas import QuoteComparison

QUOTE_IDS = ("ninebark", "larkspur", "tallgrass")
MARGIN_FLOOR = Decimal("0.10")
AWARD_FILE = "data/awards/1232SA26Q0557.json"


def award_json() -> dict[str, Any]:
    """The real award record for the demo solicitation, as stored."""
    raw: dict[str, Any] = json.loads((REPO_ROOT / AWARD_FILE).read_text(encoding="utf-8"))
    return raw


def award_total() -> Decimal:
    """The real award total the bid is measured against."""
    return Decimal(award_json()["total_obligated"])


def deposit_fraction(quote_id: str) -> Decimal:
    """Deposit fraction from the quote fixture (0 for Net 30)."""
    raw = json.loads(
        (REPO_ROOT / "data" / "quotes" / f"{quote_id}.json").read_text(encoding="utf-8")
    )
    return Decimal(raw.get("deposit_fraction", "0"))


def build_comparison() -> list[QuoteComparison]:
    """One comparison row per demo quote, cheapest first."""
    award = award_total()
    verdicts = {verdict.quote_id: verdict for verdict in demo_verdicts()}
    rows = []
    for quote_id in QUOTE_IDS:
        quote = load_quote_fixture(quote_id)
        landed = landed_cost(quote)
        per_unit, safe_total = lowest_safe_bid(quote, MARGIN_FLOOR)
        rows.append(
            QuoteComparison(
                quote=quote,
                verdict=verdicts[quote_id],
                landed_cost=landed,
                margin_at_award=margin_at_price(landed, award),
                safe_bid_per_unit=per_unit,
                safe_bid_total=safe_total,
                deposit_due=deposit_due(quote.total, deposit_fraction(quote_id)),
                award_total=award,
            )
        )
    rows.sort(key=lambda row: row.quote.total)
    return rows
