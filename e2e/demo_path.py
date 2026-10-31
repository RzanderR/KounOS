"""End-to-end demo-path test (A20): badge highlight to delay flag.

Stages (each browser gets a fresh context: clean profile, no cache —
the equivalent of a hard refresh):
1. Solicitation: click the line-0001 badge, assert the PDF page renders
   (a canvas) with highlight boxes and no viewer error; then click the
   line-1001 badge (same PDF, served from the viewer byte cache) and
   assert it renders too with no console or page errors — this pins the
   detached-ArrayBuffer regression.
2. Orders list shows the Simulated-award banner.
3. Delay path (email backup, no voicemail): reset, ingest
   data/voicemail/tallgrass_backorder.txt, assert the blocking
   2-days-late flag via API.

Needs: API on :8000, web on :3000, MODEL_API_KEY for stage 3.
Run (from repo root): python e2e/demo_path.py [--browser chrome|firefox|all]
"""

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://localhost:8000"
WEB = "http://localhost:3000"
ORDER = "ORD-001"
EMAIL = "tallgrass_backorder.txt"


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
    """Two badge clicks render with highlights and no errors."""
    from playwright.sync_api import sync_playwright

    problems: list[str] = []
    with sync_playwright() as playwright:
        if browser_name == "firefox":
            browser = playwright.firefox.launch(headless=True)
        else:
            browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: problems.append(str(e)))
        page.goto(f"{WEB}/solicitation", wait_until="networkidle")
        page.get_by_role("button", name="Show citation for line 0001").click()
        page.wait_for_selector("canvas", timeout=30000)
        highlights = page.locator("div.border-yellow-500").count()
        assert highlights > 0, f"[{browser_name}] no highlight boxes on the row"
        viewer = page.get_by_label("Passage viewer")
        assert viewer.count() > 0, f"[{browser_name}] passage viewer missing"
        errors = viewer.get_by_role("alert").count()
        assert errors == 0, f"[{browser_name}] viewer error shown"
        print(f"[{browser_name}] badge click: canvas + {highlights} highlights, no error")
        problems.clear()
        page.get_by_role("button", name="Show citation for line 1001").click()
        page.wait_for_timeout(5000)
        assert page.locator("canvas").count() > 0, f"[{browser_name}] no canvas after second click"
        highlights2 = page.locator("div.border-yellow-500").count()
        assert highlights2 > 0, f"[{browser_name}] no highlights after second click"
        assert not problems, f"[{browser_name}] errors after second click: {problems[:3]}"
        print(f"[{browser_name}] second badge: canvas + {highlights2} highlights, no errors")
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


def check_delay_path() -> None:
    """Ingest the backup email and assert the delay flag."""
    reset = api("POST", "/demo/reset")
    assert reset == {"orders": 5}, reset
    print("reset: 5 orders")

    email = ROOT / "data" / "voicemail" / EMAIL
    assert email.is_file(), f"missing backup email: {email}"
    event = api(
        "POST",
        "/events/ingest",
        {"order_id": ORDER, "source": "email", "filename": EMAIL},
    )
    assert isinstance(event, dict)
    print(f"event: {event['event_id']} ship {event['new_ship_date']}")

    flags = api("GET", "/events/flags")
    assert isinstance(flags, list)
    delay = [f for f in flags if f["order_id"] == ORDER and f["code"] == "delivery-slip"]
    assert delay and "2 days late" in delay[0]["message"], flags
    print(f"flag: {delay[0]['message']}")


def main(browsers: list[str]) -> int:
    for browser_name in browsers:
        check_solicitation(browser_name)
        check_orders_banner(browser_name)
    check_delay_path()
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
