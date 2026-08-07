import os
import sys
from pathlib import Path

import pytest

# Make the FastAPI app package visible when tests run from the project root.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "proxy"))

from vault.reverse_mapping import reverse_map_text
from vault.tokenization import TokenizationVault, create_or_get_token, reset_session
from app.services.redaction import process_text


class FakeRedisClient:
    def __init__(self, *args, **kwargs):
        self.store = {}

    def ping(self) -> bool:
        return True

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

    def incr(self, key):
        value = int(self.store.get(key, "0")) + 1
        self.store[key] = str(value)
        return value


@pytest.fixture(autouse=True)
def clear_env() -> None:
    os.environ.pop("REDIS_HOST", None)
    os.environ.pop("REDIS_PORT", None)
    os.environ.pop("REDIS_DB", None)
    os.environ.pop("REDIS_PASSWORD", None)
    reset_session()


def test_reverse_mapping_in_memory_lookup() -> None:
    token = create_or_get_token("PERSON", "John Doe")
    text = f"The patient is {token}."

    assert reverse_map_text(text) == "The patient is John Doe."


def test_reverse_mapping_unknown_token_remains_unchanged() -> None:
    text = "The patient is PERSON_9999."
    assert reverse_map_text(text) == "The patient is PERSON_9999."


def test_reverse_mapping_multiple_tokens() -> None:
    person_token = create_or_get_token("PERSON", "Alice")
    email_token = create_or_get_token("EMAIL", "alice@example.com")
    text = f"Contact {person_token} at {email_token}."

    assert reverse_map_text(text) == "Contact Alice at alice@example.com."


def test_reverse_mapping_preserves_formatting() -> None:
    token = create_or_get_token("PHONE", "555-555-1234")
    text = f"Call {token}\nFollow up later."

    assert reverse_map_text(text) == "Call 555-555-1234\nFollow up later."


def test_full_end_to_end_flow() -> None:
    note = "Patient Jane Doe called from 555-555-1234 and emailed jane@example.com."
    pseudonymized = process_text(note)

    # Simulate LLM response echoing the pseudonymized identifiers.
    llm_response = f"Summary: {pseudonymized}"
    restored = reverse_map_text(llm_response)

    assert "Jane Doe" in restored
    assert "555-555-1234" in restored
    assert "jane@example.com" in restored
    assert "PERSON_0001" not in restored
    assert "PHONE_0001" not in restored
    assert "EMAIL_0001" not in restored


def test_reverse_mapping_works_after_session_reset() -> None:
    token = create_or_get_token("PERSON", "Alice")
    reset_session()

    assert reverse_map_text(f"{token}") == token


def test_reverse_mapping_uses_redis_when_available(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")
    monkeypatch.setattr("vault.redis_client.redis.Redis", FakeRedisClient)

    token = create_or_get_token("PERSON", "Bob")
    assert reverse_map_text(f"Hello {token}.") == "Hello Bob."
