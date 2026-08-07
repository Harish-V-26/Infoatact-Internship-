"""Reversible tokenization vault implementation.

The tokenization vault tracks in-session mappings between original values and
readable pseudonyms. It supports deterministic pseudonym generation for the
duration of a session and provides reverse lookup for restoring original text.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, Optional, Tuple

from vault.redis_client import (
    clear_session as _clear_redis_session,
    connect_to_redis,
    get_original as _redis_get_original,
    get_token as _redis_get_token,
    increment_counter as _redis_increment_counter,
    save_mapping as _redis_save_mapping,
)

logger = logging.getLogger(__name__)

_TOKEN_FORMAT = "{entity_type}_{count:04d}"
_ENTITY_TYPE_CLEANER = re.compile(r"[^A-Z0-9_]" )


class TokenizationVault:
    """A session-scoped reversible pseudonymization engine."""

    def __init__(self) -> None:
        self.redis_client = None
        self._redis_tried = False
        self.reset_session()

    def _ensure_redis_client(self) -> None:
        if self.redis_client is None and not self._redis_tried:
            self.redis_client = connect_to_redis()
            self._redis_tried = True

    def _normalize_entity_type(self, entity_type: str) -> str:
        """Normalize entity types into a safe uppercase token prefix."""
        normalized = _ENTITY_TYPE_CLEANER.sub("_", entity_type.strip().upper())
        return normalized or "UNKNOWN"

    def _get_redis_token(self, normalized_type: str, original_value: str) -> Optional[str]:
        self._ensure_redis_client()
        if not self.redis_client:
            return None
        try:
            return _redis_get_token(normalized_type, original_value, self.redis_client)
        except Exception as exc:  # noqa: BLE001
            self._log_redis_unavailable(exc)
            self.redis_client = None
            return None

    def _get_redis_original(self, token: str) -> Optional[str]:
        self._ensure_redis_client()
        if not self.redis_client:
            return None
        try:
            return _redis_get_original(token, self.redis_client)
        except Exception as exc:  # noqa: BLE001
            self._log_redis_unavailable(exc)
            self.redis_client = None
            return None

    def _increment_redis_counter(self, normalized_type: str) -> Optional[int]:
        self._ensure_redis_client()
        if not self.redis_client:
            return None
        try:
            return _redis_increment_counter(normalized_type, self.redis_client)
        except Exception as exc:  # noqa: BLE001
            self._log_redis_unavailable(exc)
            self.redis_client = None
            return None

    def _save_redis_mapping(self, normalized_type: str, original_value: str, token: str) -> None:
        self._ensure_redis_client()
        if not self.redis_client:
            return
        try:
            _redis_save_mapping(normalized_type, original_value, token, self.redis_client)
        except Exception as exc:  # noqa: BLE001
            self._log_redis_unavailable(exc)
            self.redis_client = None

    def _log_redis_unavailable(self, exc: Exception) -> None:
        logger.warning(
            "Redis unavailable for tokenization vault; falling back to in-memory storage: %s",
            exc,
        )

    def create_or_get_token(self, entity_type: str, original_value: str) -> str:
        """Return an existing token or create a new one for the original value."""
        normalized_type = self._normalize_entity_type(entity_type)
        key = (normalized_type, original_value)

        existing = self._original_to_token.get(key)
        if existing is not None:
            return existing

        redis_token = self._get_redis_token(normalized_type, original_value)
        if redis_token is not None:
            self._original_to_token[key] = redis_token
            self._token_to_original[redis_token] = original_value
            return redis_token

        count = self._counters[normalized_type] + 1
        if self.redis_client:
            redis_count = self._increment_redis_counter(normalized_type)
            if redis_count is not None:
                count = redis_count

        token = _TOKEN_FORMAT.format(entity_type=normalized_type, count=count)

        while token in self._token_to_original:
            count += 1
            token = _TOKEN_FORMAT.format(entity_type=normalized_type, count=count)

        self._counters[normalized_type] = count
        self._original_to_token[key] = token
        self._token_to_original[token] = original_value
        self._save_redis_mapping(normalized_type, original_value, token)
        return token

    def detokenize(self, token: str) -> Optional[str]:
        """Return the original value for a previously generated token."""
        existing = self._token_to_original.get(token)
        if existing is not None:
            return existing

        redis_original = self._get_redis_original(token)
        if redis_original is not None:
            self._token_to_original[token] = redis_original
        return redis_original

    def reset_session(self) -> None:
        """Clear all in-memory mappings so the next tokenization starts fresh."""
        self._original_to_token: Dict[Tuple[str, str], str] = {}
        self._token_to_original: Dict[str, str] = {}
        self._counters: Dict[str, int] = defaultdict(int)
        _clear_redis_session(self.redis_client)


# Shared, session-scoped vault instance for the current process.
tokenization_vault = TokenizationVault()


def create_or_get_token(entity_type: str, original_value: str) -> str:
    return tokenization_vault.create_or_get_token(entity_type, original_value)


def detokenize(token: str) -> Optional[str]:
    return tokenization_vault.detokenize(token)


def reset_session() -> None:
    tokenization_vault.reset_session()
