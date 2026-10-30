"""Recommendation tests (A14): pursue at the safe bid, or pass."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.compare import build_comparison
from app.main import app
from app.recommend import current_decision, read_award, recommend

client = TestClient(app)


def test_demo_recommends_pursue_at_tallgrass_safe_bid() -> None:
    """Tallgrass at $91,189.92, with the sourcing confirmation flagged."""
    decision = current_decision()
    assert decision.decision == "pursue"
    assert decision.bid_price == Decimal("91189.92")
    assert decision.supplier == "Tallgrass Horticultural Supply"
    assert decision.award_total == Decimal("91880.12")
    assert any("confirm" in reason.lower() for reason in decision.reasons)


def test_pass_when_no_quote_is_compliant() -> None:
    """All-fail verdicts yield pass, never a price."""
    rows = build_comparison()
    for row in rows:
        for check in row.verdict.checks:
            check.verdict = "fail"
        row.verdict.overall = "fail"
    decision = recommend(rows, read_award())
    assert decision.decision == "pass"
    assert decision.bid_price is None
    assert decision.supplier is None
    assert any("No compliant quote" in reason for reason in decision.reasons)


def test_award_record_reads_data_awards() -> None:
    """Total, date and offers received come from the award file."""
    award = read_award()
    assert award.total == Decimal("91880.12")
    assert award.date_signed.isoformat() == "2026-09-30"
    assert award.number_of_offers == 26


def test_http_award_serves_total_date_and_offers() -> None:
    """The award reveal carries total, date and offers received."""
    response = client.get("/sourcing-decisions/award")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == "91880.12"
    assert body["date_signed"] == "2026-09-30"
    assert body["number_of_offers"] == 26


def test_http_decisions_serve_recommendation() -> None:
    """GET serves the recommendation; POST computes the same one."""
    response = client.get("/sourcing-decisions")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["decision"] == "pursue"
    assert body[0]["bid_price"] == "91189.92"
    response = client.post("/sourcing-decisions")
    assert response.status_code == 200
    assert response.json()["supplier"] == "Tallgrass Horticultural Supply"
