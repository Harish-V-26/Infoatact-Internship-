import logging
import uuid

from fastapi import APIRouter

from app.models.schemas import NoteRequest, SummarizeResponse
from app.services.llm_client import llm_client
from app.services.redaction import process_text
from vault.reverse_mapping import reverse_map_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/proxy/summarize", response_model=SummarizeResponse)
async def summarize_note(payload: NoteRequest) -> SummarizeResponse:
    request_id = str(uuid.uuid4())
    logger.info("summarize_note received request_id=%s", request_id)

    cleaned_text = process_text(payload.text)
    summary = await llm_client.summarize(cleaned_text, request_id)
    restored_summary = reverse_map_text(summary)

    logger.info("summarize_note completed request_id=%s", request_id)
    return SummarizeResponse(summary=restored_summary, request_id=request_id)
