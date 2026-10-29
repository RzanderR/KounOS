"""Quote comparison endpoint tests (A13): records, checks, costs, award."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.compare import award_total, build_comparison
from app.main import app

client = TestClient(app)


def test_comparison_rows_cheapest_first_with_verdicts() -> None:
    """Three rows ordered by quote total, each with checks and costs."""
    rows = build_comparison()
    assert [row.quote.quote_id for row in rows] == ["larkspur", "ninebark", "tallgrass"]
    assert [row.verdict.overall for row in rows] == ["fail", "fail", "needs_confirmation"]
    tallgrass = rows[2]
    assert tallgrass.landed_cost == Decimal("82070.00")
    assert tallgrass.margin_at_award == Decimal("10.68")
    assert tallgrass.safe_bid_total == Decimal("91189.92")
    assert tallgrass.deposit_due == Decimal("41035.00")
    assert tallgrass.award_total == Decimal("91880.12")


def test_award_total_is_the_real_obligation() -> None:
    """The measuring stick is the obligated $91,880.12."""
    assert award_total() == Decimal("91880.12")


def test_http_comparison_and_quote_routes() -> None:
    """GET /quotes serves three records; /comparison serves rows; unknown 404s."""
    response = client.get("/quotes")
    assert response.status_code == 200
    assert len(response.json()) == 3
    response = client.get("/quotes/comparison")
    assert response.status_code == 200
    body = response.json()
    assert [row["quote"]["quote_id"] for row in body] == ["larkspur", "ninebark", "tallgrass"]
    assert client.get("/quotes/unknown").status_code == 404
    assert client.get("/quotes/tallgrass").status_code == 200
