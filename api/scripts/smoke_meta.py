"""Meta API smoke test (A02): send one solicitation PDF to MODEL_READ.

Reads the model id, base URL and API key from the environment via
app.config.Settings (repo-root .env). Prints the parsed JSON result that
validates against SmokeResult plus token usage.
"""

import base64
import json
import sys
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel

from app.config import REPO_ROOT, Settings

DEFAULT_PDF = REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_specifications.pdf"
PROMPT = (
    "Extract the solicitation facts from this PDF: the solicitation id, "
    "title, agency, and every line item (line number, description, quantity). "
    "Return only JSON matching the schema."
)


class SmokeLineItem(BaseModel):
    line: str
    description: str
    quantity: int


class SmokeResult(BaseModel):
    solicitation_id: str
    title: str
    agency: str
    line_items: list[SmokeLineItem]


SCHEMA = {
    "type": "object",
    "properties": {
        "solicitation_id": {"type": "string"},
        "title": {"type": "string"},
        "agency": {"type": "string"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "string"},
                    "description": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["line", "description", "quantity"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["solicitation_id", "title", "agency", "line_items"],
    "additionalProperties": False,
}


def main(pdf_path: Path) -> int:
    settings = Settings()
    if not settings.model_api_key:
        print("MODEL_API_KEY is not set (repo-root .env).", file=sys.stderr)
        return 2
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

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
                "name": "solicitation",
                "schema": SCHEMA,
                "strict": True,
            }
        },
    )

    result = SmokeResult.model_validate(json.loads(response.output_text))
    print(result.model_dump_json(indent=2))
    usage = response.usage
    print(
        "token_usage: input=%d output=%d total=%d"
        % (usage.input_tokens, usage.output_tokens, usage.total_tokens)
    )
    return 0


if __name__ == "__main__":
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    raise SystemExit(main(pdf))
