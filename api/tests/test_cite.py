"""Citation-check tests (A06) on the ingested demo specifications PDF."""

import pytest

from app.cite import check_citation
from app.config import REPO_ROOT
from app.ingest import IngestedDocument, ingest_pdf


@pytest.fixture(scope="module")
def specs() -> IngestedDocument:
    """Ingest the demo specifications PDF once for the module."""
    return ingest_pdf(REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_specifications.pdf")


def test_exact_snippet_verifies_with_word_boxes(specs: IngestedDocument) -> None:
    """A verbatim snippet on its page verifies and locates word boxes."""
    result = check_citation(specs.pages, "LED Greenhouse light fixture", 1)
    assert result.status == "verified"
    assert result.actual_page is None
    assert len(result.boxes) == 4
    assert [box.text for box in result.boxes] == ["LED", "Greenhouse", "light", "fixture"]
    assert all(box.x0 <= box.x1 and box.top <= box.bottom for box in result.boxes)


def test_hyphenated_and_line_broken_snippet_verifies(specs: IngestedDocument) -> None:
    """A hyphen- and newline-broken snippet still matches its passage."""
    result = check_citation(specs.pages, "Green- house light\nfixture Quantity:", 1)
    assert result.status == "verified"
    assert [box.text for box in result.boxes] == ["Greenhouse", "light", "fixture", "Quantity:"]


def test_short_snippet_needs_review_even_when_present(specs: IngestedDocument) -> None:
    """A sub-four-word snippet cannot locate a claim, however common its text."""
    for snippet in ("58", "EA", "PTB8850LS41"):
        result = check_citation(specs.pages, snippet, 1)
        assert result.status == "needs_review"
        assert result.boxes == []


def test_snippet_on_wrong_page_needs_review(specs: IngestedDocument) -> None:
    """A page-2 passage claimed for page 1 is flagged with its real page."""
    result = check_citation(specs.pages, "Delivery and Incidental Service Schedule", 1)
    assert result.status == "needs_review"
    assert result.actual_page == 2
    assert result.boxes


def test_unknown_snippet_needs_review_without_boxes(specs: IngestedDocument) -> None:
    """A snippet found nowhere is flagged with no word boxes."""
    result = check_citation(specs.pages, "this passage appears in no PDF at all xyzzy", 1)
    assert result.status == "needs_review"
    assert result.actual_page is None
    assert result.boxes == []


def test_claimed_page_out_of_range_still_searches(specs: IngestedDocument) -> None:
    """A bad page number does not hide a passage found elsewhere."""
    result = check_citation(specs.pages, "LED Greenhouse light fixture", 99)
    assert result.status == "needs_review"
    assert result.actual_page == 1
