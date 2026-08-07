"""Reverse mapping of pseudonym tokens back to original sensitive values."""

import re
from typing import Dict

from vault.tokenization import detokenize

_TOKEN_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]*_\d{4}\b")


def reverse_map_text(text: str) -> str:
    """Replace pseudonym tokens in text with their original values.

    This function uses the existing tokenization vault's reverse lookup.
    If a token cannot be resolved, it is left unchanged.
    """

    cache: Dict[str, str | None] = {}

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token in cache:
            original = cache[token]
        else:
            original = detokenize(token)
            cache[token] = original
        return original if original is not None else token

    return _TOKEN_PATTERN.sub(_replace, text)
