"""Shared Pydantic contracts for the KounOS API (A03).

These models are the single contract for extraction output (A05-A07),
quote intake (A10-A14), order monitoring (A16-A19) and triage (A34-A35).
Models read and explain; code computes. Money is always ``Decimal``.

``KeyClause`` is the one supporting type beyond the task list: a named
passage (delivery terms, sourcing rule, brand requirement) with its
citation, reused wherever a clause is referenced.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """Exact passage an extracted fact came from."""

    file: str
    page: int
    snippet: str


class WordBox(BaseModel):
    """One word and where it sits on its page (PDF points)."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float


class KeyClause(BaseModel):
    """A named clause or term with its cited passage."""

    name: str
    summary: str
    source: SourceRef
    citation_status: Literal["verified", "needs_review"] | None = None
    boxes: list[WordBox] = Field(default_factory=list)


class Requirement(BaseModel):
    """One line item or delivery term the solicitation asks for."""

    line: str
    description: str
    quantity: int
    unit: str
    part_or_nsn: str | None = None
    required_delivery: str | None = None
    source: SourceRef | None = None
    citation_status: Literal["verified", "needs_review"] | None = None
    boxes: list[WordBox] = Field(default_factory=list)


class PassageBytes(BaseModel):
    """Attachment bytes for the viewer, base64 inside JSON."""

    file: str
    data: str


class Solicitation(BaseModel):
    """A solicitation worth pursuing, with cited requirements and clauses."""

    solicitation_id: str
    title: str
    agency: str
    sub_agency: str | None = None
    set_aside: str | None = None
    naics: str | None = None
    response_deadline: datetime | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    key_clauses: list[KeyClause] = Field(default_factory=list)
    provenance_note: str | None = None


class CompanyProfile(BaseModel):
    """Everything company-specific. Code never hardcodes these values."""

    company_name: str
    set_aside_certifications: list[str] = Field(default_factory=list)
    naics_codes: list[str] = Field(default_factory=list)
    product_categories: list[str] = Field(default_factory=list)
    demo_margin_floor: Decimal


class Notice(BaseModel):
    """One triage-batch notice, as extracted (A34). Missing facts stay None."""

    notice_id: str
    title: str
    agency: str
    set_aside: str | None = None
    product_category: str | None = None
    quantity: int | None = None
    delivery_window: str | None = None
    estimated_value: Decimal | None = None
    competition_signal: str | None = None
    url: str | None = None
    posted: date | None = None


class FitAssessment(BaseModel):
    """Pursue-or-pass verdict for one notice, with a reason per factor."""

    notice_id: str
    verdict: Literal["pursue", "pass"]
    reasons: list[str] = Field(default_factory=list)
    model: str


class AwardRecord(BaseModel):
    """The real award KounOS checks its recommendation against."""

    solicitation_id: str
    award_id: str
    awardee: str
    date_signed: date
    total: Decimal
    number_of_offers: int
    source_url: str | None = None


class QuoteLine(BaseModel):
    """One priced line on a supplier quote."""

    line: str
    description: str
    quantity: int
    unit: str
    unit_price: Decimal
    extended: Decimal
    part: str | None = None


class Quote(BaseModel):
    """One supplier quote. Status is set by the citation check (A06)."""

    quote_id: str | None = None
    supplier: str
    solicitation_id: str
    lines: list[QuoteLine] = Field(default_factory=list)
    freight: Decimal = Decimal("0")
    total: Decimal
    lead_time_days_max: int | None = None
    country_of_origin: str | None = None
    status: Literal["verified", "needs_review"] = "needs_review"


CheckVerdict = Literal["pass", "fail", "needs_confirmation"]


class RequirementCheck(BaseModel):
    """One computed requirement check for one quote."""

    check: Literal["delivery", "spec", "sourcing"]
    verdict: CheckVerdict
    reason: str


class QuoteVerdict(BaseModel):
    """All requirement checks for one quote plus the overall verdict."""

    quote_id: str
    supplier: str
    checks: list[RequirementCheck] = Field(default_factory=list)
    overall: CheckVerdict


class QuoteComparison(BaseModel):
    """One quote with its checks and code-computed costs for the screen."""

    quote: Quote
    verdict: QuoteVerdict
    landed_cost: Decimal
    margin_at_award: Decimal
    safe_bid_per_unit: Decimal
    safe_bid_total: Decimal
    deposit_due: Decimal
    award_total: Decimal


class SourcingDecision(BaseModel):
    """Computed recommendation: pursue at a price, or pass with reasons."""

    solicitation_id: str
    decision: Literal["pursue", "pass"]
    bid_price: Decimal | None = None
    supplier: str | None = None
    reasons: list[str] = Field(default_factory=list)
    award_total: Decimal | None = None


class Order(BaseModel):
    """A tracked order under the simulated award."""

    order_id: str
    solicitation_id: str
    supplier: str
    status: str
    customer_due_date: date | None = None
    supplier_ship_date: date | None = None
    notes: list[str] = Field(default_factory=list)


class SupplierPO(BaseModel):
    """The purchase order Koun places with the chosen supplier."""

    po_id: str
    order_id: str
    supplier: str
    amount: Decimal
    deposit_due: Decimal = Decimal("0")
    status: str


class Shipment(BaseModel):
    """One inbound shipment against an order."""

    shipment_id: str
    order_id: str
    ship_date: date | None = None
    arrival_date: date | None = None
    carrier: str | None = None


class Invoice(BaseModel):
    """One government invoice against an order."""

    invoice_id: str
    order_id: str
    amount: Decimal
    due_date: date | None = None
    paid: bool = False


class Event(BaseModel):
    """Something that happened: voicemail, backup email, or system note."""

    event_id: str
    order_id: str
    source: Literal["voicemail", "email", "system"]
    summary: str
    supplier: str | None = None
    new_ship_date: date | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    received_at: datetime | None = None


class Flag(BaseModel):
    """A rule-engine finding a person must look at."""

    flag_id: str
    order_id: str
    code: str
    message: str
    severity: Literal["info", "warning", "blocking"]
    ref: SourceRef | None = None


class HealthStatus(BaseModel):
    """Typed shape of the GET /health response."""

    status: Literal["ok"]
    demo_mode: str
