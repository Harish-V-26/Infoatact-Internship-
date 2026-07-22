"""
PHI/PII Redaction Proxy - application entrypoint.

Run with: uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, proxy
from app.services.llm_client import llm_client

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="PHI/PII Redaction Proxy",
    version="0.2.0",
    description=(
        "Proxy service that de-identifies clinical notes before forwarding "
        "them to an external LLM, and is intended to sit between clinical "
        "staff and any external AI summarization service."
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


@app.on_event("shutdown")
async def shutdown_event():
    await llm_client.close()
