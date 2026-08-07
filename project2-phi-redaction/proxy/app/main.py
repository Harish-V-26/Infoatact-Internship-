"""
PHI/PII Redaction Proxy - application entrypoint.

Run with: uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, proxy

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="PHI/PII Redaction Proxy",
    version="0.3.0",
    description=(
        "De-identifies clinical notes by masking structured PII (regex) "
        "and tokenizing names/locations via NLP + a reversible vault. "
        "Does not call an external LLM - that step was intentionally "
        "removed to keep this a standalone, provider-agnostic component."
    ),
)

# CORS is wide open for local development. Tighten allow_origins to the
# real frontend's domain before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(proxy.router)
