"""Run solicitation extraction (A05) and print the validated result.

Usage (from api/): python scripts/extract_solicitation.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import REPO_ROOT, Settings
from app.extract import SolicitationExtraction, extract_solicitation

DEFAULT_PDFS = [
    REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_specifications.pdf",
    REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_terms_and_clauses.pdf",
]


def main(pdf_paths: list[Path]) -> int:
    """Extract, validate and print the JSON result. Returns exit code."""
    settings = Settings()
    if not settings.model_api_key:
        print("MODEL_API_KEY is not set (repo-root .env).", file=sys.stderr)
        return 2
    extraction: SolicitationExtraction = extract_solicitation(pdf_paths, settings)
    print(extraction.model_dump_json(indent=2))
    print(f"line_items: {len(extraction.line_items)}")
    return 0


if __name__ == "__main__":
    pdfs = [Path(arg) for arg in sys.argv[1:]] or DEFAULT_PDFS
    raise SystemExit(main(pdfs))
