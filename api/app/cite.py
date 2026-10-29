"""Citation check with RapidFuzz (A06).

Every extracted field carries a page number and a verbatim snippet. This
module checks the snippet against the ingested page text and marks the
field ``verified`` or ``needs_review``. Hyphenated and line-broken
snippets still match; a snippet found on the wrong page is flagged with
the page it was actually found on. Matched word boxes locate the passage.
"""

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field
from rapidfuzz import fuzz

from app.ingest import PageContent
from app.schemas import WordBox

# Below this partial-ratio a snippet is not the passage it claims to be.
MATCH_THRESHOLD = 90.0

# A snippet shorter than this proves nothing: "58" or "EA" matches too many
# passages to locate the claim, so it always needs review.
MIN_SNIPPET_WORDS = 4


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


def aligned_word_boxes(
    page: PageContent, fused_text: str, start: int, end: int
) -> list[WordBox]:
    """Word boxes for a fused-text span, or [] when words do not line up.

    The span is widened to token boundaries, then matched as an exact run
    against the hyphen-fused page words, so a fuzzy passage still highlights
    the words it came from (e.g. a table row interleaved with other columns).
    """
    start = max(0, start)
    end = min(len(fused_text), end)
    while start > 0 and fused_text[start - 1] != " ":
        start -= 1
    while end < len(fused_text) and fused_text[end] != " ":
        end += 1
    words = fused_text[start:end].split()
    if not words:
        return []
    fused = fuse_spans([word.text.lower() for word in page.words])
    for i in range(len(fused) - len(words) + 1):
        if [text for text, _, _ in fused[i : i + len(words)]] == words:
            _, raw_start, _ = fused[i]
            _, _, raw_end = fused[i + len(words) - 1]
            return page.words[raw_start:raw_end]
    return []


def matched_word_count(box_texts: list[str], query_words: list[str]) -> int:
    """Multiset overlap between highlight words and the snippet's words."""
    box_counts = Counter(text.lower() for text in box_texts)
    query_counts = Counter(word.lower() for word in query_words)
    return sum(min(query_counts[word], box_counts[word]) for word in query_counts)


def coverage_word_boxes(
    page: PageContent, query_words: list[str], extra: int = 8, min_cover: float = 0.6
) -> list[WordBox]:
    """Densest query-word window, for rows whose cells interleave columns.

    A table row holds every snippet word but splits them across cells
    (line number, quantity, unit), so no contiguous character span covers
    them all. The window holding the most snippet words is the row.
    """
    fused = fuse_spans([word.text.lower() for word in page.words])
    texts = [text for text, _, _ in fused]
    query = [word.lower() for word in query_words]
    counts = Counter(query)
    best: tuple[tuple[float, int, int], int, int] | None = None
    for size in range(len(query), min(len(texts), len(query) + extra) + 1):
        for i in range(len(texts) - size + 1):
            window = Counter(texts[i : i + size])
            matched = sum(min(counts[word], window[word]) for word in counts)
            key = (matched / len(query), -size, -i)
            if best is None or key > best[0]:
                best = (key, i, size)
    if best is None:
        return []
    (cover, _, _), i, size = best
    if cover < min_cover or cover * len(query) < 4:
        return []
    _, raw_start, _ = fused[i]
    _, _, raw_end = fused[i + size - 1]
    return page.words[raw_start:raw_end]


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
    if snippet:
        alignment = fuzz.partial_ratio_alignment(fuse_hyphens(snippet), page_text)
        if alignment is not None and alignment.score >= MATCH_THRESHOLD:
            boxes = aligned_word_boxes(
                page, page_text, alignment.dest_start, alignment.dest_end
            )
            if matched_word_count(
                [box.text for box in boxes], snippet_words
            ) < len(snippet_words):
                window = coverage_word_boxes(page, snippet_words)
                if matched_word_count(
                    [box.text for box in window], snippet_words
                ) > matched_word_count([box.text for box in boxes], snippet_words):
                    boxes = window
            return CitationResult(
                status="verified",
                page=page.page_number,
                snippet=snippet,
                boxes=boxes,
            )
    return CitationResult(status="needs_review", page=page.page_number, snippet=snippet)


def check_citation(
    pages: list[PageContent], snippet: str, page: int
) -> CitationResult:
    """Check a snippet against its claimed page, then the other pages.

    A match on the claimed page verifies. A match elsewhere marks
    ``needs_review`` and records where it was actually found. No match
    anywhere marks ``needs_review`` with no boxes. A snippet under
    ``MIN_SNIPPET_WORDS`` words always needs review: it cannot locate a claim.
    """
    if not snippet or not snippet.strip():
        return CitationResult(status="needs_review", page=page, snippet=snippet)
    if len(snippet.split()) < MIN_SNIPPET_WORDS:
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
