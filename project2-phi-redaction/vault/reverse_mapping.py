"""Reverse mapping of pseudonym tokens back to original sensitive values."""

import re
from typing import Dict

from vault.tokenization import detokenize

_TOKEN_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]*_\d{4}\b")
_MAX_PASSES = 5  # guards against a pathological/cyclic mapping


def reverse_map_text(text: str) -> str:
    """Replace pseudonym tokens in text with their original values.

    Resolves nested tokens - e.g. if a token's stored original value is
    itself another token (which can happen if the NLP layer accidentally
    re-tokenizes an already-generated token), this keeps resolving until
    no token patterns remain or _MAX_PASSES is hit. A single pass isn't
    enough for that case: it would leave the inner token as a literal
    string like "EMAIL_0001" in the output instead of the real value.
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

    for _ in range(_MAX_PASSES):
        new_text = _TOKEN_PATTERN.sub(_replace, text)
        if new_text == text:
            break
        text = new_text

    return text
