"""PDF ingest tests (A04) on the real demo solicitation PDFs."""

from pathlib import Path

from app.config import REPO_ROOT
from app.ingest import IngestedDocument, ingest_pdf

SPECS = REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_specifications.pdf"
TERMS = REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_terms_and_clauses.pdf"


def test_specs_pdf_page_count_text_and_word_boxes() -> None:
    """The specifications PDF ingests as 2 pages with text and word boxes."""
    doc = ingest_pdf(Path(SPECS))
    assert isinstance(doc, IngestedDocument)
    assert doc.page_count == 2
    assert len(doc.pages) == 2
    first = doc.pages[0]
    assert first.page_number == 1
    assert "Greenhouse light fixture" in first.text
    assert len(first.words) > 100
    for word in first.words[:50]:
        assert word.text
        assert word.x0 <= word.x1
        assert word.top <= word.bottom


def test_terms_pdf_page_count() -> None:
    """The terms PDF ingests as 16 pages, each with text."""
    doc = ingest_pdf(Path(TERMS))
    assert doc.page_count == 16
    assert [page.page_number for page in doc.pages] == list(range(1, 17))
    assert all(page.text.strip() for page in doc.pages)
