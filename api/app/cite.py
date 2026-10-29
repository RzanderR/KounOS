"""Citation check with RapidFuzz (A06).

Every extracted field carries a page number and a verbatim snippet. This
module checks the snippet against the ingested page text and marks the
field ``verified`` or ``needs_review``. Hyphenated and line-broken
snippets still match; a snippet found on the wrong page is flagged with
the page it was actually found on. Matched word boxes locate the passage.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field
from rapidfuzz import fuzz

from app.ingest import PageContent, WordBox

# Below this partial-ratio a snippet is not the passage it claims to be.
MATCH_THRESHOLD = 90.0


def normalize(text: str) -> str:
    """Lowercase and collapse all whitespace to single spaces."""
    return re.sub(r"\s+", " ", text).strip().lower()


def fuse_hyphens(text: str) -> str:
    """Join words broken by a hyphen and whitespace (``green- house``)."""
    return re.sub(r"-\s+", "", normalize(text))


def fuse_spans(tokens: list[str]) -> list[tuple[str, int, int]]:
    """Fuse hyphen-split tokens, keeping each fused token's raw span."""
    fused: list[tuple[str, int, int]] = []
    for index, token in enumerate(tokens):
        if fused and fused[-1][0].endswith("-"):
            text, start, _ = fused[-1]
            fused[-1] = (text[:-1] + token, start, index + 1)
        else:
            fused.append((token, index, index + 1))
    return fused


def match_span(page_words: list[str], snippet_words: list[str]) -> tuple[int, int] | None:
    """Raw word span of the snippet run in the page words, else None."""
    page = fuse_spans([word.lower() for word in page_words])
    snip = fuse_spans([word.lower() for word in snippet_words])
    if not snip or len(snip) > len(page):
        return None
    want = [text for text, _, _ in snip]
    for i in range(len(page) - len(snip) + 1):
        if page[i][0] == want[0] and [text for text, _, _ in page[i : i + len(snip)]] == want:
            return (page[i][1], page[i + len(snip) - 1][2])
    return None


class CitationResult(BaseModel):
    """Verdict for one cited snippet."""

    status: Literal["verified", "needs_review"]
    page: int
    actual_page: int | None = None
    snippet: str
    boxes: list[WordBox] = Field(default_factory=list)


def check_page(page: PageContent, snippet: str) -> CitationResult:
    """Check a snippet against one page; empty boxes when it is absent."""
    snippet_words = snippet.split()
    span = match_span([word.text for word in page.words], snippet_words)
    if span is not None:
        start, end = span
        return CitationResult(
            status="verified",
            page=page.page_number,
            snippet=snippet,
            boxes=page.words[start:end],
        )
    page_text = fuse_hyphens(page.text)
    if snippet and fuzz.partial_ratio(fuse_hyphens(snippet), page_text) >= MATCH_THRESHOLD:
        return CitationResult(
            status="verified", page=page.page_number, snippet=snippet, boxes=[]
        )
    return CitationResult(status="needs_review", page=page.page_number, snippet=snippet)


def check_citation(
    pages: list[PageContent], snippet: str, page: int
) -> CitationResult:
    """Check a snippet against its claimed page, then the other pages.

    A match on the claimed page verifies. A match elsewhere marks
    ``needs_review`` and records where it was actually found. No match
    anywhere marks ``needs_review`` with no boxes.
    """
    if not snippet or not snippet.strip():
        return CitationResult(status="needs_review", page=page, snippet=snippet)
    by_number = {number: content for number, content in ((p.page_number, p) for p in pages)}
    claimed = by_number.get(page)
    if claimed is not None:
        hit = check_page(claimed, snippet)
        if hit.status == "verified":
            return hit
    for content in pages:
        if content.page_number == page:
            continue
        hit = check_page(content, snippet)
        if hit.status == "verified":
            return CitationResult(
                status="needs_review",
                page=page,
                actual_page=content.page_number,
                snippet=snippet,
                boxes=hit.boxes,
            )
    return CitationResult(status="needs_review", page=page, snippet=snippet)
