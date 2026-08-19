# Final Integration Test Report — Project 2 (PHI/PII Redaction Pipeline)

**Closes:** #57
**Scope:** Full pipeline, end-to-end — raw clinical note in, redacted by the
proxy, processed by a mock external LLM, reversed back to original values
for an authorized consumer.

## What was tested

`tests/test_end_to_end_integration.py` runs against the real FastAPI app
(via `TestClient`), not just the redaction function in isolation, so it
also exercises route wiring, request/response models, and app startup —
the same path a live demo request would take.

| Test | What it verifies |
|---|---|
| `test_full_pipeline_redact_llm_reverse` | Single representative note: no direct identifier (name, DOB, phone, email, hospital) survives into the redacted text; medical eponym (`Parkinson's disease`) is correctly *not* redacted; reverse mapping restores every original value after a mock LLM step |
| `test_health_endpoint` | `/health` returns `200 {"status": "ok"}` |
| `test_full_synthetic_dataset_round_trip` | All 20 notes in `data/sample_clinical_notes.json`: each note is redacted, then reverse-mapped, and the restored text is asserted to be byte-for-byte identical to the original |

## Results

```
21 passed in 1.98s
```
(18 pre-existing unit tests + 3 new integration tests, all green.)

- **0/20** notes in the synthetic dataset failed round-trip restoration
- **0** direct identifiers observed in any redacted payload across the dataset
- Medical eponyms (Parkinson's, Alzheimer's, Crohn's) and department names
  (Neurology) confirmed *not* redacted, per issues #47 and #68

## Bug found and fixed during this pass

The documented Quick Start command for running the service
(`uvicorn app.main:app` from inside `proxy/`) failed with
`ModuleNotFoundError: No module named 'vault'` — the `vault` package is
one directory above `proxy/` and was never on the Python path. Fixed in
PR #79: docs corrected to `PYTHONPATH=.. uvicorn app.main:app --reload`,
and a dead/broken leftover module (`proxy/app/vault/__init__.py`, which
imported a non-existent file) was removed. Confirmed the running server
starts clean and correctly redacts a live request after the fix.

## How to reproduce

```bash
cd project2-phi-redaction
pip install -r proxy/requirements.txt
python -m spacy download en_core_web_sm
pytest tests/ -v
```
