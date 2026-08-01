"""
PHI/PII Redaction Proxy - application entrypoint.

Run with: uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, proxy
from app.services.llm_client import llm_client

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing needed yet - llm_client is instantiated at import time.
    yield
    # Shutdown: close the shared HTTP client cleanly.
    await llm_client.close()


app = FastAPI(
    title="PHI/PII Redaction Proxy",
    version="0.2.1",
    description=(
        "Proxy service that de-identifies clinical notes before forwarding "
        "them to an external LLM, and is intended to sit between clinical "
        "staff and any external AI summarization service."
    ),
    lifespan=lifespan,
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
