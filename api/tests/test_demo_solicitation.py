"""Demo solicitation endpoint tests (A08).

Handler-level tests run without sockets. The TestClient round trip runs in
CI, where sockets are available.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import Settings
from app.demo_solicitation import build_demo_solicitation, demo_id
from app.main import app
from app.routers.solicitations import get_attachment, get_solicitation

client = TestClient(app)

SETTINGS = Settings()


def test_demo_id_matches_stored_extraction() -> None:
    """The served id comes from the stored model extraction."""
    assert demo_id() == "1232SA26Q0557"


def test_demo_has_both_clins_with_citation_badges() -> None:
    """Both CLINs (0001 base, 1001 option) carry a code-checked badge."""
    demo = build_demo_solicitation(SETTINGS.model_read)
    assert [req.line for req in demo.requirements] == ["0001", "1001"]
    assert [req.quantity for req in demo.requirements] == [58, 58]
    assert [req.unit for req in demo.requirements] == ["EA", "EA"]
    for req in demo.requirements:
        assert req.citation_status in ("verified", "needs_review")
        assert req.source is not None
        if req.citation_status == "verified":
            assert req.boxes, req.line
    assert len(demo.key_clauses) == 5
    for clause in demo.key_clauses:
        assert clause.citation_status in ("verified", "needs_review")


def test_provenance_names_model_and_eval_only_key() -> None:
    """The note is honest: stored model extraction, key is eval-only."""
    demo = build_demo_solicitation(SETTINGS.model_read)
    assert demo.provenance_note is not None
    assert SETTINGS.model_read in demo.provenance_note
    assert "data/extractions/1232SA26Q0557_extraction.json" in demo.provenance_note
    assert "eval" in demo.provenance_note


def test_answer_key_fields_are_not_displayed() -> None:
    """Set-aside/NAICS come only from the answer key, so the screen omits them."""
    demo = build_demo_solicitation(SETTINGS.model_read)
    assert demo.sub_agency is None
    assert demo.set_aside is None
    assert demo.naics is None


def test_handler_returns_demo_for_known_id() -> None:
    """The route handler returns the demo solicitation directly."""
    demo = get_solicitation("1232SA26Q0557", SETTINGS)
    assert demo.solicitation_id == "1232SA26Q0557"


def test_handler_404s_unknown_id() -> None:
    """Unknown solicitation ids fail closed with 404."""
    with pytest.raises(HTTPException) as exc_info:
        get_solicitation("nope", SETTINGS)
    assert exc_info.value.status_code == 404


def test_attachment_serves_demo_pdf() -> None:
    """The viewer endpoint serves the specifications PDF."""
    response = get_attachment(
        "1232SA26Q0557", "1232SA26Q0557_specifications.pdf"
    )
    assert response.media_type == "application/pdf"
    assert response.path.is_file()


def test_attachment_rejects_traversal_and_unknown_files() -> None:
    """Traversal and unknown files fail closed with 404."""
    for filename in ("../secret.env", "missing.pdf"):
        with pytest.raises(HTTPException) as exc_info:
            get_attachment("1232SA26Q0557", filename)
        assert exc_info.value.status_code == 404


def test_http_round_trip_serves_demo_and_404s_unknown() -> None:
    """CI gate: HTTP serves the demo solicitation and 404s unknown ids."""
    response = client.get("/solicitations/1232SA26Q0557")
    assert response.status_code == 200
    body = response.json()
    assert [req["line"] for req in body["requirements"]] == ["0001", "1001"]
    assert client.get("/solicitations/unknown").status_code == 404
