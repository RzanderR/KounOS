"""Solicitation routes (A03 stubs, A08 demo endpoint)."""

import base64

from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.demo_solicitation import ATTACHMENTS_DIR, build_demo_solicitation, demo_id
from app.schemas import PassageBytes, Solicitation

router = APIRouter(prefix="/solicitations", tags=["solicitations"])


@router.get("", response_model=list[Solicitation])
def list_solicitations() -> list[Solicitation]:
    """List ingested solicitations (stub until A05)."""
    raise HTTPException(status_code=501, detail="Not implemented until A05.")


@router.get("/{solicitation_id}", response_model=Solicitation)
def get_solicitation(
    solicitation_id: str, settings: Settings = Depends(get_settings)
) -> Solicitation:
    """The demo solicitation with code-checked citations (A08).

    Built from the hand-checked answer key; the provenance note names the
    pending live MODEL_READ extraction. Unknown ids 404.
    """
    if solicitation_id != demo_id():
        raise HTTPException(
            status_code=404, detail=f"Unknown solicitation: {solicitation_id}."
        )
    return build_demo_solicitation(settings.model_read)


@router.get("/{solicitation_id}/attachments/{filename}")
def get_attachment(solicitation_id: str, filename: str) -> FileResponse:
    """Serve a solicitation PDF to the viewer (A08)."""
    if solicitation_id != demo_id() or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Unknown attachment.")
    path = (ATTACHMENTS_DIR / filename).resolve()
    if path.parent != ATTACHMENTS_DIR.resolve() or not path.is_file():
        raise HTTPException(status_code=404, detail="Unknown attachment.")
    return FileResponse(path, media_type="application/pdf")


@router.get("/{solicitation_id}/passage-bytes", response_model=PassageBytes)
def get_passage_bytes(solicitation_id: str, file: str) -> PassageBytes:
    """The attachment bytes as JSON, for viewers download managers harass.

    Same file, same traversal guard as the direct attachment; wrapped in
    ``application/json`` (with a query-string filename, no ``.pdf`` path)
    so download grabbers leave the response alone. The viewer decodes the
    base64 payload and renders from memory.
    """
    if solicitation_id != demo_id() or "/" in file or "\\" in file:
        raise HTTPException(status_code=404, detail="Unknown attachment.")
    path = (ATTACHMENTS_DIR / file).resolve()
    if path.parent != ATTACHMENTS_DIR.resolve() or not path.is_file():
        raise HTTPException(status_code=404, detail="Unknown attachment.")
    return PassageBytes(file=file, data=base64.b64encode(path.read_bytes()).decode("ascii"))


@router.post("/{solicitation_id}/extract", response_model=Solicitation)
def extract_solicitation(solicitation_id: str) -> Solicitation:
    """Run MODEL_READ extraction over the solicitation PDFs (stub until A05)."""
    raise HTTPException(
        status_code=501,
        detail=f"Not implemented until A05: {solicitation_id}.",
    )


@router.post("/{solicitation_id}/gap-pass")
def gap_pass(solicitation_id: str) -> None:
    """Run the gap and ambiguity pass (stub until A07)."""
    raise HTTPException(
        status_code=501,
        detail=f"Not implemented until A07: {solicitation_id}.",
    )
