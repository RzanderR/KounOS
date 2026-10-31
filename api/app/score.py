"""Fit scoring in code (A35): pursue or pass with a reason per factor.

Veto model like the A11 checks: any failing factor makes the notice a
pass (don't pursue). Missing facts fail closed with a "not stated"
reason — the code never guesses what the notice doesn't say. Weights
are equal by documented choice; the company profile carries facts, not
weights.
"""

import json

from app.config import REPO_ROOT
from app.schemas import CompanyProfile, FitAssessment, Notice

PROFILE_PATH = REPO_ROOT / "data" / "company_profile.json"

FACTORS = (
    "set_aside",
    "product_category",
    "delivery_window",
    "estimated_value",
    "competition",
)


def load_profile() -> CompanyProfile:
    """The company profile; names H15 when the human hasn't saved it."""
    if not PROFILE_PATH.is_file():
        raise FileNotFoundError(
            "Company profile not found: data/company_profile.json (lands with H15)."
        )
    return CompanyProfile.model_validate(
        json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    )


def _match(needles: list[str], haystack: str | None) -> bool:
    """Substring match either way, case-insensitive."""
    if haystack is None:
        return False
    text = haystack.lower()
    return any(
        needle.lower() in text or text in needle.lower() for needle in needles
    )


def check_set_aside(notice: Notice, profile: CompanyProfile) -> tuple[bool, str]:
    """Koun must be eligible for the set-aside."""
    if notice.set_aside is None:
        return False, "Set-aside not stated; confirm Koun is eligible."
    if "unrestricted" in notice.set_aside.lower() or "open" in notice.set_aside.lower():
        return True, f"No set-aside ({notice.set_aside}); Koun is eligible."
    if _match(profile.set_aside_certifications, notice.set_aside):
        return True, f"Set-aside {notice.set_aside} matches Koun's certifications."
    held = ", ".join(profile.set_aside_certifications) or "none held"
    return False, f"Set-aside {notice.set_aside} needs certs Koun lacks ({held})."


def check_product(notice: Notice, profile: CompanyProfile) -> tuple[bool, str]:
    """Koun must sell the product category."""
    if notice.product_category is None:
        return False, "Product category not stated; cannot match Koun's catalog."
    if _match(profile.product_categories, notice.product_category):
        return True, f"{notice.product_category} matches what Koun sells."
    return False, f"{notice.product_category} is outside Koun's categories."


def check_delivery(notice: Notice, profile: CompanyProfile) -> tuple[bool, str]:
    """A stated window passes; feasibility detail is bid-time work."""
    _ = profile
    if notice.delivery_window is None:
        return False, "Delivery window not stated; cannot judge feasibility."
    return True, f"Delivery {notice.delivery_window} is stated; feasibility at bid time."


def check_value(notice: Notice, profile: CompanyProfile) -> tuple[bool, str]:
    """A stated value passes; banding against capacity is bid-time work."""
    _ = profile
    if notice.estimated_value is None:
        return False, "Estimated value not stated; cannot judge the band."
    return True, f"Estimated value {notice.estimated_value} is stated."


def check_competition(notice: Notice, profile: CompanyProfile) -> tuple[bool, str]:
    """Weak competition favors pursue; silence fails closed."""
    _ = profile
    if notice.competition_signal is None:
        return False, "Competition signal not stated."
    weak = ("sole source", "no competition", "only one", "limited competition")
    if any(marker in notice.competition_signal.lower() for marker in weak):
        return True, f"Weak competition: {notice.competition_signal}."
    return True, f"Competition noted ({notice.competition_signal}); bid to win."


CHECKS = {
    "set_aside": check_set_aside,
    "product_category": check_product,
    "delivery_window": check_delivery,
    "estimated_value": check_value,
    "competition": check_competition,
}


def score_notice(notice: Notice, profile: CompanyProfile) -> FitAssessment:
    """Pursue only when every factor passes, each with its reason."""
    reasons = []
    pursued = True
    for factor in FACTORS:
        passed, reason = CHECKS[factor](notice, profile)
        reasons.append(f"{factor}: {reason}")
        pursued = pursued and passed
    return FitAssessment(
        notice_id=notice.notice_id,
        verdict="pursue" if pursued else "pass",
        reasons=reasons,
        model="code",
    )
