"""Run triage fit extraction (A34) and print the validated result.

Usage (from api/): python scripts/extract_fit.py [notice.pdf ...]
Defaults to every PDF under data/notices/ (the H16 batch).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import REPO_ROOT, Settings
from app.fit import FitExtraction, cited_notice, extract_fit_facts


def main(pdf_paths: list[Path]) -> int:
    """Extract each notice, check its citations, print the Notice record."""
    settings = Settings()
    if not settings.model_api_key:
        print("MODEL_API_KEY is not set (repo-root .env).", file=sys.stderr)
        return 2
    for pdf_path in pdf_paths:
        extraction: FitExtraction = extract_fit_facts(pdf_path, settings)
        notice = cited_notice(pdf_path.stem, pdf_path, extraction)
        print(json.dumps(json.loads(notice.model_dump_json()), indent=2))
    return 0


if __name__ == "__main__":
    pdfs = [Path(arg) for arg in sys.argv[1:]]
    if not pdfs:
        notices = REPO_ROOT / "data" / "notices"
        pdfs = sorted(notices.glob("*.pdf")) if notices.is_dir() else []
    if not pdfs:
        print("No notice PDFs: the triage batch lands with H16.", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(pdfs))
