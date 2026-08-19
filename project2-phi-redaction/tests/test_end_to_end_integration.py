"""
Final integration test (#57): full pipeline end-to-end.

Raw note in -> proxy redacts it -> a mock external LLM processes ONLY the
redacted text -> reverse_map_text restores the original values for an
authorized downstream consumer.

This exercises the real FastAPI app (via TestClient), not just the
service function in isolation, so it also catches wiring/import issues
that a unit test on redaction.py alone would miss (see PR #79 for an
example of the kind of bug this is meant to catch).
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "proxy"))

from fastapi.testclient import TestClient  # noqa: E402

from vault.reverse_mapping import reverse_map_text  # noqa: E402
from vault.tokenization import reset_session  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

SAMPLE_NOTE = (
    "Patient Jane Smith, DOB 03/14/1985, phone (555) 234-9876, "
    "email jane.smith@example.com, seen at Springfield General Hospital "
    "for follow-up. Family history includes Parkinson's disease "
    "(unrelated eponym, must not be redacted)."
)


def mock_llm_process(redacted_text: str) -> str:
    """
    Stand-in for an external LLM call. In production, this de-identified
    text is the only thing that would ever leave the network boundary.
    Wrapping it here proves two things: (1) no original PHI survives past
    the proxy boundary, and (2) a downstream consumer's output can still
    be correctly reversed afterward.
    """
    return f"Clinical summary: {redacted_text}"


def setup_function() -> None:
    reset_session()


def test_full_pipeline_redact_llm_reverse() -> None:
    # Step 1: raw note -> proxy -> redacted text
    response = client.post("/proxy/redact", json={"text": SAMPLE_NOTE})
    assert response.status_code == 200
    body = response.json()
    assert "redacted_text" in body and "request_id" in body
    redacted_text = body["redacted_text"]

    # Step 2: confirm no direct identifier crosses the proxy boundary
    assert "Jane Smith" not in redacted_text
    assert "03/14/1985" not in redacted_text
    assert "234-9876" not in redacted_text
    assert "jane.smith@example.com" not in redacted_text
    assert "Springfield General Hospital" not in redacted_text
    # medical eponym must survive untouched (issue #47)
    assert "Parkinson's disease" in redacted_text

    # Step 3: mock external LLM only ever sees the redacted text
    llm_output = mock_llm_process(redacted_text)
    assert "Jane Smith" not in llm_output

    # Step 4: reverse mapping restores originals for an authorized consumer
    restored = reverse_map_text(llm_output)
    assert "Jane Smith" in restored
    assert "03/14/1985" in restored
    assert "jane.smith@example.com" in restored
    assert "Springfield General Hospital" in restored


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_full_synthetic_dataset_round_trip() -> None:
    """
    Batch smoke test across the full synthetic dataset used for the risk
    report: every note must redact with a 200, and every entity that gets
    tokenized must be perfectly reversible.
    """
    data_path = ROOT_DIR / "data" / "sample_clinical_notes.json"
    payload = json.loads(data_path.read_text())
    notes = payload["notes"]
    assert len(notes) > 0

    failures = []
    for note in notes:
        reset_session()
        text = note["text"]
        response = client.post("/proxy/redact", json={"text": text})
        if response.status_code != 200:
            failures.append((note["note_id"], "non-200 response"))
            continue
        redacted = response.json()["redacted_text"]
        restored = reverse_map_text(redacted)
        if restored != text:
            failures.append((note["note_id"], f"round-trip mismatch: {restored!r} != {text!r}"))

    assert not failures, f"{len(failures)} note(s) failed round-trip: {failures}"
