# PHI/PII Redaction Proxy Service

Production-structured FastAPI service that sits between clinical staff and an
external LLM API, de-identifying clinical notes before they leave the
network boundary.

## Setup

```bash
cp .env.example .env   # fill in LLM_API_KEY before running for real
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Architecture

```
app/
  config.py          - environment-based settings (no hardcoded secrets)
  main.py            - FastAPI app, middleware, router registration
  models/schemas.py  - request/response models
  routes/
    health.py        - GET /health
    proxy.py          - POST /proxy/summarize
  services/
    redaction.py      - de-identification pre-processing hook (issue #44, Jagadesh)
    llm_client.py     - real async LLM client: timeouts, retries with backoff
```

## What's real vs. what's pending

- The LLM client makes an actual HTTP call to the configured provider
  (Anthropic Messages API by default) with retries and exponential
  backoff on 5xx/network errors - it is not a stub.
- `services/redaction.py` is the de-identification hook. It currently
  passes text through unchanged - this is issue #44, owned by Jagadesh.
- NLP entity detection (names, addresses) and the tokenization vault
  (Redis-backed pseudonymization) are separate services, owned by
  Sourish and Rishi (issues #46-#52), and will plug in ahead of
  `services/redaction.py` in the request pipeline once built.

## Security notes

- No API keys or secrets are hardcoded anywhere in this service - all
  come from environment variables via `app/config.py`.
- Logging is metadata-only (request IDs, lengths, status codes) -
  never logs raw or redacted note text, to avoid leaking PHI into logs.
- CORS is wide open (`*`) for local development only - restrict
  `allow_origins` before any real deployment.
