"""Record the scripted Ask KounOS answer for replay (A24).

Usage (from api/): python scripts/record_ask.py

Resets the demo orders, ingests the pre-demo Tallgrass backorder email, then
asks MODEL_READ "Which orders need attention today?" as of 2026-11-04
(submission day). When the answer is grounded, the full AskAnswer is stored
under data/extractions/ and the replay record under data/replay/.
"""

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import app.main
from app import ask
from app.config import REPO_ROOT, get_settings

QUESTION = "Which orders need attention today?"
AS_OF = date(2026, 11, 4)
EXTRACTION_PATH = REPO_ROOT / "data" / "extractions" / "ask_attention.json"
REPLAY_PATH = REPO_ROOT / "data" / "replay" / "ask_attention.json"
STATE = "seed reset + tallgrass_backorder.txt ingested"


def main() -> int:
    """Reset, ingest, ask and store the grounded answer. Returns exit code."""
    settings = get_settings()
    if not settings.model_api_key:
        print("MODEL_API_KEY is not set (repo-root .env).", file=sys.stderr)
        return 2
    client = TestClient(app.main.app)
    reset = client.post("/demo/reset")
    reset.raise_for_status()
    ingested = client.post(
        "/events/ingest",
        json={
            "order_id": "ORD-001",
            "source": "email",
            "filename": "tallgrass_backorder.txt",
        },
    )
    ingested.raise_for_status()
    live = settings.model_copy(update={"demo_mode": "live", "demo_today": AS_OF})
    result = ask.answer(QUESTION, live)
    if not result.grounded:
        print("Answer is not grounded; writing nothing.", file=sys.stderr)
        print(f"ungrounded_figures: {result.ungrounded_figures}", file=sys.stderr)
        print(f"unknown_records: {result.unknown_records}", file=sys.stderr)
        return 1
    EXTRACTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    extraction = result.model_dump(mode="json")
    extraction["recorded_at"] = datetime.now(timezone.utc).isoformat()
    extraction["state"] = STATE
    EXTRACTION_PATH.write_text(
        json.dumps(extraction, indent=2) + "\n", encoding="utf-8"
    )
    replay = {
        "source": "data/extractions/ask_attention.json",
        "model": result.generated_by,
        "as_of": AS_OF.isoformat(),
        "response": {
            "tool_calls": [call.model_dump(mode="json") for call in result.tool_calls],
            "answer": result.answer,
        },
    }
    REPLAY_PATH.write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    print(result.answer)
    for call in result.tool_calls:
        print(f"{call.name} {json.dumps(call.arguments)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
