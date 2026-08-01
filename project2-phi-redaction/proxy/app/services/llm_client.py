"""
Async client for the external LLM API.

Supports two providers:
- "anthropic": cloud API, needs LLM_API_KEY, costs money per request
- "ollama": local model running on your own machine via Ollama, free,
  no API key needed, and the clinical note never leaves the machine -
  worth calling out explicitly in the security report as a data
  residency advantage.

Includes timeouts, retries with exponential backoff on transient
failures, and proper error propagation via HTTPException. No text is
logged here - only request IDs and status/error metadata.
"""

import asyncio
import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.llm_timeout_seconds)

    async def summarize(self, text: str, request_id: str) -> str:
        if settings.llm_provider == "ollama":
            return await self._summarize_ollama(text, request_id)
        return await self._summarize_anthropic(text, request_id)

    # ------------------------------------------------------------------
    # Anthropic (cloud)
    # ------------------------------------------------------------------
    async def _summarize_anthropic(self, text: str, request_id: str) -> str:
        if not settings.llm_api_key:
            raise HTTPException(
                status_code=503,
                detail="LLM API key not configured. Set LLM_API_KEY in the environment.",
            )

        headers = {
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": f"Summarize this clinical note:\n\n{text}"}
            ],
        }

        async def call():
            response = await self._client.post(
                settings.llm_api_url, headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            blocks = data.get("content", [])
            return "".join(
                b.get("text", "") for b in blocks if b.get("type") == "text"
            )

        return await self._with_retries(call, request_id, provider="anthropic")

    # ------------------------------------------------------------------
    # Ollama (local, free)
    # ------------------------------------------------------------------
    async def _summarize_ollama(self, text: str, request_id: str) -> str:
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "user", "content": f"Summarize this clinical note:\n\n{text}"}
            ],
            "stream": False,
        }

        async def call():
            try:
                response = await self._client.post(
                    settings.ollama_api_url, json=payload
                )
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Could not reach local Ollama server at "
                        f"{settings.ollama_api_url}. Is Ollama running? "
                        "(ollama run <model>)"
                    ),
                ) from e
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

        return await self._with_retries(call, request_id, provider="ollama")

    # ------------------------------------------------------------------
    # Shared retry logic
    # ------------------------------------------------------------------
    async def _with_retries(self, call, request_id: str, provider: str) -> str:
        last_error: Exception | None = None

        for attempt in range(1, settings.llm_max_retries + 1):
            try:
                return await call()

            except HTTPException as e:
                if e.status_code < 500:
                    logger.error(
                        "%s client error request_id=%s status=%s",
                        provider,
                        request_id,
                        e.status_code,
                    )
                    raise
                last_error = e
                logger.warning(
                    "%s server error, retrying request_id=%s attempt=%d",
                    provider,
                    request_id,
                    attempt,
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500:
                    logger.error(
                        "%s client error request_id=%s status=%s",
                        provider,
                        request_id,
                        e.response.status_code,
                    )
                    raise HTTPException(
                        status_code=502, detail=f"{provider} API rejected the request."
                    ) from e
                logger.warning(
                    "%s server error, retrying request_id=%s attempt=%d",
                    provider,
                    request_id,
                    attempt,
                )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                logger.warning(
                    "%s network error, retrying request_id=%s attempt=%d",
                    provider,
                    request_id,
                    attempt,
                )

            if attempt < settings.llm_max_retries:
                await asyncio.sleep(2 ** attempt)  # exponential backoff

        logger.error("%s failed after retries request_id=%s", provider, request_id)
        if isinstance(last_error, HTTPException):
            raise last_error
        raise HTTPException(
            status_code=502, detail=f"{provider} API unavailable after retries."
        ) from last_error

    async def close(self):
        await self._client.aclose()


llm_client = LLMClient()
