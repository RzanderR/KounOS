"""CORS tests: the hosted demo is cross-origin, so headers must allow it."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ATTACHMENT = "/solicitations/1232SA26Q0557/attachments/1232SA26Q0557_specifications.pdf"


def test_pdf_response_exposes_range_headers() -> None:
    """Cross-origin viewers can read length and range headers off the PDF."""
    response = client.get(ATTACHMENT, headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    exposed = response.headers["access-control-expose-headers"]
    for header in ("Content-Length", "Content-Range", "Accept-Ranges"):
        assert header in exposed, exposed
