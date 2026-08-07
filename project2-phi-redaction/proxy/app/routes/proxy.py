import logging
import uuid

from fastapi import APIRouter

from app.models.schemas import NoteRequest, RedactResponse
from app.services.redaction import process_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/proxy/redact", response_model=RedactResponse)
async def redact_note(payload: NoteRequest) -> RedactResponse:
    """
    Takes a raw clinical note and returns it fully de-identified -
    structured PII masked via regex, names/locations tokenized via the
    NLP + vault pipeline.

    This service no longer calls an external LLM - that decision was
    made explicitly to keep the redaction pipeline as a standalone,
    reusable component rather than coupling it to any one LLM provider.
    Restoring original values from tokens (for an authorized downstream
    consumer) is available separately via vault.reverse_mapping, but is
    intentionally not wired into this endpoint.
    """
    request_id = str(uuid.uuid4())
    logger.info("redact_note received request_id=%s", request_id)

    redacted_text = process_text(payload.text)

    logger.info("redact_note completed request_id=%s", request_id)
    return RedactResponse(redacted_text=redacted_text, request_id=request_id)
