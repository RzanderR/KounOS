"""Passage-bytes tests: the viewer fetches PDF bytes wrapped in JSON."""

import base64

from fastapi.testclient import TestClient

from app.demo_solicitation import ATTACHMENTS_DIR
from app.main import app

client = TestClient(app)

ENDPOINT = "/solicitations/1232SA26Q0557/passage-bytes"
FILE = "1232SA26Q0557_specifications.pdf"


def test_passage_bytes_round_trip() -> None:
    """JSON-wrapped bytes decode to the exact attachment on disk."""
    response = client.get(ENDPOINT, params={"file": FILE})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["file"] == FILE
    expected = (ATTACHMENTS_DIR / FILE).read_bytes()
    assert base64.b64decode(body["data"]) == expected
    assert base64.b64decode(body["data"]).startswith(b"%PDF")


def test_passage_bytes_rejects_traversal() -> None:
    """The file guard matches the direct attachment endpoint."""
    response = client.get(ENDPOINT, params={"file": "../secret.pdf"})
    assert response.status_code == 404


def test_passage_bytes_unknown_file_404s() -> None:
    """Unknown filenames 404 instead of leaking directory state."""
    response = client.get(ENDPOINT, params={"file": "nope.pdf"})
    assert response.status_code == 404
