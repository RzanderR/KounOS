"""Cost-engine tests (A12): the demo vectors, reproduced to the cent."""

import json
from decimal import Decimal

import pytest

from app.checks import load_quote_fixture
from app.config import REPO_ROOT
from app.costs import (
    cash_exposure,
    deposit_due,
    landed_cost,
    landed_per_unit,
    lowest_safe_bid,
    margin_at_price,
)

AWARD = Decimal("91880.12")
MARGIN_FLOOR = Decimal("0.10")


def fixture_expected(quote_id: str) -> dict[str, str]:
    """The expected KounOS results stored with each quote fixture."""
    raw = json.loads(
        (REPO_ROOT / "data" / "quotes" / f"{quote_id}.json").read_text(encoding="utf-8")
    )
    return raw["expected_kounos_results"]


@pytest.mark.parametrize(
    "quote_id, landed",
    [("ninebark", "79348.00"), ("larkspur", "78764.00"), ("tallgrass", "82070.00")],
)
def test_landed_costs_match_fixtures(quote_id: str, landed: str) -> None:
    """Landed costs: $79,348 / $78,764 / $82,070."""
    quote = load_quote_fixture(quote_id)
    assert landed_cost(quote) == Decimal(landed)
    assert cash_exposure(quote) == Decimal(landed)
    assert fixture_expected(quote_id)["landed_cost"] == landed


@pytest.mark.parametrize(
    "quote_id, margin",
    [("ninebark", "13.64"), ("larkspur", "14.28"), ("tallgrass", "10.68")],
)
def test_margins_at_award_match_fixtures(quote_id: str, margin: str) -> None:
    """Margins 13.6% / 14.3% / 10.7% at the $91,880.12 award."""
    quote = load_quote_fixture(quote_id)
    assert margin_at_price(landed_cost(quote), AWARD) == Decimal(margin)
    assert fixture_expected(quote_id)["margin_at_actual_award_price"] == f"{margin}%"
    assert landed_per_unit(quote) == Decimal(
        fixture_expected(quote_id)["landed_cost_per_unit"]
    )


def test_lowest_safe_bid_matches_fixture() -> None:
    """Lowest safe bid $91,189.92 for $82,070 at 10% (Tallgrass)."""
    quote = load_quote_fixture("tallgrass")
    per_unit, total = lowest_safe_bid(quote, MARGIN_FLOOR)
    assert per_unit == Decimal("786.12")
    assert total == Decimal("91189.92")
    expected = fixture_expected("tallgrass")
    assert expected["lowest_safe_bid_per_unit_at_10pct"] == "786.12"
    assert expected["lowest_safe_bid_total_at_10pct"] == "91189.92"


def test_deposit_only_where_quoted() -> None:
    """Tallgrass takes 50% with the PO; the others are Net 30."""
    assert deposit_due(Decimal("82070.00"), Decimal("0.5")) == Decimal("41035.00")
    assert deposit_due(Decimal("79348.00"), Decimal("0")) == Decimal("0.00")
    assert fixture_expected("tallgrass")["deposit_due_with_po"] == "41035.00"


def test_safe_bid_rounds_up_to_protect_the_floor() -> None:
    """The safe per-unit price never rounds down past the margin floor."""
    per_unit, _ = lowest_safe_bid(load_quote_fixture("tallgrass"), MARGIN_FLOOR)
    assert margin_at_price(Decimal("707.50"), per_unit) >= Decimal("10.00")


def test_invalid_inputs_fail_closed() -> None:
    """Zero prices, wild margins and fractions raise instead of pricing."""
    with pytest.raises(ValueError):
        margin_at_price(Decimal("82070.00"), Decimal("0"))
    with pytest.raises(ValueError):
        lowest_safe_bid(load_quote_fixture("tallgrass"), Decimal("1"))
    with pytest.raises(ValueError):
        deposit_due(Decimal("82070.00"), Decimal("1.5"))
