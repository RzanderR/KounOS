"""Contract-file lineage (A37): every figure resolves to a doc or a calc.

A doc figure names the source file (repo-relative) plus page and snippet
reusing the A06 citation data. A calc figure names the code function and
its inputs, reusing the A12 cost engine and A11 checks. Nothing here
calls a model: the solicitation builder re-checks stored output in code.

Event-sourced figures resolve to the ingest call that recorded them; file
linkage for those lands with the A39 ripple.
"""

import json
import re
from decimal import Decimal

from app import costs, order_store
from app.checks import demo_verdicts, load_quote_fixture
from app.compare import MARGIN_FLOOR
from app.config import REPO_ROOT, Settings
from app.demo_solicitation import ATTACHMENTS_DIR, build_demo_solicitation
from app.recommend import read_award
from app.schemas import (
    ContractFile,
    ContractSection,
    FigureLineage,
    LinkedFigure,
    OrderDetail,
)

QUOTE_ID = "tallgrass"


def doc(file: str, page: int | None = None, snippet: str | None = None) -> FigureLineage:
    """Lineage into a repo-relative source file.

    Stored citation refs are bare attachment names; resolve those against
    the solicitation attachments dir so the file always exists in-repo.
    """
    if "/" not in file and "\\" not in file and not (REPO_ROOT / file).is_file():
        candidate = ATTACHMENTS_DIR / file
        if candidate.is_file():
            file = str(candidate.relative_to(REPO_ROOT)).replace("\\", "/")
    return FigureLineage(kind="doc", file=file, page=page, snippet=snippet)


def calc(calculation: str, inputs: dict[str, str]) -> FigureLineage:
    """Lineage into a code function with its inputs."""
    return FigureLineage(kind="calc", calculation=calculation, inputs=inputs)


def _detail(order_id: str) -> OrderDetail:
    detail = order_store.get_detail(order_id)
    if detail is None:
        raise ValueError(f"Unknown order: {order_id}.")
    return detail


def requirement_figures(model_read: str) -> list[LinkedFigure]:
    """Quantities, part and delivery limit off the cited solicitation."""
    solicitation = build_demo_solicitation(model_read)
    figures: list[LinkedFigure] = []
    for req in solicitation.requirements:
        if req.source is None:
            continue
        figures.append(
            LinkedFigure(
                label=f"CLIN {req.line} quantity",
                value=f"{req.quantity} {req.unit}".strip(),
                lineage=doc(req.source.file, req.source.page, req.source.snippet),
            )
        )
        if req.part_or_nsn:
            figures.append(
                LinkedFigure(
                    label=f"CLIN {req.line} part",
                    value=req.part_or_nsn,
                    lineage=doc(req.source.file, req.source.page, req.source.snippet),
                )
            )
    for clause in solicitation.key_clauses:
        if clause.name == "delivery":
            match = re.search(r"within (\d+) days", clause.summary)
            if match:
                figures.append(
                    LinkedFigure(
                        label="Delivery limit",
                        value=f"{match.group(1)} days",
                        lineage=doc(
                            clause.source.file,
                            clause.source.page,
                            clause.source.snippet,
                        ),
                    )
                )
    return figures


def quote_figures() -> list[LinkedFigure]:
    """Tallgrass figures off the curated fixture plus live check verdicts."""
    quote = load_quote_fixture(QUOTE_ID)
    fixture = f"data/quotes/{QUOTE_ID}.json"
    figures = [
        LinkedFigure(
            label="Quoted unit price",
            value=str(quote.lines[0].unit_price),
            lineage=doc(fixture),
        ),
        LinkedFigure(
            label="Quoted freight",
            value=str(quote.freight),
            lineage=doc(fixture),
        ),
        LinkedFigure(
            label="Quoted total",
            value=str(quote.total),
            lineage=doc(fixture),
        ),
    ]
    for verdict in demo_verdicts():
        if verdict.supplier != quote.supplier:
            continue
        for check in verdict.checks:
            figures.append(
                LinkedFigure(
                    label=f"Tallgrass {check.check} check",
                    value=check.verdict,
                    lineage=calc(
                        "checks.check_quote",
                        {"supplier": verdict.supplier, "reason": check.reason},
                    ),
                )
            )
    return figures


def cost_figures() -> list[LinkedFigure]:
    """Landed cost, safe bid, margin and deposit off the cost engine."""
    quote = load_quote_fixture(QUOTE_ID)
    landed = costs.landed_cost(quote)
    per_unit, safe_bid = costs.lowest_safe_bid(quote, MARGIN_FLOOR)
    margin = costs.margin_at_price(landed, safe_bid)
    deposit = costs.deposit_due(quote.total, Decimal("0.5"))
    return [
        LinkedFigure(
            label="Landed cost",
            value=str(landed),
            lineage=calc(
                "costs.landed_cost",
                {"lines": "+".join(str(line.extended) for line in quote.lines),
                 "freight": str(quote.freight)},
            ),
        ),
        LinkedFigure(
            label="Landed per unit",
            value=str(costs.landed_per_unit(quote)),
            lineage=calc(
                "costs.landed_per_unit",
                {"landed": str(landed), "units": str(costs.total_units(quote))},
            ),
        ),
        LinkedFigure(
            label="Lowest safe bid",
            value=str(safe_bid),
            lineage=calc(
                "costs.lowest_safe_bid",
                {"per_unit": str(per_unit),
                 "units": str(costs.total_units(quote)),
                 "margin_floor": str(MARGIN_FLOOR)},
            ),
        ),
        LinkedFigure(
            label="Margin at safe bid",
            value=str(margin),
            lineage=calc(
                "costs.margin_at_price",
                {"landed": str(landed), "price": str(safe_bid)},
            ),
        ),
        LinkedFigure(
            label="Deposit due with PO",
            value=str(deposit),
            lineage=calc(
                "costs.deposit_due",
                {"quote_total": str(quote.total), "fraction": "0.5"},
            ),
        ),
    ]


def award_figures() -> list[LinkedFigure]:
    """The real award off data/awards."""
    award = read_award()
    raw = json.loads(
        (REPO_ROOT / "data" / "awards" / "1232SA26Q0557.json").read_text(
            encoding="utf-8"
        )
    )
    file = "data/awards/1232SA26Q0557.json"
    return [
        LinkedFigure(
            label="Award total",
            value=str(award.total),
            lineage=doc(file),
        ),
        LinkedFigure(
            label="Offers received",
            value=str(award.number_of_offers),
            lineage=doc(file),
        ),
        LinkedFigure(
            label="Award unit price",
            value=str(raw["unit_price_implied"]),
            lineage=doc(file),
        ),
        LinkedFigure(
            label="Award signed",
            value=award.date_signed.isoformat(),
            lineage=doc(file),
        ),
    ]


def order_figures(detail: OrderDetail) -> list[LinkedFigure]:
    """Order, PO, shipment and invoice figures off the seed record."""
    order = detail.order
    file = "data/orders/seed.json"
    figures = [
        LinkedFigure(label="Bid price", value=str(order.bid_price), lineage=doc(file)),
        LinkedFigure(
            label="Order landed cost", value=str(order.landed_cost), lineage=doc(file)
        ),
        LinkedFigure(
            label="Customer due date",
            value=order.customer_due_date.isoformat()
            if order.customer_due_date
            else "not stated",
            lineage=doc(file),
        ),
    ]
    if detail.po is not None:
        figures.append(
            LinkedFigure(
                label="PO amount", value=str(detail.po.amount), lineage=doc(file)
            )
        )
        figures.append(
            LinkedFigure(
                label="PO deposit due",
                value=str(detail.po.deposit_due),
                lineage=doc(file),
            )
        )
    if detail.shipments:
        ship = detail.shipments[0]
        figures.append(
            LinkedFigure(
                label="Ship date",
                value=ship.ship_date.isoformat() if ship.ship_date else "not stated",
                lineage=doc(file),
            )
        )
        figures.append(
            LinkedFigure(
                label="Arrival date",
                value=ship.arrival_date.isoformat()
                if ship.arrival_date
                else "not stated",
                lineage=doc(file),
            )
        )
    balance = sum(
        (inv.amount for inv in detail.invoices if not inv.paid), Decimal("0")
    )
    figures.append(
        LinkedFigure(label="Invoice balance", value=str(balance), lineage=doc(file))
    )
    return figures


def event_figures(detail: OrderDetail) -> list[LinkedFigure]:
    """Recorded events; file linkage for these lands with the A39 ripple."""
    figures = []
    for event in detail.events:
        if event.new_ship_date is None:
            continue
        figures.append(
            LinkedFigure(
                label=f"Event {event.event_id} new ship date",
                value=event.new_ship_date.isoformat(),
                lineage=calc(
                    "voicemail.ingest_file",
                    {"source": event.source, "event_id": event.event_id},
                ),
            )
        )
    return figures


def cash_figures(detail: OrderDetail) -> list[LinkedFigure]:
    """Cash tied up before the customer pays, off the PO and cost engine."""
    quote = load_quote_fixture(QUOTE_ID)
    file = "data/orders/seed.json"
    figures = [
        LinkedFigure(
            label="Cash exposure",
            value=str(costs.cash_exposure(quote)),
            lineage=calc(
                "costs.cash_exposure", {"landed": str(costs.landed_cost(quote))}
            ),
        )
    ]
    if detail.po is not None:
        figures.append(
            LinkedFigure(
                label="Deposit due with PO",
                value=str(detail.po.deposit_due),
                lineage=doc(file),
            )
        )
    return figures


def build_contract_file(order_id: str, settings: Settings) -> ContractFile:
    """The whole linked picture for one order, every figure resolved."""
    detail = _detail(order_id)
    return ContractFile(
        order_id=order_id,
        solicitation_id=detail.order.solicitation_id,
        sections=[
            ContractSection(
                name="requirements",
                figures=requirement_figures(settings.model_read),
            ),
            ContractSection(name="quotes", figures=quote_figures()),
            ContractSection(name="cost_bid", figures=cost_figures()),
            ContractSection(name="award", figures=award_figures()),
            ContractSection(name="order", figures=order_figures(detail)),
            ContractSection(name="events", figures=event_figures(detail)),
            ContractSection(name="cash", figures=cash_figures(detail)),
        ],
    )
