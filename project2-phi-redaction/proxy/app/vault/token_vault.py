import uuid
from typing import Dict, Optional


class TokenVault:
    """
    In-memory tokenization vault.

    Creates reversible pseudonyms for sensitive values and keeps
    the same value mapped to the same token within one vault session.
    """

    def __init__(self):
        self._value_to_token: Dict[str, str] = {}
        self._token_to_value: Dict[str, str] = {}

    def tokenize(self, value: str, entity_type: str = "ENTITY") -> str:
        """Return a deterministic token for a value within this session."""

        if not value:
            return value

        # Return the existing token if this value was already tokenized.
        if value in self._value_to_token:
            return self._value_to_token[value]

        token = f"{entity_type.upper()}_{uuid.uuid4().hex[:12]}"

        self._value_to_token[value] = token
        self._token_to_value[token] = value

        return token

    def detokenize(self, token: str) -> Optional[str]:
        """Return the original value for a token."""
        return self._token_to_value.get(token)

    def clear(self) -> None:
        """Clear all mappings for the current session."""
        self._value_to_token.clear()
        self._token_to_value.clear()