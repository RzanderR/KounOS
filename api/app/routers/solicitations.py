"""Solicitation routes: the demo solicitation and its PDFs (A08)."""

import base64

from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.demo_solicitation import ATTACHMENTS_DIR, build_demo_solicitation, demo_id
from app.schemas import PassageBytes, Solicitation

router = APIRouter(prefix="/solicitations", tags=["solicitations"])


@router.get("/{solicitation_id}", response_model=Solicitation)
def get_solicitation(
    solicitation_id: str, settings: Settings = Depends(get_settings)
) -> Solicitation:
    """The demo solicitation with code-checked citations (A08).

    Built from the stored MODEL_READ extraction, every citation re-checked
    in code; the provenance note names the stored file. Unknown ids 404.
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
