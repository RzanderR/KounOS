"""Ask KounOS tests (A24): code decides attention, the model only phrases it.

No test here calls a model: ``ask._call_model`` is faked with scripted
Responses API output items.
"""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import ask, replay
from app.config import Settings, get_settings
from app.main import app
from app.order_store import get_detail, list_orders, reset
from app.schemas import Invoice, OrderDetail, Shipment

client = TestClient(app)
TODAY = date(2026, 11, 2)
GOOD = (
    "Three orders need attention. ORD-001 has deposit 41035.00 due with PO-001. "
    "ORD-003 has invoice INV-003 for 18750.00 due 2026-11-03. ORD-004 has shipment "
    "SHP-004B with no arrival date yet."
)


def make_settings(**overrides: Any) -> Settings:
    """Explicit settings so the repo-root .env can never skew the tests."""
    values: dict[str, Any] = {
        "model_api_key": "test",
        "model_read": "muse-spark-1.3",
        "demo_mode": "live",
        "demo_today": TODAY,
    }
    values.update(overrides)
    return Settings(**values)


def call(name: str, arguments: dict[str, str], call_id: str) -> dict[str, Any]:
    return {"type": "function_call", "name": name, "arguments": json.dumps(arguments),
            "call_id": call_id}


def message(text: str) -> dict[str, Any]:
    return {"type": "message", "content": [{"type": "output_text", "text": text}]}


def scripted(*rounds: list[dict[str, Any]]) -> Any:
    """A fake model that returns each round's output items in turn."""
    queue = list(rounds)
    seen: list[list[dict[str, Any]]] = []

    def fake(model: str, items: list[dict[str, Any]], settings: Settings) -> list[dict[str, Any]]:
        seen.append(list(items))
        return queue.pop(0)

    fake.seen = seen  # type: ignore[attr-defined]
    return fake


@pytest.fixture(autouse=True)
def fresh_store() -> Any:
    reset()
    yield
    reset()
    app.dependency_overrides.clear()


def snapshot() -> dict[str, object]:
    return {
        order.order_id: detail.model_dump()
        for order in list_orders()
        if (detail := get_detail(order.order_id)) is not None
    }


def detail_with(invoices: list[Invoice], shipments: list[Shipment], status: str) -> OrderDetail:
    base = get_detail("ORD-005")
    assert base is not None
    return base.model_copy(
        update={
            "invoices": invoices,
            "shipments": shipments,
            "order": base.order.model_copy(update={"status": status}),
            "po": None,
        }
    )


def invoice(invoice_id: str, due: date, paid: bool = False) -> Invoice:
    return Invoice(invoice_id=invoice_id, order_id="ORD-005", amount=Decimal("100.00"),
                   due_date=due, paid=paid)


def test_attention_invoice_window() -> None:
    detail = detail_with(
        [
            invoice("INV-A", date(2026, 10, 30)),
            invoice("INV-B", TODAY),
            invoice("INV-C", date(2026, 11, 3)),
            invoice("INV-D", date(2026, 11, 9)),
            invoice("INV-E", date(2026, 11, 10)),
            invoice("INV-F", date(2026, 10, 1), paid=True),
        ],
        [],
        "placed",
    )
    reasons = ask.attention(detail, TODAY)
    assert reasons == [
        "Invoice INV-A for 100.00 is 3 days overdue (due 2026-10-30).",
        "Invoice INV-B for 100.00 is due today (2026-11-02).",
        "Invoice INV-C for 100.00 is due in 1 day (2026-11-03).",
        "Invoice INV-D for 100.00 is due in 7 days (2026-11-09).",
    ]


def test_attention_undated_shipment_unless_delivered() -> None:
    shipment = Shipment(shipment_id="SHP-X", order_id="ORD-005", ship_date=TODAY,
                        arrival_date=None)
    assert ask.attention(detail_with([], [shipment], "placed"), TODAY) == [
        "Shipment SHP-X (ship date 2026-11-02) has no arrival date yet."
    ]
    assert ask.attention(detail_with([], [shipment], "delivered"), TODAY) == []


def test_seeded_attention_today() -> None:
    orders = {o["order_id"]: o["attention"] for o in ask.list_orders_tool(TODAY)["orders"]}  # type: ignore[attr-defined]
    assert [oid for oid, reasons in orders.items() if reasons] == ["ORD-001", "ORD-003", "ORD-004"]


def test_tool_loop_grounded_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = scripted([call("list_orders", {}, "c1")], [message(GOOD)])
    monkeypatch.setattr(ask, "_call_model", fake)
    before = snapshot()
    result = ask.answer("Which orders need attention today?", make_settings())
    assert snapshot() == before, "tools must only read"
    assert result.grounded
    assert result.answer == GOOD
    assert result.generated_by == "muse-spark-1.3"
    assert [c.name for c in result.tool_calls] == ["list_orders"]
    assert [(r.record_id, r.kind, r.order_id) for r in result.records] == [
        ("ORD-001", "order", "ORD-001"),
        ("PO-001", "po", "ORD-001"),
        ("ORD-003", "order", "ORD-003"),
        ("INV-003", "invoice", "ORD-003"),
        ("ORD-004", "order", "ORD-004"),
        ("SHP-004B", "shipment", "ORD-004"),
    ]
    # The tool result went back to the model under the same call id.
    second = fake.seen[1]
    outputs = [item for item in second if item.get("type") == "function_call_output"]
    assert outputs and outputs[0]["call_id"] == "c1"
    assert "ORD-003" in outputs[0]["output"]


def test_get_order_tool_round(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = scripted(
        [call("list_orders", {}, "c1")],
        [call("get_order", {"order_id": "ORD-004"}, "c2")],
        [message("ORD-004 shipment SHP-004B left 2026-11-05 with no arrival date.")],
    )
    monkeypatch.setattr(ask, "_call_model", fake)
    result = ask.answer("What is going on with ORD-004?", make_settings())
    assert result.grounded
    assert [(c.name, c.arguments) for c in result.tool_calls] == [
        ("list_orders", {}),
        ("get_order", {"order_id": "ORD-004"}),
    ]


def test_invented_figure_is_withheld(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = scripted([call("list_orders", {}, "c1")],
                    [message("ORD-003 owes $99,999 by 2026-11-03.")])
    monkeypatch.setattr(ask, "_call_model", fake)
    result = ask.answer("Which orders need attention today?", make_settings())
    assert not result.grounded
    assert result.ungrounded_figures == ["$99,999"]
    assert result.answer == ask.code_answer(TODAY)
    assert {r.record_id for r in result.records} >= {"ORD-001", "INV-003", "SHP-004B"}


def test_unknown_record_is_withheld(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = scripted([call("list_orders", {}, "c1")], [message("ORD-999 is late.")])
    monkeypatch.setattr(ask, "_call_model", fake)
    result = ask.answer("Which orders need attention today?", make_settings())
    assert not result.grounded
    assert result.unknown_records == ["ORD-999"]


def test_answer_without_tool_calls_is_withheld(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ask, "_call_model", scripted([message("ORD-003 needs attention.")]))
    result = ask.answer("Which orders need attention today?", make_settings())
    assert not result.grounded
    assert result.unknown_records == ["ORD-003"]


def test_unknown_tool_and_order_answer_with_errors() -> None:
    assert ask.run_tool("delete_order", {}, TODAY) == {"error": "Unknown tool: delete_order."}
    assert ask.run_tool("get_order", {"order_id": "ORD-999"}, TODAY) == {
        "error": "Unknown order: ORD-999."
    }


def test_route_502_when_model_never_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    rounds = [[call("list_orders", {}, f"c{i}")] for i in range(ask.MAX_ROUNDS)]
    monkeypatch.setattr(ask, "_call_model", scripted(*rounds))
    app.dependency_overrides[get_settings] = lambda: make_settings()
    response = client.post("/ask", json={"question": "Which orders need attention today?"})
    assert response.status_code == 502
    assert "kept calling tools" in response.json()["detail"]


def test_route_502_on_empty_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ask, "_call_model", scripted([message("  ")]))
    app.dependency_overrides[get_settings] = lambda: make_settings()
    response = client.post("/ask", json={"question": "Anything?"})
    assert response.status_code == 502


def test_route_503_without_model_key() -> None:
    app.dependency_overrides[get_settings] = lambda: make_settings(model_api_key=None)
    response = client.post("/ask", json={"question": "Which orders need attention today?"})
    assert response.status_code == 503
    assert "MODEL_API_KEY" in response.json()["detail"]


def test_route_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ask, "_call_model", scripted([call("list_orders", {}, "c1")],
                                                     [message(GOOD)]))
    app.dependency_overrides[get_settings] = lambda: make_settings()
    response = client.post("/ask", json={"question": "Which orders need attention today?"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["as_of"] == "2026-11-02"


def write_replay(directory: Path) -> None:
    record = {
        "model": "muse-spark-1.3",
        "as_of": "2026-11-04",
        "response": {"tool_calls": [{"name": "list_orders", "arguments": {}}], "answer": GOOD},
    }
    (directory / f"{ask.REPLAY_NAME}.json").write_text(json.dumps(record), encoding="utf-8")


def test_replay_scripted_question(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    write_replay(tmp_path)
    monkeypatch.setattr(replay, "REPLAY_DIR", tmp_path)

    def no_model(*_: object) -> list[dict[str, Any]]:
        raise AssertionError("replay must not call a model")

    monkeypatch.setattr(ask, "_call_model", no_model)
    settings = make_settings(demo_mode="replay", model_api_key=None)
    result = ask.answer("  which orders need attention today ", settings)
    assert result.grounded
    assert result.generated_by == "muse-spark-1.3 (replay)"
    assert [c.name for c in result.tool_calls] == ["list_orders"]


def test_replay_uses_recorded_date(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    write_replay(tmp_path)
    monkeypatch.setattr(replay, "REPLAY_DIR", tmp_path)

    def no_model(*_: object) -> list[dict[str, Any]]:
        raise AssertionError("replay must not call a model")

    monkeypatch.setattr(ask, "_call_model", no_model)
    settings = make_settings(demo_mode="replay", model_api_key=None, demo_today=None)
    result = ask.answer("Which orders need attention today?", settings)
    assert result.as_of == date(2026, 11, 4)


def test_replay_other_question_503(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    write_replay(tmp_path)
    monkeypatch.setattr(replay, "REPLAY_DIR", tmp_path)
    app.dependency_overrides[get_settings] = lambda: make_settings(demo_mode="replay")
    response = client.post("/ask", json={"question": "What is ORD-004's status?"})
    assert response.status_code == 503
