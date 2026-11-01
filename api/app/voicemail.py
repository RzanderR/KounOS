"""Voicemail and backup-email intake (A18): transcribe, extract, record.

A supplier voicemail (audio) is transcribed with MODEL_TRANSCRIBE; the
backup email (text) skips transcription. Both go through the same
MODEL_READ extraction into an Event, which is stored on the order and
applied to its open shipment. Models read; code records.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from openai import OpenAI
from pydantic import BaseModel, Field

from app import replay
from app.config import REPO_ROOT, Settings
from app.schemas import Event, OrderDetail

VOICEMAIL_DIR = REPO_ROOT / "data" / "voicemail"
AUDIO_SUFFIXES = {".m4a", ".mp3", ".wav", ".ogg", ".flac"}

EVENT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "supplier": {"type": "string"},
        "po_id": {"type": "string"},
        "affected_items": {"type": "string"},
        "new_ship_date": {"type": "string"},
        "new_arrival_date": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": [
        "supplier",
        "po_id",
        "affected_items",
        "new_ship_date",
        "new_arrival_date",
        "confidence",
    ],
    "additionalProperties": False,
}

EVENT_PROMPT = (
    "Extract the supplier delay event from this message: the supplier name, "
    "the purchase order id, which items are affected, the new ship date and "
    "the new arrival date as YYYY-MM-DD, and your confidence 0 to 1. "
    "Return only JSON matching the schema."
)


class ExtractedEvent(BaseModel):
    """Validated MODEL_READ output for one delay message."""

    supplier: str
    po_id: str
    affected_items: str
    new_ship_date: date
    new_arrival_date: date
    confidence: float = Field(ge=0.0, le=1.0)


def transcribe_audio(audio_path: Path, settings: Settings) -> str:
    """Transcribe a voicemail with MODEL_TRANSCRIBE."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    with audio_path.open("rb") as audio:
        transcript = client.audio.transcriptions.create(
            model=settings.model_transcribe, file=audio
        )
    return transcript.text


def extract_event_from_text(
    transcript: str, settings: Settings
) -> ExtractedEvent:
    """Extract the delay event from a transcript or email body."""
    if not settings.model_api_key:
        raise RuntimeError("MODEL_API_KEY is not set (repo-root .env).")
    client = OpenAI(base_url=settings.meta_base_url, api_key=settings.model_api_key)
    response = client.responses.create(
        model=settings.model_read,
        input=[{"role": "user", "content": f"{EVENT_PROMPT}\n\n{transcript}"}],
        text={
            "format": {
                "type": "json_schema",
                "name": "delay_event",
                "schema": EVENT_SCHEMA,
                "strict": True,
            }
        },
    )
    return ExtractedEvent.model_validate(json.loads(response.output_text))


def build_event(
    order_id: str,
    source: Literal["voicemail", "email", "system"],
    summary: str,
    extracted: ExtractedEvent,
) -> Event:
    """Assemble the stored Event from an extraction."""
    return Event(
        event_id=f"EVT-{uuid4().hex[:8]}",
        order_id=order_id,
        source=source,
        summary=summary,
        supplier=extracted.supplier,
        new_ship_date=extracted.new_ship_date,
        confidence=extracted.confidence,
        received_at=datetime.now(timezone.utc),
    )


def resolve_file(filename: str) -> Path:
    """A voicemail-dir file by bare name; traversal and missing files fail."""
    if not filename or "/" in filename or "\\" in filename or filename.startswith("."):
        raise ValueError(f"Unsafe filename: {filename!r}")
    path = (VOICEMAIL_DIR / filename).resolve()
    if path.parent != VOICEMAIL_DIR.resolve() or not path.is_file():
        raise FileNotFoundError(f"Voicemail file not found: {filename}")
    return path


def ingest_file(
    order_id: str,
    source: Literal["voicemail", "email"],
    filename: str,
    settings: Settings,
    detail: OrderDetail,
) -> Event:
    """Transcribe (audio) or read (email), extract, store and apply one message.

    In replay mode the stored extraction for this file stands in for the
    model calls (A27); building and applying the event is the same code.
    """
    path = resolve_file(filename)
    if source == "voicemail" and path.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError(f"Not an audio file: {filename}")
    if source == "email" and path.suffix.lower() != ".txt":
        raise ValueError(f"Not a text backup: {filename}")
    if settings.demo_mode == "replay":
        record = replay.stored(f"event_{path.stem}")
        extracted = ExtractedEvent.model_validate(record["response"])
    else:
        if source == "voicemail":
            transcript = transcribe_audio(path, settings)
        else:
            transcript = path.read_text(encoding="utf-8")
        extracted = extract_event_from_text(transcript, settings)
    event = build_event(
        order_id,
        source,
        f"{extracted.supplier} reports a delay on {extracted.po_id} "
        f"({extracted.affected_items}): now shipping {extracted.new_ship_date} "
        f"arriving {extracted.new_arrival_date}.",
        extracted,
    )
    apply_event(detail, event, extracted.new_arrival_date)
    return event


def apply_event(detail: OrderDetail, event: Event, new_arrival: date) -> OrderDetail:
    """Store the event and move the order's dated shipment to the new dates.

    Events naming another supplier never move this order's shipment.
    Returns the same detail object the store already holds.
    """
    detail.events.append(event)
    if event.new_ship_date is None:
        return detail
    if event.supplier and detail.order.supplier != event.supplier:
        return detail
    for shipment in detail.shipments:
        if shipment.arrival_date is None or shipment.ship_date is None:
            continue
        shipment.ship_date = event.new_ship_date
        shipment.arrival_date = new_arrival
        detail.order.supplier_ship_date = event.new_ship_date
        break
    return detail
