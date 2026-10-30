"""Gap-pass contract tests (A07): schema shape, rejection, answer key."""

import json

import pytest
from pydantic import ValidationError

from app.config import REPO_ROOT
from app.gaps import GAP_SCHEMA, GapReport


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


def test_schema_links_every_flag_to_page_and_snippet() -> None:
    """Every flag needs its issue, clause and a page-plus-snippet source."""
    walk(GAP_SCHEMA)
    item_props = GAP_SCHEMA["properties"]["flags"]["items"]["properties"]
    assert set(item_props) == {"issue", "clause", "source"}
    assert item_props["source"]["required"] == ["file", "page", "snippet"]


def test_flag_without_snippet_is_rejected() -> None:
    """A flag without its verbatim passage is rejected, not stored."""
    with pytest.raises(ValidationError):
        GapReport.model_validate(
            {
                "flags": [
                    {
                        "issue": "Conflicting delivery dates.",
                        "clause": "delivery",
                        "source": {"file": "terms.pdf", "page": 12},
                    }
                ]
            }
        )


def test_answer_key_has_three_known_ambiguities() -> None:
    """The hand-checked answer key holds the three genuine conflicts."""
    key = json.loads(
        (REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(key["known_ambiguities"]) == 3
    for ambiguity in key["known_ambiguities"]:
        assert ambiguity["issue"]
        assert ambiguity["refs"]
        for ref in ambiguity["refs"]:
            assert ref["file"].endswith(".pdf")
            assert isinstance(ref["page"], int)
