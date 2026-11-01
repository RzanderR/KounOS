"""Triage fit-fact extraction via MODEL_READ (A34).

Sends one notice PDF as-is and requires every fit fact back with a
1-based page number and a verbatim snippet (~5 words or more). Anything
that fails validation is rejected, never stored. Facts read "not stated"
stay missing on the Notice: never guessed. Snippets are checked with the
A06 citation checker against the ingested notice PDF; a fact whose
snippet does not verify also stays missing, so it never drives scoring,
and its citation is kept on the Notice marked ``needs_review``.
"""

import base64
import json
from pathlib import Path

from decimal import Decimal, InvalidOperation

from openai import OpenAI
from pydantic import BaseModel

from app import cite
from app.config import REPO_ROOT, Settings
from app.ingest import ingest_pdf
from app.schemas import KeyClause, Notice, SourceRef

NOTICES_DIR = REPO_ROOT / "data" / "notices"

NOT_STATED = "not stated"


def cited_fact(description: str) -> dict[str, object]:
    """One fit fact: its value (or 'not stated') plus where it was read."""
    return {
        "type": "object",
        "description": description,
        "properties": {
            "value": {"type": "string"},
            "page": {"type": "integer"},
            "snippet": {"type": "string"},
        },
        "required": ["value", "page", "snippet"],
        "additionalProperties": False,
    }


FIT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "title": cited_fact("What is being bought."),
        "agency": cited_fact("The buying agency."),
        "set_aside": cited_fact(
            "The set-aside (e.g. total small business), or 'not stated'."
        ),
        "product_category": cited_fact(
            "What is being bought, in a few words (e.g. LED greenhouse "
            "fixtures), or 'not stated'."
        ),
        "quantity": cited_fact("How many, or 'not stated'."),
        "delivery_window": cited_fact(
            "When delivery is due, or 'not stated'."
        ),
        "estimated_value": cited_fact(
            "The estimated dollar value, or 'not stated'."
        ),
        "competition_signal": cited_fact(
            "Any competition signal (e.g. sole source, number of offers "
            "expected), or 'not stated'."
        ),
    },
    "required": [
        "title",
        "agency",
        "set_aside",
        "product_category",
        "quantity",
        "delivery_window",
        "estimated_value",
        "competition_signal",
    ],
    "additionalProperties": False,
}

PROMPT = (
    "Extract the triage fit facts from this federal notice. Every field "
    "needs its value, the 1-based page number, and a verbatim snippet of "
    "about five words or more supporting it. A fact the notice does not "
    "state must read exactly 'not stated' with the page and snippet of "
    "where it would appear. Return only JSON matching the schema."
)


class CitedFact(BaseModel):
    """One extracted fit fact with its page and verbatim snippet."""

    value: str
    page: int
    snippet: str


class FitExtraction(BaseModel):
    """Validated MODEL_READ output for one notice. Rejected when invalid."""

    title: CitedFact
    agency: CitedFact
    set_aside: CitedFact
    product_category: CitedFact
    quantity: CitedFact
    delivery_window: CitedFact
    estimated_value: CitedFact
    competition_signal: CitedFact


def extract_fit_facts(pdf_path: Path, settings: Settings) -> FitExtraction:
    """Run fit extraction over one notice PDF; raise on invalid output."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
    response = client.responses.create(
        model=settings.model_read,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    {
                        "type": "input_file",
                        "filename": pdf_path.name,
                        "file_data": f"data:application/pdf;base64,{pdf_b64}",
                    },
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "fit_facts",
                "schema": FIT_SCHEMA,
                "strict": True,
            }
        },
    )
    return FitExtraction.model_validate(json.loads(response.output_text))


def _present(value: str) -> str | None:
    """A 'not stated' fact stays missing; anything else is kept."""
    if value.strip().lower() in (NOT_STATED, "not stated.", "n/a", ""):
        return None
    return value


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return int(digits) if digits else None


def _parse_decimal(value: str | None) -> Decimal | None:
    """First $-token as Decimal; unparseable values stay missing."""
    if value is None:
        return None
    cleaned = value.replace("$", "").replace(",", "").strip().split()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned[0])
    except InvalidOperation:
        return None


def build_notice(
    notice_id: str,
    extraction: FitExtraction,
    citations: dict[str, cite.CitationResult],
    pdf_file: str,
) -> Notice:
    """A Notice from checked facts; unstated or unverified facts stay None."""

    def checked(field: str) -> str | None:
        if citations[field].status != "verified":
            return None
        fact: CitedFact = getattr(extraction, field)
        return _present(fact.value)

    cited = []
    for field in FIT_FIELDS:
        fact = getattr(extraction, field)
        result = citations[field]
        cited.append(
            KeyClause(
                name=field,
                summary=fact.value,
                source=SourceRef(
                    file=pdf_file,
                    page=result.actual_page or result.page,
                    snippet=fact.snippet,
                ),
                citation_status=result.status,
                boxes=result.boxes,
            )
        )
    return Notice(
        notice_id=notice_id,
        title=extraction.title.value,
        agency=extraction.agency.value,
        set_aside=checked("set_aside"),
        product_category=checked("product_category"),
        quantity=_parse_int(checked("quantity")),
        delivery_window=checked("delivery_window"),
        estimated_value=_parse_decimal(checked("estimated_value")),
        competition_signal=checked("competition_signal"),
        citations=cited,
    )


FIT_FIELDS = (
    "title",
    "agency",
    "set_aside",
    "product_category",
    "quantity",
    "delivery_window",
    "estimated_value",
    "competition_signal",
)


def check_fit_facts(
    pdf_path: Path, extraction: FitExtraction
) -> dict[str, cite.CitationResult]:
    """Check every fact snippet against the ingested notice PDF (A06)."""
    pages = ingest_pdf(pdf_path).pages
    results = {}
    for field in FIT_FIELDS:
        fact: CitedFact = getattr(extraction, field)
        results[field] = cite.check_citation(pages, fact.snippet, fact.page)
    return results


def cited_notice(notice_id: str, pdf_path: Path, extraction: FitExtraction) -> Notice:
    """Check every fact against the notice PDF, then build the record."""
    resolved = pdf_path.resolve()
    root = REPO_ROOT.resolve()
    pdf_file = (
        resolved.relative_to(root).as_posix()
        if resolved.is_relative_to(root)
        else pdf_path.name
    )
    return build_notice(
        notice_id, extraction, check_fit_facts(pdf_path, extraction), pdf_file
    )


def list_notice_ids() -> list[str]:
    """Stored notice records (empty until the H16 batch lands)."""
    if not NOTICES_DIR.is_dir():
        return []
    return sorted(
        path.stem for path in NOTICES_DIR.glob("*.json") if path.is_file()
    )


def load_notice(notice_id: str) -> Notice:
    """One stored notice record; names H16 when the batch is missing."""
    if "/" in notice_id or "\\" in notice_id or notice_id.startswith("."):
        raise ValueError(f"Unsafe notice id: {notice_id!r}")
    path = (NOTICES_DIR / f"{notice_id}.json").resolve()
    if path.parent != NOTICES_DIR.resolve() or not path.is_file():
        raise FileNotFoundError(
            f"Notice not found: {notice_id} (triage batch lands with H16)."
        )
    return Notice.model_validate(json.loads(path.read_text(encoding="utf-8")))



