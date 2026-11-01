"""Bid recommendation and award reveal (A14), computed in code.

Pursue at the lowest safe bid with the cheapest eligible supplier, or
pass with reasons when no quote is compliant. A quote counts as eligible
when no check fails; a ``needs_confirmation`` sourcing check rides along
as an explicit reason, never a silent pass. The actual award is read
from ``data/awards/`` for the side-by-side reveal.
"""

from datetime import date
from decimal import Decimal

from app.compare import MARGIN_FLOOR, award_json, build_comparison
from app.schemas import AwardRecord, QuoteComparison, SourcingDecision

SOLICITATION_ID = "1232SA26Q0557"


def read_award() -> AwardRecord:
    """The real award record for the demo solicitation."""
    raw = award_json()
    return AwardRecord(
        solicitation_id=raw["solicitation_id"],
        award_id=raw["award_id"],
        awardee=raw["awardee"],
        date_signed=date.fromisoformat(raw["date_signed"]),
        total=Decimal(raw["total_obligated"]),
        number_of_offers=raw["number_of_offers_received"],
        source_url=raw["usaspending_url"],
    )


def recommend(
    rows: list[QuoteComparison], award: AwardRecord, floor: Decimal = MARGIN_FLOOR
) -> SourcingDecision:
    """Pursue at the lowest safe bid, or pass because nothing is compliant."""
    eligible = [row for row in rows if row.verdict.overall != "fail"]
    if not eligible:
        return SourcingDecision(
            solicitation_id=SOLICITATION_ID,
            decision="pass",
            reasons=["No compliant quote: every supplier fails a requirement."],
            award_total=award.total,
        )
    best = min(eligible, key=lambda row: row.safe_bid_total)
    standing = (
        "passes every requirement check"
        if best.verdict.overall == "pass"
        else "fails no requirement check but has open items"
    )
    reasons = [
        f"{best.quote.supplier} {standing}; lowest safe bid "
        f"{best.safe_bid_total} with a {floor * 100:.0f}% margin floor."
    ]
    if best.verdict.overall == "needs_confirmation":
        pending = [
            check.reason
            for check in best.verdict.checks
            if check.verdict == "needs_confirmation"
        ]
        reasons.extend(pending)
        reasons.append("A person confirms the open items before bidding.")
    return SourcingDecision(
        solicitation_id=SOLICITATION_ID,
        decision="pursue",
        bid_price=best.safe_bid_total,
        supplier=best.quote.supplier,
        reasons=reasons,
        award_total=award.total,
    )


def current_decision() -> SourcingDecision:
    """The demo recommendation over the live comparison rows."""
    return recommend(build_comparison(), read_award())
