from pydantic import BaseModel, Field

from app.config import settings


class NoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=settings.max_note_length)


class RedactResponse(BaseModel):
    redacted_text: str
    request_id: str


class HealthResponse(BaseModel):
    status: str
