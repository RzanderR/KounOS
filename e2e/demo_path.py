"""End-to-end demo-path test (A20): reset to delay flag, in a real browser.

Flow: POST /demo/reset, ingest the H09 voicemail, then open the order in
headless system Chrome and assert the Simulated-award banner, the moved
shipment and the blocking delay flag are on screen.

Needs: API on :8000, web on :3000, data/voicemail/tallgrass_backorder.m4a
(H09) and MODEL_API_KEY for transcription + extraction.
Run (from repo root): python e2e/demo_path.py
"""

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://localhost:8000"
WEB = "http://localhost:3000"
ORDER = "ORD-001"
AUDIO = "tallgrass_backorder.m4a"


def api(method: str, path: str, body: object = None) -> object:
    """One JSON API call; raises on HTTP error."""
    import json

    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def main() -> int:
    reset = api("POST", "/demo/reset")
    assert reset == {"orders": 5}, reset
    print("reset: 5 orders")

    audio = ROOT / "data" / "voicemail" / AUDIO
    if not audio.is_file():
        print(f"missing H09 audio: {audio} — record it, then re-run")
        return 2
    event = api(
        "POST",
        "/events/ingest",
        {"order_id": ORDER, "source": "voicemail", "filename": AUDIO},
    )
    assert isinstance(event, dict)
    print(f"event: {event['event_id']} ship {event['new_ship_date']}")

    flags = api("GET", "/events/flags")
    assert isinstance(flags, list)
    delay = [f for f in flags if f["order_id"] == ORDER and f["code"] == "delivery-slip"]
    assert delay and "2 days late" in delay[0]["message"], flags
    print(f"flag: {delay[0]['message']}")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="chrome", headless=True
        )
        page = browser.new_page()
        page.goto(f"{WEB}/orders/{ORDER}", wait_until="networkidle")
        body = page.text_content("main") or ""
        assert "Simulated award" in body, "banner missing"
        assert "2 days late" in body, "flag missing on screen"
        assert "2027-01-03" in body, "moved arrival missing on screen"
        browser.close()
    print("browser: banner, flag and arrival on screen — demo path green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
