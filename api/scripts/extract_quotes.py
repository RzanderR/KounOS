"""Run quote extraction (A10) over the three fictional quote files.

Usage (from api/): python scripts/extract_quotes.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import REPO_ROOT, Settings
from app.quote_extract import QuoteExtraction, extract_quote, to_quote_record

QUOTE_FILES = [
    ("ninebark", REPO_ROOT / "data" / "quotes" / "docs" / "ninebark_quote.pdf"),
    ("larkspur", REPO_ROOT / "data" / "quotes" / "docs" / "larkspur_email.png"),
    (
        "tallgrass",
        REPO_ROOT
        / "data"
        / "quotes"
        / "docs"
        / "tallgrass_quote_PRINT_AND_PHOTOGRAPH.pdf",
    ),
]


def main() -> int:
    """Extract each quote, print its record, check it against its fixture."""
    settings = Settings()
    if not settings.model_api_key:
        print("MODEL_API_KEY is not set (repo-root .env).", file=sys.stderr)
        return 2
    out_dir = REPO_ROOT / "data" / "extractions"
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for quote_id, file_path in QUOTE_FILES:
        extraction: QuoteExtraction = extract_quote(file_path, settings)
        record = to_quote_record(extraction, quote_id, "1232SA26Q0557")
        (out_dir / f"quotes_{quote_id}.json").write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )
        print(record.model_dump_json(indent=2))
        fixture = json.loads(
            (REPO_ROOT / "data" / "quotes" / f"{quote_id}.json").read_text(
                encoding="utf-8"
            )
        )
        checks = {
            "supplier": record.supplier.lower() == fixture["supplier"].lower(),
            "total": str(record.total) == fixture["quote_total"],
            "lead_time_days_max": record.lead_time_days_max
            == fixture["lead_time_days_max"],
            "parts": [line.part.upper() for line in record.lines]
            == [line["part"].upper() for line in fixture["lines"]],
        }
        print(f"{quote_id}: {checks}")
        failures += sum(1 for ok in checks.values() if not ok)
    print(f"mismatches: {failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
