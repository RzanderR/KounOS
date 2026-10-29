"""Demo solicitation for the A08 screen (A08).

Builds the solicitation from the stored MODEL_READ extraction
(``data/extractions/1232SA26Q0557_extraction.json``) and runs every cited
passage through the A06 citation check, so each row carries an honest,
code-computed ``verified`` or ``needs_review`` badge plus word boxes for
the PDF jump. The hand-checked answer key
(``data/solicitations/1232SA26Q0557.json``) is eval scoring input only
(A15); nothing from it is displayed here.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.cite import check_citation
from app.config import REPO_ROOT
from app.extract import SolicitationExtraction
from app.ingest import IngestedDocument, ingest_pdf
from app.schemas import KeyClause, Requirement, Solicitation, SourceRef, WordBox

STORED_EXTRACTION = REPO_ROOT / "data" / "extractions" / "1232SA26Q0557_extraction.json"
ATTACHMENTS_DIR = REPO_ROOT / "data" / "solicitations"

# The extraction cites page numbers but no file, so each snippet is checked
# against the specs PDF first (the requirements document), then the terms
# PDF. Snippets are honest either way: the badge says where it verified.
DOC_ORDER = (
    "1232SA26Q0557_specifications.pdf",
    "1232SA26Q0557_terms_and_clauses.pdf",
)


@lru_cache(maxsize=4)
def _ingest_cached(path_str: str) -> IngestedDocument:
    """Ingest once per PDF; pages are only read, never mutated."""
    return ingest_pdf(Path(path_str))


@lru_cache(maxsize=1)
def _stored_extraction() -> SolicitationExtraction:
    """The stored model output; invalid JSON fails closed here, not on screen."""
    return SolicitationExtraction.model_validate(
        json.loads(STORED_EXTRACTION.read_text(encoding="utf-8"))
    )


@lru_cache(maxsize=1)
def demo_id() -> str:
    """The demo solicitation id, read from the stored extraction."""
    return _stored_extraction().solicitation_id.value


def _cite(
    page: int, snippet: str
) -> tuple[Literal["verified", "needs_review"], str, int, list[WordBox]]:
    """Check one passage; return its status, file, page and word boxes."""
    fallback: tuple[Literal["verified", "needs_review"], str, int, list[WordBox]] | None = (
        None
    )
    for file in DOC_ORDER:
        pages = _ingest_cached(str(ATTACHMENTS_DIR / file)).pages
        if not 1 <= page <= len(pages):
            continue
        result = check_citation(pages, snippet, page)
        if result.status == "verified":
            return result.status, file, page, result.boxes
        if fallback is None:
            found = result.actual_page if result.actual_page is not None else page
            fallback = (result.status, file, found, result.boxes)
    if fallback is not None:
        return fallback
    specs_pages = _ingest_cached(str(ATTACHMENTS_DIR / DOC_ORDER[0])).pages
    file = DOC_ORDER[0] if page <= len(specs_pages) else DOC_ORDER[1]
    return "needs_review", file, page, []


def _quantity(raw: str) -> tuple[int, bool]:
    """Parse an extracted quantity; flag when it is not a whole number."""
    try:
        return int(raw.strip()), True
    except ValueError:
        return 0, False


def build_demo_solicitation(model_read: str) -> Solicitation:
    """Build the demo solicitation from the stored extraction with badges."""
    extraction = _stored_extraction()
    requirements = []
    for item in extraction.line_items:
        quantity, quantity_ok = _quantity(item.quantity.value)
        part = item.part_or_nsn.value.strip()
        status, file, page, boxes = _cite(item.description.page, item.description.snippet)
        for field in (item.line, item.part_or_nsn, item.quantity, item.unit):
            field_status, field_file, field_page, field_boxes = _cite(
                field.page, field.snippet
            )
            if field_status == "needs_review":
                status = "needs_review"
            if not boxes and field_boxes:
                file, page, boxes = field_file, field_page, field_boxes
        if not quantity_ok:
            status = "needs_review"
        requirements.append(
            Requirement(
                line=item.line.value,
                description=item.description.value,
                quantity=quantity,
                unit=item.unit.value,
                part_or_nsn=None if part.lower() == "not stated" else part,
                source=SourceRef(
                    file=file, page=page, snippet=item.description.snippet
                ),
                citation_status=status,
                boxes=boxes,
            )
        )
    clauses: list[KeyClause] = []
    for clause in extraction.key_clauses:
        status, file, page, boxes = _cite(
            clause.detail.page, clause.detail.snippet
        )
        clauses.append(
            KeyClause(
                name=clause.name,
                summary=clause.detail.value,
                source=SourceRef(
                    file=file, page=page, snippet=clause.detail.snippet
                ),
                citation_status=status,
                boxes=boxes,
            )
        )
    return Solicitation(
        solicitation_id=extraction.solicitation_id.value,
        title=extraction.title.value,
        agency=extraction.agency.value,
        requirements=requirements,
        key_clauses=clauses,
        provenance_note=(
            f"Extracted by {model_read} (MODEL_READ); every passage checked in code. "
            "Stored output: data/extractions/1232SA26Q0557_extraction.json. "
            "The hand-checked answer key is eval scoring input only, never displayed."
        ),
    )
