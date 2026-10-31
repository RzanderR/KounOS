"""Delay impact analysis (A21): read-only tools price options, a model explains.

Code computes every figure from the seed, the demo quotes and the cost
engine; the model only writes the per-option summaries and the overall
note. Every tool below only reads: nothing here mutates an order, an
event or a shipment. Uses MODEL_IMPACT, falling back to MODEL_READ when
the impact model is unavailable.
"""

import json
from datetime import date
from decimal import Decimal

from openai import OpenAI

from app import costs, grounding, order_store
from app.checks import demo_verdicts
from app.config import Settings
from app.rules import evaluate
from app.schemas import ImpactAnalysis, ImpactOption, OrderDetail

# Demo assumption: overnight freight to pull the Tallgrass shipment back
# to an on-time arrival. Priced in code so the margin math stays exact.
EXPEDITE_OVERNIGHT = Decimal("1100.00")

OPTION_NAMES = (
    "expedite_overnight",
    "request_extension",
    "partial_shipment",
    "switch_supplier",
)

OPTION_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "summaries": {
            "type": "object",
            "properties": {name: {"type": "string"} for name in OPTION_NAMES},
            "required": list(OPTION_NAMES),
            "additionalProperties": False,
        },
        "note": {"type": "string"},
    },
    "required": ["summaries", "note"],
    "additionalProperties": False,
}

ANALYSIS_PROMPT = (
    "You are KounOS explaining a supplier delay to a small government "
    "supplier. Using ONLY the figures in the tool output below, write one "
    "plain sentence per recovery option (expedite_overnight, "
    "request_extension, partial_shipment, switch_supplier) and a one-line "
    "overall note. Never invent a number: repeat the figures exactly; "
    "never invent ids, lots, units, parties or tool chatter — the note "
    "is one sentence recommending exactly one of the four options above "
    "using its figures, and the switch_supplier sentence must name the "
    "failing suppliers from its context line. "
    "Return only JSON matching the schema."
)


def _detail(order_id: str) -> OrderDetail:
    """The order or a 404-style ValueError for the router to translate."""
    detail = order_store.get_detail(order_id)
    if detail is None:
        raise ValueError(f"Unknown order: {order_id}.")
    return detail


def order_facts(order_id: str) -> dict[str, object]:
    """Read-only facts the analysis may cite: money, dates, flags."""
    detail = _detail(order_id)
    order = detail.order
    bid = order.bid_price or Decimal("0")
    landed = order.landed_cost or Decimal("0")
    invoice_balance = sum(
        (inv.amount for inv in detail.invoices if not inv.paid), Decimal("0")
    )
    ship = detail.shipments[0] if detail.shipments else None
    return {
        "order_id": order.order_id,
        "supplier": order.supplier,
        "bid_price": str(bid),
        "landed_cost": str(landed),
        "margin_pct": str(costs.margin_at_price(landed, bid)) if bid > 0 else None,
        "customer_due_date": order.customer_due_date.isoformat()
        if order.customer_due_date
        else None,
        "po_amount": str(detail.po.amount) if detail.po else None,
        "deposit_due": str(detail.po.deposit_due) if detail.po else None,
        "invoice_balance": str(invoice_balance),
        "ship_date": ship.ship_date.isoformat() if ship and ship.ship_date else None,
        "arrival_date": ship.arrival_date.isoformat()
        if ship and ship.arrival_date
        else None,
        "days_late": (ship.arrival_date - order.customer_due_date).days
        if ship
        and ship.arrival_date
        and order.customer_due_date
        and ship.arrival_date > order.customer_due_date
        else 0,
        "flags": [flag.message for flag in evaluate(detail)],
    }


def priced_options(order_id: str) -> list[ImpactOption]:
    """The four recovery options with code-computed figures (A21)."""
    detail = _detail(order_id)
    order = detail.order
    bid = order.bid_price or Decimal("0")
    landed = order.landed_cost or Decimal("0")
    due = order.customer_due_date
    ship = detail.shipments[0] if detail.shipments else None
    arrival = ship.arrival_date if ship else None

    expedite_landed = landed + EXPEDITE_OVERNIGHT
    expedite = ImpactOption(
        name="expedite_overnight",
        summary="",
        cost_delta=EXPEDITE_OVERNIGHT,
        new_margin_pct=costs.margin_at_price(expedite_landed, bid),
        new_arrival_date=due,
        on_time=True,
    )
    extension = ImpactOption(
        name="request_extension",
        summary="",
        cost_delta=Decimal("0"),
        new_margin_pct=costs.margin_at_price(landed, bid),
        new_arrival_date=arrival,
        on_time=False,
    )
    partial = ImpactOption(
        name="partial_shipment",
        summary="",
        cost_delta=Decimal("0"),
        new_margin_pct=None,
        new_arrival_date=None,
        on_time=False,
        needs_confirmation=True,
    )
    failures = "; ".join(
        f"{verdict.supplier} fails "
        + ", ".join(
            check.reason.rstrip(".")
            for check in verdict.checks
            if check.verdict == "fail"
        )
        for verdict in demo_verdicts()
        if verdict.overall == "fail"
    )
    switch = ImpactOption(
        name="switch_supplier",
        summary=f"No compliant alternate: {failures}." if failures else "",
        cost_delta=Decimal("0"),
        new_margin_pct=None,
        new_arrival_date=None,
        on_time=False,
    )
    return [expedite, extension, partial, switch]


def _request(model: str, prompt: str, settings: Settings) -> dict[str, object]:
    """One strict-schema MODEL call returning parsed JSON."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
        text={
            "format": {
                "type": "json_schema",
                "name": "impact_analysis",
                "schema": OPTION_SCHEMA,
                "strict": True,
            }
        },
    )
    parsed: dict[str, object] = json.loads(response.output_text)
    return parsed


def plain_summary(option: ImpactOption) -> str:
    """A code-written sentence for one option, used when model prose is rejected."""
    parts = [option.name.replace("_", " ").capitalize()]
    if option.cost_delta:
        parts.append(f"adds ${option.cost_delta:,.2f}")
    if option.new_margin_pct is not None:
        parts.append(f"margin {option.new_margin_pct}%")
    if option.new_arrival_date is not None:
        timing = "on time" if option.on_time else "late"
        parts.append(f"arrives {option.new_arrival_date.isoformat()} ({timing})")
    if option.needs_confirmation:
        parts.append("needs confirmation before use")
    sentence = "; ".join(parts) + "."
    return f"{sentence} {option.summary}" if option.summary else sentence


def ground(
    summaries: dict[str, str], note: str, allowed: list[grounding.Figure]
) -> list[str]:
    """Every figure in the model prose that no tool returned (A22)."""
    ungrounded: list[str] = []
    for text in [*summaries.values(), note]:
        ungrounded.extend(grounding.check(text, allowed).ungrounded)
    return ungrounded


def analyze(order_id: str, settings: Settings) -> ImpactAnalysis:
    """Price the options in code, have the model explain them.

    Figures always come from :func:`priced_options`; the model contributes
    only the summaries and the note. Falls back to MODEL_READ when
    MODEL_IMPACT is unavailable.
    """
    detail = _detail(order_id)
    facts = order_facts(order_id)
    options = priced_options(order_id)
    prompt = (
        f"{ANALYSIS_PROMPT}\n\nTool output:\n{json.dumps(facts, indent=2)}"
        f"\n\nPriced options:\n"
        + "\n".join(
            f"- {opt.name}: cost_delta {opt.cost_delta}, "
            f"new_margin_pct {opt.new_margin_pct}, "
            f"new_arrival_date {opt.new_arrival_date}, "
            f"on_time {opt.on_time}"
            + (f". Context: {opt.summary}" if opt.summary else "")
            for opt in options
        )
    )
    try:
        raw = _request(settings.model_impact, prompt, settings)
        used = settings.model_impact
    except Exception:
        raw = _request(settings.model_read, prompt, settings)
        used = settings.model_read
    summaries = raw.get("summaries")
    if not isinstance(summaries, dict):
        raise ValueError(f"Impact model returned no summaries: {raw!r}.")
    note = raw.get("note")
    if not isinstance(note, str):
        raise ValueError(f"Impact model returned no note: {raw!r}.")
    prose = {name: str(summaries.get(name) or "") for name in OPTION_NAMES}
    allowed = grounding.tool_figures([facts, [opt.model_dump() for opt in options]])
    ungrounded = ground(prose, note, allowed)
    if ungrounded:
        # Discard all model prose: code-written sentences and the rule flags.
        raw_flags = facts["flags"]
        flags = [str(flag) for flag in raw_flags] if isinstance(raw_flags, list) else []
        prose = {opt.name: plain_summary(opt) for opt in options}
        note = (
            "Rule-based flags: " + "; ".join(flag.rstrip(".") for flag in flags) + "."
            if flags
            else "No rule-based flags."
        )
    latest_event = detail.events[-1].event_id if detail.events else None
    return ImpactAnalysis(
        order_id=order_id,
        event_id=latest_event,
        generated_by=used,
        options=[
            ImpactOption(
                name=opt.name,
                summary=prose[opt.name] or opt.summary,
                cost_delta=opt.cost_delta,
                new_margin_pct=opt.new_margin_pct,
                new_arrival_date=opt.new_arrival_date,
                on_time=opt.on_time,
                needs_confirmation=opt.needs_confirmation,
            )
            for opt in options
        ],
        note=note,
        grounded=not ungrounded,
        ungrounded_figures=ungrounded,
    )


def current_arrival(order_id: str) -> date | None:
    """The order's first shipment arrival, for ripple math (A39 helper)."""
    detail = _detail(order_id)
    if not detail.shipments or detail.shipments[0].arrival_date is None:
        return None
    return detail.shipments[0].arrival_date
