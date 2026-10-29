"""Extraction contract tests (A05): schema shape and rejection of bad output."""

import pytest
from pydantic import ValidationError

from app.extract import (
    EXTRACTION_SCHEMA,
    CitedField,
    SolicitationExtraction,
)


def cited(value: str = "58", page: int = 1, snippet: str = "Quantity: 58") -> CitedField:
    """One well-formed cited field."""
    return CitedField(value=value, page=page, snippet=snippet)


def valid_payload() -> dict[str, object]:
    """Minimal payload with both demo line items (0001 base, 1001 option)."""
    line = {
        "line": {"value": "0001", "page": 1, "snippet": "CLIN 0001"},
        "description": {"value": "LED greenhouse light fixtures", "page": 1, "snippet": "LED"},
        "part_or_nsn": {"value": "PTB8850LS41", "page": 1, "snippet": "PTB8850LS41"},
        "quantity": {"value": "58", "page": 1, "snippet": "Quantity: 58"},
        "unit": {"value": "EA", "page": 1, "snippet": "EA"},
    }
    option = {
        "line": {"value": "1001", "page": 1, "snippet": "CLIN 1001"},
        "description": {
            "value": "LED greenhouse light fixtures (option)",
            "page": 1,
            "snippet": "LED",
        },
        "part_or_nsn": {"value": "PTB8850LS41", "page": 1, "snippet": "PTB8850LS41"},
        "quantity": {"value": "58", "page": 1, "snippet": "Quantity: 58"},
        "unit": {"value": "EA", "page": 1, "snippet": "EA"},
    }
    return {
        "solicitation_id": {"value": "1232SA26Q0557", "page": 1, "snippet": "1232SA26Q0557"},
        "title": {"value": "Greenhouse light fixtures", "page": 1, "snippet": "fixtures"},
        "agency": {"value": "USDA", "page": 1, "snippet": "USDA"},
        "line_items": [line, option],
        "required_delivery": {
            "value": "All items within 60 days after award",
            "page": 12,
            "snippet": "delivery of all items within 60 days after award",
        },
        "key_clauses": [],
    }


def walk(node: object) -> None:
    """Assert every object level forbids extra properties (strict schema)."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, node
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)


def test_schema_requires_page_and_snippet_per_field() -> None:
    """Every object in the sent schema is strict; cited fields need page+snippet."""
    walk(EXTRACTION_SCHEMA)
    props = EXTRACTION_SCHEMA["properties"]
    assert isinstance(props, dict)
    line_props = props["line_items"]["items"]["properties"]
    assert set(line_props) == {"line", "description", "part_or_nsn", "quantity", "unit"}
    for field_schema in line_props.values():
        assert field_schema["required"] == ["value", "page", "snippet"]


def test_demo_line_items_validate() -> None:
    """Both demo CLINs (0001 base, 1001 option) validate."""
    extraction = SolicitationExtraction.model_validate(valid_payload())
    assert [item.line.value for item in extraction.line_items] == ["0001", "1001"]
    assert extraction.required_delivery.page == 12


def test_missing_snippet_is_rejected() -> None:
    """A field without its verbatim snippet is rejected, not stored."""
    payload = valid_payload()
    items = payload["line_items"]
    assert isinstance(items, list)
    first = items[0]
    assert isinstance(first, dict)
    quantity = first["quantity"]
    assert isinstance(quantity, dict)
    del quantity["snippet"]
    with pytest.raises(ValidationError):
        SolicitationExtraction.model_validate(payload)


def test_missing_page_is_rejected() -> None:
    """A field without its page number is rejected, not stored."""
    payload = valid_payload()
    delivery = payload["required_delivery"]
    assert isinstance(delivery, dict)
    del delivery["page"]
    with pytest.raises(ValidationError):
        SolicitationExtraction.model_validate(payload)


def test_wrong_line_item_shape_is_rejected() -> None:
    """A line item missing quantity is rejected, not stored."""
    payload = valid_payload()
    items = payload["line_items"]
    assert isinstance(items, list)
    first = items[0]
    assert isinstance(first, dict)
    del first["quantity"]
    with pytest.raises(ValidationError):
        SolicitationExtraction.model_validate(payload)
