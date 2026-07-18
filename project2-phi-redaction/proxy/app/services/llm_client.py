"""
Async client for the external LLM API.

This is a real integration, not a mock: it makes an actual HTTP call to
the configured LLM API (Anthropic's Messages API by default), reading the
API key from environment configuration. It includes timeouts, retries
with exponential backoff on transient failures, and proper error
propagation via HTTPException so the API layer returns sensible status
codes instead of leaking stack traces.

No text is logged here - only request IDs and status/error metadata.
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

        last_error: Exception | None = None

        for attempt in range(1, settings.llm_max_retries + 1):
            try:
                response = await self._client.post(
                    settings.llm_api_url, headers=headers, json=payload
                )
                response.raise_for_status()
                return self._extract_text(response.json())

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500:
                    logger.error(
                        "LLM API client error request_id=%s status=%s",
                        request_id,
                        e.response.status_code,
                    )
                    raise HTTPException(
                        status_code=502, detail="LLM API rejected the request."
                    ) from e
                logger.warning(
                    "LLM API server error, retrying request_id=%s attempt=%d",
                    request_id,
                    attempt,
                )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                logger.warning(
                    "LLM API network error, retrying request_id=%s attempt=%d",
                    request_id,
                    attempt,
                )

            if attempt < settings.llm_max_retries:
                await asyncio.sleep(2 ** attempt)  # exponential backoff

        logger.error("LLM API failed after retries request_id=%s", request_id)
        raise HTTPException(
            status_code=502, detail="LLM API unavailable after retries."
        ) from last_error

    @staticmethod
    def _extract_text(data: dict) -> str:
        try:
            blocks = data.get("content", [])
            return "".join(
                block.get("text", "") for block in blocks if block.get("type") == "text"
            )
        except Exception as e:
            logger.exception("Failed to parse LLM response")
            raise HTTPException(
                status_code=502, detail="Malformed response from LLM API."
            ) from e

    async def close(self):
        await self._client.aclose()


llm_client = LLMClient()
