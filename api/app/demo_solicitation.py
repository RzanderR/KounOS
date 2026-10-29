"""Demo solicitation for the A08 screen (A08).

Builds the solicitation from the hand-checked answer key
(``data/solicitations/1232SA26Q0557.json``) and runs every cited passage
through the A06 citation check, so each row carries an honest,
code-computed ``verified`` or ``needs_review`` badge plus word boxes for
the PDF jump. Nothing here is model output: the provenance note says so
and names the live extraction as pending. When the live MODEL_READ run
lands on a dev machine, the same screen consumes it instead.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.cite import check_citation
from app.config import REPO_ROOT
from app.ingest import IngestedDocument, ingest_pdf
from app.schemas import KeyClause, Requirement, Solicitation, SourceRef, WordBox

ANSWER_KEY = REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557.json"
ATTACHMENTS_DIR = REPO_ROOT / "data" / "solicitations"

# Passages copied verbatim from the specifications PDF (page 1), observed
# during ingest probing. The citation check confirms each one at runtime.
SPECS_PART_SNIPPET = "PTB8850LS41 PHOTOBIO CX 2125 850W"
SPECS_OPTION_SNIPPET = "Quantity: 58+ one option to order 58 more."


@lru_cache(maxsize=4)
def _ingest_cached(path_str: str) -> IngestedDocument:
    """Ingest once per PDF; pages are only read, never mutated."""
    return ingest_pdf(Path(path_str))


@lru_cache(maxsize=1)
def demo_id() -> str:
    """The demo solicitation id, read from the answer key (no ingest)."""
    key = json.loads(ANSWER_KEY.read_text(encoding="utf-8"))
    solicitation_id = key["solicitation_id"]
    assert isinstance(solicitation_id, str)
    return solicitation_id


def _cite(
    file: str, page: int, snippet: str
) -> tuple[Literal["verified", "needs_review"], list[WordBox]]:
    """Check one passage; return its status and word boxes."""
    pages = _ingest_cached(str(ATTACHMENTS_DIR / file)).pages
    result = check_citation(pages, snippet, page)
    return result.status, result.boxes


def build_demo_solicitation(model_read: str) -> Solicitation:
    """Build the demo solicitation with code-checked citation badges."""
    key = json.loads(ANSWER_KEY.read_text(encoding="utf-8"))
    specs = "1232SA26Q0557_specifications.pdf"
    part_status, part_boxes = _cite(specs, 1, SPECS_PART_SNIPPET)
    option_status, option_boxes = _cite(specs, 1, SPECS_OPTION_SNIPPET)
    lines = {item["line"]: item for item in key["line_items"]}
    base = lines["0001"]
    option = lines["1001"]
    requirements = [
        Requirement(
            line="0001",
            description=base["description"],
            quantity=base["quantity"],
            unit=base["unit"],
            part_or_nsn="PTB8850LS41",
            source=SourceRef(file=specs, page=1, snippet=SPECS_PART_SNIPPET),
            citation_status=part_status,
            boxes=part_boxes,
        ),
        Requirement(
            line="1001",
            description=option["description"],
            quantity=option["quantity"],
            unit=option["unit"],
            part_or_nsn="PTB8850LS41",
            source=SourceRef(file=specs, page=1, snippet=SPECS_OPTION_SNIPPET),
            citation_status=option_status,
            boxes=option_boxes,
        ),
    ]
    clauses: list[KeyClause] = []
    confirmed = key["confirmed_from_attachments"]
    for name in ("delivery", "fob", "brand_name", "evaluation"):
        entry = confirmed[name]
        status, boxes = _cite(entry["file"], entry["page"], entry["snippet"])
        clauses.append(
            KeyClause(
                name=name,
                summary=entry["value"],
                source=SourceRef(
                    file=entry["file"], page=entry["page"], snippet=entry["snippet"]
                ),
                citation_status=status,
                boxes=boxes,
            )
        )
    return Solicitation(
        solicitation_id=key["solicitation_id"],
        title=key["title"],
        agency=key["agency"],
        sub_agency=key.get("sub_agency"),
        set_aside=key.get("set_aside"),
        naics=key.get("naics"),
        requirements=requirements,
        key_clauses=clauses,
        provenance_note=(
            "Hand-checked answer key "
            "(data/solicitations/1232SA26Q0557.json); citations checked in code. "
            f"Live MODEL_READ extraction ({model_read}) is pending: run "
            "scripts/extract_solicitation.py on a dev machine."
        ),
    )
