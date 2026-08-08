# PHI/PII De-identification Proxy Service

A FastAPI service that takes a raw clinical note and returns it fully de-identified: structured PII (phone, email, date) masked via regex, and names/locations tokenized via NLP + a reversible vault.

This service does **not** call any external LLM. That was an earlier design direction, deliberately removed to keep this a standalone, provider-agnostic component that any downstream system can plug into.

## Setup

```bash
cp .env.example .env
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload
```

No API key is required to run this service.

## Endpoints

- `GET /health` — basic health check
- `POST /proxy/redact` — takes `{"text": "..."}`, returns `{"redacted_text": "...", "request_id": "..."}`

## Architecture

```
app/
  config.py          - environment-based settings (Redis config only, no LLM)
  main.py            - FastAPI app, middleware, router registration
  models/schemas.py  - request/response models
  routes/
    health.py        - GET /health
    proxy.py          - POST /proxy/redact
  services/
    redaction.py      - de-identification logic: regex + spaCy NLP (Rishi)

../vault/             - reversible tokenization vault (Sourish) - imported
                         by redaction.py, lives one level up since it's
                         shared infrastructure, not proxy-specific
```

## Restoring original values

`redact_note()` only redacts — it doesn't reverse. To restore original values from tokens (e.g. for an authorized downstream consumer), use `vault.reverse_mapping.reverse_map_text()` directly. This is intentionally not wired into the `/proxy/redact` endpoint itself.

## Verified status

Tested end-to-end against the 20-note synthetic dataset in `../data/`:
- 0/20 PHI leaks (phone, email, date)
- 0/20 reverse-mapping failures
- ~11ms average latency per request (unoptimized, single-request timing — not a formal benchmark)

## Security notes

- No API keys or secrets are hardcoded anywhere - all Redis config comes from environment variables via `app/config.py`
- Logging is metadata-only (request IDs, lengths, status codes) - never logs raw or redacted note text, to avoid leaking PHI into logs
- CORS is wide open (`*`) for local development only - restrict `allow_origins` before any real deployment
- No Docker image yet — this currently only runs via `uvicorn` directly
