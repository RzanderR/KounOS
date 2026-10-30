"""Requirement-check tests (A11): the D03 verdicts, computed in code."""

import pytest

from app.checks import (
    check_quote,
    demo_spec,
    demo_verdicts,
    load_quote_fixture,
    parse_delivery_days,
    parse_far_number,
)
from app.schemas import Quote


def test_demo_verdicts_match_d03() -> None:
    """Ninebark fails delivery, Larkspur fails spec, Tallgrass passes spec.

    Sourcing needs confirmation on all three: no quote states a country
    of origin, and a missing origin is never a pass.
    """
    verdicts = {verdict.quote_id: verdict for verdict in demo_verdicts()}
    ninebark = verdicts["ninebark"]
    assert ninebark.checks[0].verdict == "fail"  # 98 days vs 60
    assert ninebark.overall == "fail"
    larkspur = verdicts["larkspur"]
    spec = [check for check in larkspur.checks if check.check == "spec"][0]
    assert spec.verdict == "fail"  # PTB8850LS42, brand name only
    assert "PTB8850LS42" in spec.reason
    assert larkspur.overall == "fail"
    tallgrass = verdicts["tallgrass"]
    by_name = {check.check: check.verdict for check in tallgrass.checks}
    assert by_name == {
        "delivery": "pass",
        "spec": "pass",
        "sourcing": "needs_confirmation",
    }
    assert tallgrass.overall == "needs_confirmation"


def test_delivery_boundary() -> None:
    """Exactly the limit passes; one day over fails."""
    quote = load_quote_fixture("tallgrass")
    quote.lead_time_days_max = 60
    assert check_quote("t", quote, demo_spec()).checks[0].verdict == "pass"
    quote.lead_time_days_max = 61
    assert check_quote("t", quote, demo_spec()).checks[0].verdict == "fail"


def test_missing_lead_time_needs_confirmation() -> None:
    """No lead time is a question for a person, not a pass."""
    quote = load_quote_fixture("tallgrass")
    quote.lead_time_days_max = None
    verdict = check_quote("t", quote, demo_spec())
    assert verdict.checks[0].verdict == "needs_confirmation"


def test_domestic_origin_passes_and_foreign_fails() -> None:
    """A stated origin decides sourcing; an absent one never passes."""
    quote = load_quote_fixture("tallgrass")
    assert isinstance(quote, Quote)
    quote.country_of_origin = "USA"
    assert check_quote("t", quote, demo_spec()).checks[2].verdict == "pass"
    quote.country_of_origin = "China"
    assert check_quote("t", quote, demo_spec()).checks[2].verdict == "fail"


def test_delivery_term_and_far_number_parse() -> None:
    """The served wording parses to the D03 parameters."""
    assert parse_delivery_days(
        "The USDA requires delivery of all items within 60 days after award."
    ) == 60
    assert (
        parse_far_number("FAR 52.225-3 Buy American applies, with the certificate")
        == "52.225-3"
    )
    with pytest.raises(ValueError):
        parse_delivery_days("delivery TBD")
    with pytest.raises(ValueError):
        parse_far_number("no clause number here")
