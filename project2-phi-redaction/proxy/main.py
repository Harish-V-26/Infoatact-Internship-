"""
FastAPI Proxy Service - PHI/PII Redaction Pipeline
Project 2 - HealthTech - Infotact Internship

Skeleton built by Harish (issue #42).
Regex-based de-identification (issue #44) is to be wired in by Jagadesh
inside process_text() below - that's the pre-processing step that runs
before text is sent to the LLM.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="PHI/PII Redaction Proxy", version="0.1.0")


class NoteRequest(BaseModel):
    text: str


@app.get("/health")
def health_check():
    """Basic health-check endpoint."""
    return {"status": "ok"}


def process_text(raw_text: str) -> str:
    """
    Pre-process the clinical note before sending it to the LLM.

    TODO (Jagadesh - issue #44): plug in regex-based de-identification
    here. This should detect and mask:
      - phone numbers (e.g. 555-123-4567 / (555) 123-4567)
      - emails
      - standard date formats (DOB, visit dates)

    Return the text with those fields replaced by placeholders, e.g.
    "[PHONE]", "[EMAIL]", "[DATE]". Leave names and addresses alone for
    now - those are handled later by the NLP layer (issue #46).
    """
    # Placeholder passthrough until the regex layer is added.
    return raw_text


def call_mock_llm(text: str) -> str:
    """
    Sends text to a mock LLM endpoint and returns a mock summary.
    In production this would call the real external LLM API. For now
    it's a stub so the pipeline can be tested end-to-end without
    external dependencies.
    """
    return f"[MOCK LLM SUMMARY] {text[:200]}"


@app.post("/proxy/summarize")
def summarize_note(payload: NoteRequest):
    """
    Main proxy route: takes a raw clinical note, pre-processes it
    (regex de-identification once #44 is wired in), sends it to the
    mock LLM, and returns the result.
    """
    cleaned = process_text(payload.text)
    result = call_mock_llm(cleaned)
    return {"summary": result, "processed_input": cleaned}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
