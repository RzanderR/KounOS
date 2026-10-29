"""Schema contract tests (A03): demo values validate, bad payloads don't."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import (
    AwardRecord,
    Event,
    FitAssessment,
    KeyClause,
    Quote,
    Requirement,
    Solicitation,
    SourceRef,
    SourcingDecision,
)


def test_award_record_matches_demo_award() -> None:
    """The real award 1232SA26P0357 validates against AwardRecord."""
    award = AwardRecord(
        solicitation_id="1232SA26Q0557",
        award_id="1232SA26P0357",
        awardee="MORGAN INGLAND LLC",
        date_signed=date(2026, 9, 30),
        total=Decimal("91880.12"),
        number_of_offers=26,
        source_url="https://www.usaspending.gov/award/CONT_AWD_1232SA26P0357_12K3_-NONE-_-NONE-",
    )
    assert award.total == Decimal("91880.12")
    assert award.number_of_offers == 26


def test_quote_matches_ninebark_demo_values() -> None:
    """Ninebark's fictional quote validates; money stays Decimal."""
    quote = Quote(
        supplier="Ninebark Lighting Supply",
        solicitation_id="1232SA26Q0557",
        freight=Decimal("1860.00"),
        total=Decimal("79348.00"),
        lead_time_days_max=98,
    )
    assert quote.total == Decimal("79348.00")
    assert quote.status == "needs_review"


def test_solicitation_carries_cited_requirements() -> None:
    """Requirements and key clauses keep their page citations."""
    ref = SourceRef(
        file="1232SA26Q0557_terms_and_clauses.pdf",
        page=12,
        snippet="The USDA requires delivery of all items within 60 days after award.",
    )
    solicitation = Solicitation(
        solicitation_id="1232SA26Q0557",
        title="Greenhouse light fixtures",
        agency="U.S. Department of Agriculture",
        requirements=[
            Requirement(
                line="0001", description="LED greenhouse light fixtures", quantity=58, unit="EA"
            )
        ],
        key_clauses=[
            KeyClause(name="delivery", summary="All items within 60 days after award", source=ref)
        ],
    )
    assert solicitation.key_clauses[0].source.page == 12


def test_recommendation_pass_needs_no_supplier() -> None:
    """A pass decision carries reasons and no bid price."""
    decision = SourcingDecision(
        solicitation_id="1232SA26Q0557",
        decision="pass",
        reasons=["No compliant quote: every offer misses delivery or spec."],
        award_total=Decimal("91880.12"),
    )
    assert decision.bid_price is None
    assert decision.reasons


def test_fit_assessment_labels_its_model() -> None:
    """Every AI verdict names the model that produced it."""
    fit = FitAssessment(
        notice_id="1232SA26Q0557",
        verdict="pursue",
        reasons=["set_aside: pass - total small business set-aside matches."],
        model="muse-spark-1.3",
    )
    assert fit.model == "muse-spark-1.3"


def test_event_rejects_confidence_outside_zero_to_one() -> None:
    """Confidence outside [0, 1] fails validation instead of storing."""
    with pytest.raises(ValidationError):
        Event(
            event_id="e1",
            order_id="o1",
            source="voicemail",
            summary="Slip asserted with impossible confidence.",
            confidence=1.5,
        )


def test_award_missing_total_is_rejected() -> None:
    """An award without a total is rejected, not stored."""
    with pytest.raises(ValidationError):
        AwardRecord(
            solicitation_id="1232SA26Q0557",  # type: ignore[call-arg]
            award_id="1232SA26P0357",
            awardee="MORGAN INGLAND LLC",
            date_signed=date(2026, 9, 30),
            number_of_offers=26,
        )
