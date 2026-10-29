"""Gap and ambiguity pass via MODEL_READ (A07).

Reads the solicitation PDFs at high reasoning effort and flags what is
missing or contradictory: a missing packaging spec, an unclear unit of
issue, conflicting dates or quantities. Every flag links the clause or
passage it relates to with a page and a verbatim snippet. The hand-checked
``known_ambiguities`` in the solicitation JSON are the answer key.
"""

import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import Settings
from app.extract import pdf_part
from app.schemas import SourceRef

GAP_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "flags": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"},
                    "clause": {"type": "string"},
                    "source": {
                        "type": "object",
                        "description": "The conflicting or unclear passage.",
                        "properties": {
                            "file": {"type": "string"},
                            "page": {"type": "integer"},
                            "snippet": {"type": "string"},
                        },
                        "required": ["file", "page", "snippet"],
                        "additionalProperties": False,
                    },
                },
                "required": ["issue", "clause", "source"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["flags"],
    "additionalProperties": False,
}

PROMPT = (
    "Review this federal solicitation for gaps and ambiguities a bidder must resolve "
    "before quoting: a missing packaging or labeling spec, an unclear unit of issue, "
    "conflicting delivery dates, conflicting quantities, conflicting part descriptions, "
    "or an unclear evaluation basis. For each flag state the issue, name the clause or "
    "section it relates to, and give the file name, 1-based page number and exact "
    "verbatim snippet of the passage. Return only JSON matching the schema."
)


class GapFlag(BaseModel):
    """One gap or ambiguity, linked to its clause or passage."""

    issue: str
    clause: str
    source: SourceRef


class GapReport(BaseModel):
    """Validated MODEL_READ gap pass output."""

    flags: list[GapFlag] = Field(default_factory=list)


def gap_pass(pdf_paths: list[Path], settings: Settings) -> GapReport:
    """Run the gap pass over the given PDFs; raise on invalid output."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    for pdf_path in pdf_paths:
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    response = client.responses.create(
        model=settings.model_read,
        reasoning={"effort": "high"},
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
                "name": "solicitation_gaps",
                "schema": GAP_SCHEMA,
                "strict": True,
            }
        },
    )
    return GapReport.model_validate(json.loads(response.output_text))
