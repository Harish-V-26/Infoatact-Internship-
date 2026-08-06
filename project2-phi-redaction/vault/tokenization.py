"""Reversible tokenization vault implementation.

The tokenization vault tracks in-session mappings between original values and
readable pseudonyms. It supports deterministic pseudonym generation for the
duration of a session and provides reverse lookup for restoring original text.
"""

import re
from collections import defaultdict
from typing import Dict, Optional, Tuple

_TOKEN_FORMAT = "{entity_type}_{count:04d}"
_ENTITY_TYPE_CLEANER = re.compile(r"[^A-Z0-9_]" )


class TokenizationVault:
    """A session-scoped reversible pseudonymization engine."""

    def __init__(self) -> None:
        self.reset_session()

    def _normalize_entity_type(self, entity_type: str) -> str:
        """Normalize entity types into a safe uppercase token prefix."""
        normalized = _ENTITY_TYPE_CLEANER.sub("_", entity_type.strip().upper())
        return normalized or "UNKNOWN"

    def create_or_get_token(self, entity_type: str, original_value: str) -> str:
        """Return an existing token or create a new one for the original value."""
        normalized_type = self._normalize_entity_type(entity_type)
        key = (normalized_type, original_value)

        existing = self._original_to_token.get(key)
        if existing is not None:
            return existing

        count = self._counters[normalized_type] + 1
        token = _TOKEN_FORMAT.format(entity_type=normalized_type, count=count)

        # Ensure the generated token is unique across all session tokens.
        while token in self._token_to_original:
            count += 1
            token = _TOKEN_FORMAT.format(entity_type=normalized_type, count=count)

        self._counters[normalized_type] = count
        self._original_to_token[key] = token
        self._token_to_original[token] = original_value
        return token

    def detokenize(self, token: str) -> Optional[str]:
        """Return the original value for a previously generated token."""
        return self._token_to_original.get(token)

    def reset_session(self) -> None:
        """Clear all mappings so the next tokenization starts fresh."""
        self._original_to_token: Dict[Tuple[str, str], str] = {}
        self._token_to_original: Dict[str, str] = {}
        self._counters: Dict[str, int] = defaultdict(int)


# Shared, session-scoped vault instance for the current process.
tokenization_vault = TokenizationVault()


def create_or_get_token(entity_type: str, original_value: str) -> str:
    return tokenization_vault.create_or_get_token(entity_type, original_value)


def detokenize(token: str) -> Optional[str]:
    return tokenization_vault.detokenize(token)


def reset_session() -> None:
    tokenization_vault.reset_session()
