"""PDF ingest with pdfplumber (A04).

Reads each page's text and every word's bounding box. The boxes let the
citation check (A06) point at the exact passage a snippet came from.
Page numbers are 1-based to match how the PDFs are cited by hand.
"""

from pathlib import Path

import pdfplumber
from pydantic import BaseModel, Field


class WordBox(BaseModel):
    """One word and where it sits on its page (PDF points)."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float


class PageContent(BaseModel):
    """Text and word boxes for one page."""

    page_number: int
    text: str
    words: list[WordBox] = Field(default_factory=list)


class IngestedDocument(BaseModel):
    """A PDF reduced to per-page text plus word boxes."""

    file: str
    page_count: int
    pages: list[PageContent] = Field(default_factory=list)


def ingest_pdf(pdf_path: Path) -> IngestedDocument:
    """Extract page text and word boxes from one PDF."""
    pages: list[PageContent] = []
    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            words = [
                WordBox(
                    text=str(word["text"]),
                    x0=float(word["x0"]),
                    top=float(word["top"]),
                    x1=float(word["x1"]),
                    bottom=float(word["bottom"]),
                )
                for word in page.extract_words()
            ]
            pages.append(
                PageContent(page_number=number, text=page.extract_text() or "", words=words)
            )
    return IngestedDocument(file=pdf_path.name, page_count=len(pages), pages=pages)
