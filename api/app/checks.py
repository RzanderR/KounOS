"""Requirement checks in code (A11).

Every verdict is computed by plain rules over the extracted records; no
model call. Delivery compares the quote's worst-case lead time against the
solicitation's delivery limit. Spec compares each quoted part against the
required part (brand name only: anything else is technically
unacceptable). Sourcing never guesses: a missing country of origin is
``needs_confirmation`` for a person to resolve, never a pass.
"""

import json
import re
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel

from app.config import REPO_ROOT
from app.schemas import (
    CheckVerdict,
    Quote,
    QuoteLine,
    QuoteVerdict,
    RequirementCheck,
)

class RequirementsSpec(BaseModel):
    """What a quote must satisfy, read from the served solicitation."""

    delivery_limit_days: int
    required_part: str
    brand_name_only: bool = True
    sourcing_clause: str = ""


def parse_delivery_days(text: str) -> int:
    """Read the day count out of a delivery term ("within 60 days")."""
    match = re.search(r"(\d+)\s*days?", text, re.IGNORECASE)
    if match is None:
        raise ValueError(f"No day count in delivery term: {text!r}")
    return int(match.group(1))


def parse_far_number(text: str) -> str:
    """Read the FAR clause number ("FAR 52.225-3") out of a clause summary."""
    match = re.search(r"FAR\s+(\d+\.\d+-\d+)", text, re.IGNORECASE)
    if match is None:
        raise ValueError(f"No FAR number in sourcing clause: {text!r}")
    return match.group(1)


def check_delivery(quote: Quote, limit_days: int) -> RequirementCheck:
    """The quote's worst-case lead time must fit the delivery limit."""
    if quote.lead_time_days_max is None:
        return RequirementCheck(
            check="delivery",
            verdict="needs_confirmation",
            reason="No lead time stated; confirm delivery fits "
            f"{limit_days} days after award.",
        )
    if quote.lead_time_days_max <= limit_days:
        return RequirementCheck(
            check="delivery",
            verdict="pass",
            reason=f"Lead time up to {quote.lead_time_days_max} days fits "
            f"{limit_days} days after award.",
        )
    return RequirementCheck(
        check="delivery",
        verdict="fail",
        reason=f"Lead time up to {quote.lead_time_days_max} days exceeds "
        f"{limit_days} days after award.",
    )


def check_spec(quote: Quote, spec: RequirementsSpec) -> RequirementCheck:
    """Every quoted line must be the required part (brand name only)."""
    wrong = sorted(
        {line.part or "no part stated" for line in quote.lines if line.part != spec.required_part}
    )
    if not wrong:
        return RequirementCheck(
            check="spec",
            verdict="pass",
            reason=f"All lines quote {spec.required_part}.",
        )
    return RequirementCheck(
        check="spec",
        verdict="fail",
        reason=f"Quotes {', '.join(wrong)} instead of {spec.required_part}; "
        "brand name only, alternates are technically unacceptable.",
    )


def check_sourcing(quote: Quote, sourcing_clause: str) -> RequirementCheck:
    """Country of origin must be stated; a missing one needs confirmation."""
    origin = (quote.country_of_origin or "").strip().lower()
    if origin in ("", "not stated", "not stated on quote", "none"):
        return RequirementCheck(
            check="sourcing",
            verdict="needs_confirmation",
            reason=f"No country of origin stated; confirm {sourcing_clause} "
            "compliance with the supplier.",
        )
    if origin in ("usa", "u.s.a.", "us", "u.s.", "united states"):
        return RequirementCheck(
            check="sourcing",
            verdict="pass",
            reason=f"Country of origin {quote.country_of_origin} satisfies "
            f"{sourcing_clause}.",
        )
    return RequirementCheck(
        check="sourcing",
        verdict="fail",
        reason=f"Country of origin {quote.country_of_origin} does not satisfy "
        f"{sourcing_clause}.",
    )


def check_quote(quote_id: str, quote: Quote, spec: RequirementsSpec) -> QuoteVerdict:
    """Run every requirement check; fail dominates, then needs_confirmation."""
    checks = [
        check_delivery(quote, spec.delivery_limit_days),
        check_spec(quote, spec),
        check_sourcing(quote, spec.sourcing_clause or "the sourcing clause"),
    ]
    verdicts = [check.verdict for check in checks]
    overall: CheckVerdict
    if "fail" in verdicts:
        overall = "fail"
    elif "needs_confirmation" in verdicts:
        overall = "needs_confirmation"
    else:
        overall = "pass"
    return QuoteVerdict(
        quote_id=quote_id, supplier=quote.supplier, checks=checks, overall=overall
    )


def load_quote_fixture(quote_id: str) -> Quote:
    """Load a curated quote record from data/quotes/<id>.json as a Quote."""
    raw = json.loads(
        (REPO_ROOT / "data" / "quotes" / f"{quote_id}.json").read_text(encoding="utf-8")
    )
    return Quote(
        quote_id=quote_id,
        supplier=raw["supplier"],
        solicitation_id=raw["solicitation_id"],
        lines=[
            QuoteLine(
                line=item["line"],
                description=item["description"],
                quantity=item["quantity"],
                unit=item["unit"],
                unit_price=Decimal(item["unit_price"]),
                extended=Decimal(item["extended"]),
                part=item["part"],
            )
            for item in raw["lines"]
        ],
        freight=Decimal(raw["freight"]),
        total=Decimal(raw["quote_total"]),
        lead_time_days_max=raw["lead_time_days_max"],
        country_of_origin=raw["country_of_origin"],
    )


def demo_spec() -> RequirementsSpec:
    """The demo solicitation's requirements (D03): 60 days, PTB8850LS41."""
    return RequirementsSpec(
        delivery_limit_days=60,
        required_part="PTB8850LS41",
        brand_name_only=True,
        sourcing_clause="FAR 52.225-3",
    )


def demo_verdicts() -> list[QuoteVerdict]:
    """Check the three demo quotes; encodes the D03 verdicts."""
    spec = demo_spec()
    return [
        check_quote(quote_id, load_quote_fixture(quote_id), spec)
        for quote_id in ("ninebark", "larkspur", "tallgrass")
    ]


def fixture_path(quote_id: str) -> Path:
    """Path of a curated quote fixture (for tests and screens)."""
    return REPO_ROOT / "data" / "quotes" / f"{quote_id}.json"
