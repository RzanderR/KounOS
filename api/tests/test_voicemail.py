"""Voicemail intake tests (A18): record and apply without model calls.

Transcription and MODEL_READ extraction need the API key and the H09
audio; they run live when the recording lands. Everything after the
extraction — build, store, apply, flag — is code and tested here.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.order_store import get_detail, reset
from app.rules import evaluate
from app.voicemail import (
    EVENT_SCHEMA,
    ExtractedEvent,
    apply_event,
    build_event,
    resolve_file,
)

client = TestClient(app)

EXTRACTION = ExtractedEvent(
    supplier="Tallgrass Horticultural Supply",
    po_id="PO-001",
    affected_items="116 LED greenhouse fixtures (base + option)",
    new_ship_date=date(2026, 12, 31),
    new_arrival_date=date(2027, 1, 3),
    confidence=0.9,
)


def test_event_schema_requires_every_property() -> None:
    """Strict-mode APIs reject the schema unless required lists every property."""
    props = EVENT_SCHEMA["properties"]
    assert isinstance(props, dict)
    required = EVENT_SCHEMA["required"]
    assert isinstance(required, list)
    assert set(required) == set(props)


def test_apply_event_moves_shipment_and_flags_delay() -> None:
    """The full no-model path: event stored, shipment moved, flag raised."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    event = build_event("ORD-001", "voicemail", "Tallgrass backorder.", EXTRACTION)
    assert event.new_ship_date == date(2026, 12, 31)
    apply_event(detail, event, EXTRACTION.new_arrival_date)
    assert detail.events[-1].event_id == event.event_id
    assert detail.shipments[0].ship_date == date(2026, 12, 31)
    assert detail.shipments[0].arrival_date == date(2027, 1, 3)
    flags = evaluate(detail)
    assert any("2 days late" in flag.message for flag in flags)


def test_wrong_supplier_event_never_moves_shipment() -> None:
    """An event naming another supplier is stored but not applied."""
    reset()
    detail = get_detail("ORD-001")
    assert detail is not None
    other = EXTRACTION.model_copy(update={"supplier": "Someone Else"})
    event = build_event("ORD-001", "email", "Unrelated notice.", other)
    apply_event(detail, event, other.new_arrival_date)
    assert len(detail.events) == 1
    assert detail.shipments[0].ship_date == date(2026, 11, 30)


def test_resolve_file_rejects_traversal_and_missing() -> None:
    """Audio comes only from data/voicemail/ by bare name."""
    with pytest.raises(ValueError):
        resolve_file("../secret.env")
    with pytest.raises(FileNotFoundError):
        resolve_file("no-such-file.m4a")


def test_ingest_endpoint_validates_before_models() -> None:
    """Unknown orders and files fail closed without touching a model."""
    reset()
    response = client.post(
        "/events/ingest",
        json={"order_id": "nope", "source": "voicemail", "filename": "x.m4a"},
    )
    assert response.status_code == 404
    response = client.post(
        "/events/ingest",
        json={"order_id": "ORD-001", "source": "voicemail", "filename": "x.m4a"},
    )
    assert response.status_code == 404
