import os

import pytest

from vault.redis_client import connect_to_redis, get_original, get_token, save_mapping
from vault.tokenization import TokenizationVault, reset_session, tokenization_vault


@pytest.fixture(autouse=True)
def clear_env() -> None:
    os.environ.pop("REDIS_HOST", None)
    os.environ.pop("REDIS_PORT", None)
    os.environ.pop("REDIS_DB", None)
    os.environ.pop("REDIS_PASSWORD", None)
    reset_session()


def test_redis_environment_required_for_connection() -> None:
    client = connect_to_redis()
    assert client is None


def test_redis_connection_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")

    client = connect_to_redis()
    assert client is not None
    assert client.ping() is True


def test_redis_mapping_write_and_read(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")

    client = connect_to_redis()
    assert client is not None

    save_mapping("PERSON", "Alice", "PERSON_0001", client)
    assert get_token("PERSON", "Alice", client) == "PERSON_0001"
    assert get_original("PERSON_0001", client) == "Alice"


def test_deterministic_token_reuse_with_redis(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")

    vault = TokenizationVault()
    token1 = vault.create_or_get_token("PERSON", "Bob Smith")
    token2 = vault.create_or_get_token("PERSON", "Bob Smith")

    assert token1 == token2
    assert vault.detokenize(token1) == "Bob Smith"


def test_fallback_to_memory_when_redis_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "9999")
    monkeypatch.setenv("REDIS_DB", "0")

    vault = TokenizationVault()
    token = vault.create_or_get_token("EMAIL", "test@example.com")

    assert token == "EMAIL_0001"
    assert vault.detokenize(token) == "test@example.com"
    assert tokenization_vault.detokenize(token) == "test@example.com"


def test_reset_session_maintains_api_behavior(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")

    vault = TokenizationVault()
    token = vault.create_or_get_token("PERSON", "Carol")
    assert token.startswith("PERSON_")

    reset_session()
    token_after_reset = vault.create_or_get_token("PERSON", "Carol")
    assert token_after_reset == "PERSON_0001"
