# Project 2: HealthTech — PHI/PII De-identification Pipeline

**Infotact Internship — Cybersecurity Track — Month 2**
**Team:** Harish (Team Lead), Jagadesh, Sourish, Rishi

## Overview

A standalone service that de-identifies clinical notes: it detects and reversibly tokenizes PHI/PII (names, dates, phone numbers, emails, addresses) so the redacted text can be safely used elsewhere, with the ability to restore original values later for an authorized consumer. It does **not** call any external LLM — that scope was deliberately removed to keep this a provider-agnostic, standalone component.

## Folder Structure

| Folder | Purpose | Owner |
|---|---|---|
| `proxy/` | FastAPI service — `POST /proxy/redact` takes a raw note, returns it de-identified | Harish, Jagadesh |
| `proxy/app/services/redaction.py` | Regex (phone/email/date) + spaCy NLP (names/locations) de-identification logic | Rishi |
| `vault/` | Reversible tokenization engine — Redis-backed, with in-memory fallback | Sourish |
| `data/` | Synthetic clinical note samples used for testing — no real PHI | Harish |
| `tests/` | Unit + integration tests for the vault and reverse-mapping | Sourish |
| `docs/` | Architecture and risk-report documentation | Harish, Sourish |

## Quick Start

```bash
cd proxy
cp .env.example .env
pip install -r requirements.txt
python -m spacy download en_core_web_sm
PYTHONPATH=.. uvicorn app.main:app --reload
```

> `PYTHONPATH=..` is required so `vault/` (one level up, shared infrastructure)
> is importable — see `proxy/README.md` for details.

Test it:
```bash
curl -X POST http://localhost:8000/proxy/redact \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient John Doe, DOB 1985-03-14, call 555-123-4567."}'
```

## Status

Core de-identification pipeline is functionally complete and verified: 0 PHI leaks (phone/email/date) and 0 reverse-mapping failures across the full synthetic test dataset, confirmed via automated round-trip testing. See [`docs/RISK_REPORT.md`](docs/RISK_REPORT.md) for the detailed HIPAA Safe Harbor alignment assessment.

**Remaining work:** Docker deployment and formal latency benchmarking under load (not correctness issues — the pipeline works, it just isn't containerized yet).

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the tokenization/pseudonymization design.
