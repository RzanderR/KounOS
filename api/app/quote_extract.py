"""Quote extraction via MODEL_READ (A10).

One schema reads all three quote formats: the Ninebark PDF quote, the
Larkspur email screenshot (PNG) and the Tallgrass printed-and-photographed
quote (PDF). Files go to the model as-is; money comes back as plain
numbers and is converted to ``Decimal`` only in code.
"""

import base64
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openai import OpenAI
from openai.types.responses import ResponseInputFileParam
from pydantic import BaseModel, Field

from app.config import Settings
from app.schemas import Quote, QuoteLine


def money_field(description: str) -> dict[str, object]:
    """One money amount as a plain number string, e.g. "668.00"."""
    return {
        "type": "object",
        "description": description,
        "properties": {
            "value": {"type": "string"},
            "snippet": {"type": "string"},
        },
        "required": ["value", "snippet"],
        "additionalProperties": False,
    }


QUOTE_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "supplier": {"type": "string"},
        "quote_number": {"type": "string"},
        "quote_date": {"type": "string"},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "part": {"type": "string"},
                    "description": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "unit": {"type": "string"},
                    "unit_price": {"type": "string"},
                    "extended": {"type": "string"},
                },
                "required": ["part", "description", "quantity", "unit", "unit_price", "extended"],
                "additionalProperties": False,
            },
        },
        "freight": money_field("Freight or shipping total; 0 when included or free."),
        "quote_total": money_field("The quote grand total."),
        "lead_time_text": {"type": "string"},
        "lead_time_days_max": {"type": "integer"},
        "payment_terms": {"type": "string"},
        "country_of_origin": {
            "type": "string",
            "description": "Stated country of origin, or 'not stated' when absent.",
        },
    },
    "required": [
        "supplier",
        "quote_number",
        "quote_date",
        "lines",
        "freight",
        "quote_total",
        "lead_time_text",
        "lead_time_days_max",
        "payment_terms",
        "country_of_origin",
    ],
    "additionalProperties": False,
}

PROMPT = (
    "Extract this supplier quote into structured data. Read the part number, "
    "description, quantity, unit and prices off every line, plus freight, the "
    "grand total, lead time (and its worst-case days), payment terms and the "
    "stated country of origin (write 'not stated' when none is given). Money "
    "as plain numbers without currency signs or commas. Snippets must be the "
    "surrounding line or phrase, at least about five words long. "
    "Return only JSON matching the schema."
)


class ExtractedMoney(BaseModel):
    """One money amount with the phrase it was read from."""

    value: str
    snippet: str


class ExtractedQuoteLine(BaseModel):
    """One priced line on the quote."""

    part: str
    description: str
    quantity: int
    unit: str
    unit_price: str
    extended: str


class QuoteExtraction(BaseModel):
    """Validated MODEL_READ output for one quote file."""

    supplier: str
    quote_number: str
    quote_date: str
    lines: list[ExtractedQuoteLine] = Field(default_factory=list)
    freight: ExtractedMoney
    quote_total: ExtractedMoney
    lead_time_text: str
    lead_time_days_max: int
    payment_terms: str
    country_of_origin: str


def parse_money(raw: str) -> Decimal:
    """Parse a plain-number money string; reject currency signs and commas."""
    return Decimal(raw.strip())


def file_part(file_path: Path, media_type: str) -> ResponseInputFileParam:
    """Encode one quote file (PDF or image) as a Responses API file part."""
    data = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return {
        "type": "input_file",
        "filename": file_path.name,
        "file_data": f"data:{media_type};base64,{data}",
    }


def media_type_for(file_path: Path) -> str:
    """MIME type for a quote file by suffix."""
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(file_path.suffix.lower(), "application/octet-stream")


def extract_quote(file_path: Path, settings: Settings) -> QuoteExtraction:
    """Run extraction over one quote file; raise on invalid output."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    if not file_path.is_file():
        raise FileNotFoundError(f"Quote file not found: {file_path}")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    response = client.responses.create(
        model=settings.model_read,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    file_part(file_path, media_type_for(file_path)),
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "quote_extraction",
                "schema": QUOTE_SCHEMA,
                "strict": True,
            }
        },
    )
    return QuoteExtraction.model_validate(json.loads(response.output_text))


def to_quote_record(
    extraction: QuoteExtraction, quote_id: str, solicitation_id: str
) -> Quote:
    """Convert validated extraction to a Quote record; money becomes Decimal."""
    try:
        freight = parse_money(extraction.freight.value)
        total = parse_money(extraction.quote_total.value)
        lines = [
            QuoteLine(
                line=str(index + 1),
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=parse_money(item.unit_price),
                extended=parse_money(item.extended),
                part=item.part,
            )
            for index, item in enumerate(extraction.lines)
        ]
    except InvalidOperation as exc:
        raise ValueError(f"Quote money is not a plain number: {exc}") from exc
    return Quote(
        quote_id=quote_id,
        supplier=extraction.supplier,
        solicitation_id=solicitation_id,
        lines=lines,
        freight=freight,
        total=total,
        lead_time_days_max=extraction.lead_time_days_max,
        country_of_origin=extraction.country_of_origin,
    )
