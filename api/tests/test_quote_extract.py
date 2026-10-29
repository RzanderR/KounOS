"""Quote extraction contract tests (A10): schema shape and money parsing."""

from decimal import Decimal, InvalidOperation

import pytest
from pydantic import ValidationError

from app.quote_extract import (
    QUOTE_SCHEMA,
    QuoteExtraction,
    parse_money,
    to_quote_record,
)


def valid_payload() -> dict[str, object]:
    """Minimal Tallgrass-shaped payload (correct part, deposit terms aside)."""
    return {
        "supplier": "Tallgrass Horticultural Supply",
        "quote_number": "THS-2026-1487",
        "quote_date": "2026-06-04",
        "lines": [
            {
                "part": "PTB8850LS41",
                "description": "PHOTOBIO CX 2125 LED, 850W",
                "quantity": 58,
                "unit": "EA",
                "unit_price": "695.00",
                "extended": "40310.00",
            }
        ],
        "freight": {"value": "1450.00", "snippet": "freight to Fargo ND 1450.00"},
        "quote_total": {"value": "82070.00", "snippet": "quote total 82070.00 due net 30"},
        "lead_time_text": "3-4 weeks ARO",
        "lead_time_days_max": 28,
        "payment_terms": "Net 30",
        "country_of_origin": "not stated",
    }


def test_top_level_required_covers_every_property() -> None:
    """Strict-mode APIs reject the schema unless required lists every property."""
    props = QUOTE_SCHEMA["properties"]
    assert isinstance(props, dict)
    required = QUOTE_SCHEMA["required"]
    assert isinstance(required, list)
    assert set(required) == set(props)


def test_valid_payload_converts_to_quote_record() -> None:
    """Extraction converts to a Quote with Decimal money."""
    record = to_quote_record(
        QuoteExtraction.model_validate(valid_payload()), "tallgrass", "1232SA26Q0557"
    )
    assert record.supplier == "Tallgrass Horticultural Supply"
    assert record.total == Decimal("82070.00")
    assert record.freight == Decimal("1450.00")
    assert record.lines[0].part == "PTB8850LS41"
    assert record.lead_time_days_max == 28


def test_missing_country_is_rejected() -> None:
    """Output without the country field is rejected, not stored."""
    payload = valid_payload()
    assert isinstance(payload, dict)
    del payload["country_of_origin"]
    with pytest.raises(ValidationError):
        QuoteExtraction.model_validate(payload)


def test_parse_money_rejects_formatted_amounts() -> None:
    """Money with signs or commas is rejected; code owns the arithmetic."""
    assert parse_money("668.00") == Decimal("668.00")
    with pytest.raises(InvalidOperation):
        parse_money("$668.00")
    with pytest.raises(InvalidOperation):
        parse_money("79,348.00")
