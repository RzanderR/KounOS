"""Ask KounOS route (A24): a question answered from read-only tool calls."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import ask, replay
from app.config import ModelKeyMissing, Settings, get_settings
from app.schemas import AskAnswer

router = APIRouter(prefix="/ask", tags=["ask"])


class AskBody(BaseModel):
    """The question to answer."""

    question: str = Field(min_length=1, max_length=500)


@router.post("", response_model=AskAnswer)
def ask_question(body: AskBody, settings: Settings = Depends(get_settings)) -> AskAnswer:
    """Answer from read-only tools; figures and record IDs are checked in code."""
    try:
        return ask.answer(body.question, settings)
    except (replay.NoReplay, ModelKeyMissing) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ask.NoAnswer as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
