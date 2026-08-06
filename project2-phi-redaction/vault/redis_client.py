"""Redis-backed storage helpers for the tokenization vault."""

import hashlib
import logging
import os
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)

_REDIS_PREFIX = "vault"


def _format_original_key(entity_type: str, original_value: str) -> str:
    digest = hashlib.sha256(original_value.encode("utf-8")).hexdigest()
    return f"{_REDIS_PREFIX}:original:{entity_type}:{digest}"


def _format_token_key(token: str) -> str:
    return f"{_REDIS_PREFIX}:token:{token}"


def _format_counter_key(entity_type: str) -> str:
    return f"{_REDIS_PREFIX}:counter:{entity_type}"


def connect_to_redis() -> Optional[redis.Redis]:
    """Create and verify a Redis connection using environment variables."""
    host = os.getenv("REDIS_HOST")
    port = os.getenv("REDIS_PORT")
    db = os.getenv("REDIS_DB")
    password = os.getenv("REDIS_PASSWORD")

    if not host or not port or not db:
        logger.warning(
            "Redis configuration incomplete: REDIS_HOST, REDIS_PORT, and REDIS_DB are required"
        )
        return None

    try:
        redis_client = redis.Redis(
            host=host,
            port=int(port),
            db=int(db),
            password=password or None,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        redis_client.ping()
        return redis_client
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis connection failed, falling back to in-memory vault: %s", exc)
        return None


def save_mapping(entity_type: str, original_value: str, token: str, client: redis.Redis) -> None:
    """Persist a token and its reverse mapping in Redis."""
    original_key = _format_original_key(entity_type, original_value)
    token_key = _format_token_key(token)
    client.set(original_key, token)
    client.set(token_key, original_value)


def get_token(entity_type: str, original_value: str, client: redis.Redis) -> Optional[str]:
    """Retrieve an existing token for an original value from Redis."""
    original_key = _format_original_key(entity_type, original_value)
    return client.get(original_key)


def get_original(token: str, client: redis.Redis) -> Optional[str]:
    """Retrieve the original value for a token from Redis."""
    token_key = _format_token_key(token)
    return client.get(token_key)


def increment_counter(entity_type: str, client: redis.Redis) -> int:
    """Atomically increment the entity counter in Redis and return the new value."""
    counter_key = _format_counter_key(entity_type)
    return int(client.incr(counter_key))


def clear_session(client: Optional[redis.Redis]) -> None:
    """No-op for Redis persistence: session state is managed by the vault wrapper."""
    if client is None:
        return
    logger.debug("Redis clear_session called; persistent mappings are retained")
