"""Solicitation extraction via MODEL_READ (A05).

Sends the solicitation PDFs as-is and requires every field back with a
1-based page number and a verbatim snippet. Anything that fails
validation is rejected, never stored.
"""

import base64
import json
from pathlib import Path

from openai import OpenAI
from openai.types.responses import ResponseInputFileParam
from pydantic import BaseModel, Field

from app.config import Settings


def cited_field(description: str) -> dict[str, object]:
    """One extracted field: its value plus where it was read."""
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


EXTRACTION_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "solicitation_id": cited_field("The solicitation number."),
        "title": cited_field("What is being bought."),
        "agency": cited_field("The buying agency."),
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "line": cited_field("The CLIN or line number."),
                    "description": cited_field("What this line asks for."),
                    "part_or_nsn": cited_field("Required part number or NSN, or 'not stated'."),
                    "quantity": cited_field("How many."),
                    "unit": cited_field("Unit of issue, e.g. EA."),
                },
                "required": ["line", "description", "part_or_nsn", "quantity", "unit"],
                "additionalProperties": False,
            },
        },
        "required_delivery": cited_field("When and where delivery is due."),
        "sourcing_clause": cited_field(
            "The domestic-sourcing / Buy American / Trade Agreements clause: "
            "its FAR number (e.g. FAR 52.225-3), what it requires, and whether "
            "a certificate (e.g. 52.225-4) applies."
        ),
        "key_clauses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "detail": cited_field("The clause or term."),
                },
                "required": ["name", "detail"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "solicitation_id",
        "title",
        "agency",
        "line_items",
        "required_delivery",
        "sourcing_clause",
        "key_clauses",
    ],
    "additionalProperties": False,
}

PROMPT = (
    "Extract the facts of this federal solicitation. Every field needs its value, "
    "the 1-based page number it appears on, and the exact verbatim snippet you read it from. "
    "Each snippet must be the surrounding line or phrase, at least about five words long: "
    "a bare number, unit or part code alone proves nothing, so always include its context. "
    "Line items: every CLIN with line number, description, part number or NSN "
    "(write 'not stated' when none is given), quantity and unit. "
    "Also extract the required delivery term and the key clauses "
    "(delivery, FOB, brand-name requirement, sourcing clause, evaluation basis). "
    "Clause lists use checkboxes: report only checked clauses, never unchecked ones. "
    "The sourcing clause is required: give its FAR number (e.g. FAR 52.225-3) and "
    "whether a certificate (e.g. 52.225-4) applies. "
    "Return only JSON matching the schema."
)


class CitedField(BaseModel):
    """One extracted fact with its page and verbatim snippet."""

    value: str
    page: int
    snippet: str


class ExtractedLineItem(BaseModel):
    """One solicitation line item, every field cited."""

    line: CitedField
    description: CitedField
    part_or_nsn: CitedField
    quantity: CitedField
    unit: CitedField


class ExtractedClause(BaseModel):
    """One key clause or term, cited."""

    name: str
    detail: CitedField


class SolicitationExtraction(BaseModel):
    """Validated MODEL_READ output. Rejected when it fails this schema."""

    solicitation_id: CitedField
    title: CitedField
    agency: CitedField
    line_items: list[ExtractedLineItem] = Field(default_factory=list)
    required_delivery: CitedField
    sourcing_clause: CitedField
    key_clauses: list[ExtractedClause] = Field(default_factory=list)


def pdf_part(pdf_path: Path) -> ResponseInputFileParam:
    """Encode one PDF as a Responses API file input part."""
    pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
    return {
        "type": "input_file",
        "filename": pdf_path.name,
        "file_data": f"data:application/pdf;base64,{pdf_b64}",
    }


def extract_solicitation(pdf_paths: list[Path], settings: Settings) -> SolicitationExtraction:
    """Run extraction over the given PDFs; raise on invalid output."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    for pdf_path in pdf_paths:
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    response = client.responses.create(
        model=settings.model_read,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    *(pdf_part(path) for path in pdf_paths),
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "solicitation_extraction",
                "schema": EXTRACTION_SCHEMA,
                "strict": True,
            }
        },
    )
    return SolicitationExtraction.model_validate(json.loads(response.output_text))
