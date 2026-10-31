"""Number grounding tests (A22): invented figures are rejected.

The extraction and matching rules are pinned on small strings; the
impact tests then show an invented figure discards the model prose,
while the stored live Muse Wonder run passes untouched.
"""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app import grounding, impact
from app.config import REPO_ROOT, Settings
from app.order_store import get_detail, reset
from app.schemas import Event

STORED_RUN = REPO_ROOT / "data" / "extractions" / "impact_ord-001.json"


def allowed(*values: object) -> list[grounding.Figure]:
    return grounding.tool_figures(values)


def raws(text: str) -> list[str]:
    return [figure.raw for figure in grounding.extract_figures(text)]


def test_extracts_money_percent_numbers_and_dates() -> None:
    text = "Pay $1,100.00 to arrive 2027-01-01 (Jan 1, 2027) at 8.79% on a 60-day term."
    assert raws(text) == ["2027-01-01", "Jan 1, 2027", "$1,100.00", "8.79%", "60"]


def test_identifiers_are_not_figures() -> None:
    assert raws("ORD-001 on PO-001, event EVT-7b36d6f9, part PTB8850LS41") == []


def test_tool_figure_passes_exactly_and_reformatted() -> None:
    tools = allowed({"landed_cost": "82070.00", "margin_pct": "10.00"})
    assert grounding.check("Landed cost $82,070 at 10% margin.", tools).grounded


def test_invented_number_is_rejected() -> None:
    """The A22 acceptance test: a figure no tool returned fails the check."""
    tools = allowed({"expedite_cost": "1100.00", "margin_pct": "8.79"})
    result = grounding.check("Expedite for $1,450 to hold 8.79% margin.", tools)
    assert not result.grounded
    assert result.ungrounded == ["$1,450"]


def test_rounding_needs_a_decimal_place() -> None:
    tools = allowed({"margin_pct": "8.79"})
    assert grounding.check("Margin falls to 8.8%.", tools).grounded
    assert not grounding.check("Margin falls to 9%.", tools).grounded


def test_dates_must_match_a_tool_date() -> None:
    tools = allowed({"arrival_date": "2027-01-03"})
    assert grounding.check("It now arrives Jan 3.", tools).grounded
    assert grounding.check("It now arrives 1/3/2027 in 2027.", tools).grounded
    result = grounding.check("It now arrives Jan 5, 2027.", tools)
    assert result.ungrounded == ["Jan 5, 2027"]


def test_figures_inside_tool_text_count() -> None:
    """Flag messages are tool output too; their numbers may be repeated."""
    tools = allowed({"flags": ["Deposit 41035.00 due with PO-001 before delivery."]})
    assert grounding.check("The $41,035.00 deposit is still due.", tools).grounded


def delayed_store() -> None:
    """ORD-001 after the Tallgrass email: ships Dec 31, arrives Jan 3."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    detail.events.append(
        Event(
            event_id="EVT-test",
            order_id="ORD-001",
            source="email",
            summary="Tallgrass backorder.",
            supplier="Tallgrass Horticultural Supply",
            new_ship_date=date(2026, 12, 31),
            confidence=1.0,
        )
    )
    detail.shipments[0].ship_date = date(2026, 12, 31)
    detail.shipments[0].arrival_date = date(2027, 1, 3)


def settings() -> Settings:
    return Settings(
        model_api_key="test", model_read="muse-spark-1.3", model_impact="muse-wonder-1.0"
    )


def test_stored_live_run_is_grounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real Muse Wonder output stored by A21 passes and is kept verbatim."""
    stored = json.loads(Path(STORED_RUN).read_text(encoding="utf-8"))
    summaries = {opt["name"]: opt["summary"] for opt in stored["options"]}
    delayed_store()
    monkeypatch.setattr(
        impact, "_request", lambda *_: {"summaries": summaries, "note": stored["note"]}
    )
    analysis = impact.analyze("ORD-001", settings())
    assert analysis.grounded, analysis.ungrounded_figures
    assert analysis.note == stored["note"]
    assert analysis.options[0].summary == summaries["expedite_overnight"]


def test_invented_figure_discards_all_model_prose(monkeypatch: pytest.MonkeyPatch) -> None:
    """One invented figure: summaries become code sentences, note the rule flags."""
    delayed_store()
    invented = {
        "summaries": {
            "expedite_overnight": "Overnight freight costs $1,450 and arrives on time.",
            "request_extension": "Ask the CO for more time.",
            "partial_shipment": "Ship what is ready if allowed.",
            "switch_supplier": "No compliant alternate.",
        },
        "note": "Expedite.",
    }
    monkeypatch.setattr(impact, "_request", lambda *_: invented)
    analysis = impact.analyze("ORD-001", settings())
    assert not analysis.grounded
    assert analysis.ungrounded_figures == ["$1,450"]
    assert analysis.generated_by == "muse-wonder-1.0"
    expedite = analysis.options[0]
    assert "$1,450" not in expedite.summary
    assert expedite.summary.startswith("Expedite overnight; adds $1,100.00; margin 8.79%")
    assert expedite.new_margin_pct == Decimal("8.79")
    assert analysis.note == (
        "Rule-based flags: Arrival 2027-01-03 is 2 days late (due 2027-01-01); "
        "Deposit 41035.00 due with PO-001 before delivery."
    )


def test_days_late_is_a_tool_figure() -> None:
    """The model may say "2 days late" because code computed it."""
    delayed_store()
    assert impact.order_facts("ORD-001")["days_late"] == 2
