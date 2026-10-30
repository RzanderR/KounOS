"""End-to-end demo-path test (A20): badge highlight to delay flag.

Stages (each browser gets a fresh context: clean profile, no cache —
the equivalent of a hard refresh):
1. Solicitation: click the line-0001 badge, assert the PDF page renders
   (a canvas) with highlight boxes and no viewer error.
2. Orders list shows the Simulated-award banner.
3. Delay path (needs H09 audio): ingest the voicemail, assert the
   blocking 2-days-late flag via API and on the order page.

Needs: API on :8000, web on :3000. Stage 3 additionally needs
data/voicemail/tallgrass_backorder.m4a (H09) and MODEL_API_KEY.
Run (from repo root): python e2e/demo_path.py [--browser chrome|firefox|all]
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


def check_solicitation(browser_name: str) -> None:
    """Badge click renders the PDF page with highlights, no error."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        if browser_name == "firefox":
            browser = playwright.firefox.launch(headless=True)
        else:
            browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{WEB}/solicitation", wait_until="networkidle")
        page.get_by_role("button", name="Show citation for line 0001").click()
        page.wait_for_selector("canvas", timeout=30000)
        highlights = page.locator("div.border-yellow-500").count()
        assert highlights > 0, f"[{browser_name}] no highlight boxes on the row"
        errors = page.get_by_role("alert").count()
        assert errors == 0, f"[{browser_name}] viewer error shown"
        print(f"[{browser_name}] badge click: canvas + {highlights} highlights, no error")
        context.close()
        browser.close()


def check_orders_banner(browser_name: str) -> None:
    """The orders list shows the Simulated-award banner."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        if browser_name == "firefox":
            browser = playwright.firefox.launch(headless=True)
        else:
            browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{WEB}/orders", wait_until="networkidle")
        body = page.text_content("main") or ""
        assert "Simulated award" in body, f"[{browser_name}] banner missing"
        print(f"[{browser_name}] orders banner on screen")
        context.close()
        browser.close()


def check_delay_path() -> bool:
    """Ingest the voicemail and assert the delay flag (needs H09 audio)."""
    reset = api("POST", "/demo/reset")
    assert reset == {"orders": 5}, reset
    print("reset: 5 orders")

    audio = ROOT / "data" / "voicemail" / AUDIO
    if not audio.is_file():
        print(f"missing H09 audio: {audio} — record it, then re-run")
        return False
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
    return True


def main(browsers: list[str]) -> int:
    for browser_name in browsers:
        check_solicitation(browser_name)
        check_orders_banner(browser_name)
    if not check_delay_path():
        print("browser stages green; delay path waits for H09 audio")
        return 2
    print("demo path green end to end")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--browser=all"
    if arg == "--browser=chrome":
        chosen = ["chrome"]
    elif arg == "--browser=firefox":
        chosen = ["firefox"]
    else:
        chosen = ["chrome", "firefox"]
    raise SystemExit(main(chosen))
