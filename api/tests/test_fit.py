"""Triage tests (A34/A35): records, scoring and wiring without model calls.

Live extraction over the H16 batch happens when the notices land; every
code path around it — record building, veto scoring, routers, profile
handling — is pinned here with fixtures.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app import fit, score
from app.config import REPO_ROOT
from app.fit import CitedFact, FitExtraction, build_notice
from app.main import app
from app.schemas import CompanyProfile, Notice

client = TestClient(app)


def fact(value: str) -> CitedFact:
    """A cited fact with a throwaway page and snippet."""
    return CitedFact(value=value, page=1, snippet=f"supporting text for {value}")


def extraction(**overrides: str) -> FitExtraction:
    """A full fit extraction; override any field value."""
    values = {
        "title": "Greenhouse LED fixtures",
        "agency": "USDA ARS",
        "set_aside": "Total small business",
        "product_category": "LED greenhouse fixtures",
        "quantity": "58",
        "delivery_window": "60 days after award",
        "estimated_value": "$91,880.12",
        "competition_signal": "26 offers expected",
    }
    values.update(overrides)
    return FitExtraction(**{key: fact(value) for key, value in values.items()})


def profile() -> CompanyProfile:
    """Koun's fixture profile: small-business electrical supplier."""
    return CompanyProfile(
        company_name="Koun Test Co",
        set_aside_certifications=["Small business", "SBA 8(a)"],
        naics_codes=["335132"],
        product_categories=["LED greenhouse fixtures", "electrical supplies"],
        demo_margin_floor=Decimal("0.10"),
    )


def test_not_stated_facts_stay_missing() -> None:
    """'not stated' is never guessed into the record."""
    notice = build_notice(
        "N-1",
        extraction(set_aside="not stated", quantity="not stated"),
    )
    assert notice.set_aside is None
    assert notice.quantity is None
    assert notice.title == "Greenhouse LED fixtures"


def test_record_parses_numbers() -> None:
    """Quantity and value parse; unparseable values stay missing."""
    notice = build_notice("N-1", extraction())
    assert notice.quantity == 58
    assert notice.estimated_value == Decimal("91880.12")
    broken = build_notice("N-2", extraction(quantity="several", estimated_value="TBD"))
    assert broken.quantity is None
    assert broken.estimated_value is None


def test_demo_like_notice_scores_pursue() -> None:
    """The demo-shaped notice pursues with a reason per factor."""
    assessment = score.score_notice(build_notice("demo", extraction()), profile())
    assert assessment.verdict == "pursue"
    assert len(assessment.reasons) == 5


@pytest.mark.parametrize(
    "factor,field,value",
    [
        ("set_aside", "set_aside", "HUBZone"),
        ("product_category", "product_category", "office furniture"),
        ("delivery_window", "delivery_window", "not stated"),
        ("estimated_value", "estimated_value", "not stated"),
        ("competition", "competition_signal", "not stated"),
    ],
)
def test_each_factor_can_veto(factor: str, field: str, value: str) -> None:
    """One failing factor makes the notice a pass, naming the factor."""
    assessment = score.score_notice(
        build_notice("N-1", extraction(**{field: value})), profile()
    )
    assert assessment.verdict == "pass"
    assert any(reason.startswith(f"{factor}:") for reason in assessment.reasons)


def test_unrestricted_set_aside_passes() -> None:
    """Open competition needs no certificate."""
    assessment = score.score_notice(
        build_notice("N-1", extraction(set_aside="Unrestricted")), profile()
    )
    assert assessment.verdict == "pursue"


def test_citation_check_wires_to_a06() -> None:
    """Every fact snippet is checked; a known passage verifies."""
    pdf = REPO_ROOT / "data" / "solicitations" / "1232SA26Q0557_terms_and_clauses.pdf"
    ext = extraction()
    ext.title = CitedFact(
        value="CLIN 0001",
        page=1,
        snippet=(
            "0001 LED greenhouse light fixtures, brand name to PhotoBio "
            "CX 2125, 850W, 100-277 V 58 EA"
        ),
    )
    results = fit.check_fit_facts(pdf, ext)
    assert set(results) == set(fit.FIT_FIELDS)
    assert results["title"].status == "verified"


def test_profile_missing_names_h15() -> None:
    """No company profile yet: the error says H15, not a traceback."""
    assert not score.PROFILE_PATH.is_file()
    with pytest.raises(FileNotFoundError, match="H15"):
        score.load_profile()


def test_batch_empty_until_h16() -> None:
    """No notices dir: empty batch, and the loader names H16."""
    assert fit.list_notice_ids() == []
    with pytest.raises(FileNotFoundError, match="H16"):
        fit.load_notice("anything")
    response = client.get("/notices")
    assert response.status_code == 200
    assert response.json() == []


def test_unknown_notice_404s() -> None:
    """Unknown ids 404 with the H16 hint."""
    response = client.get("/notices/nope")
    assert response.status_code == 404


def test_fit_without_profile_is_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Scoring without H15 is explicit, not a 500."""
    notice = Notice(notice_id="demo", title="t", agency="a")
    monkeypatch.setattr(fit, "load_notice", lambda notice_id: notice)
    response = client.get("/notices/demo/fit")
    assert response.status_code == 503
    assert "H15" in response.json()["detail"]
