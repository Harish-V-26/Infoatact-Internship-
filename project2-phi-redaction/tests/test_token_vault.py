import re

from vault import reset_session, tokenization_vault
from proxy.app.services.redaction import process_text


def setup_function() -> None:
    reset_session()


def test_deterministic_tokens_and_reverse_lookup() -> None:
    token1 = tokenization_vault.create_or_get_token("PERSON", "John Doe")
    token2 = tokenization_vault.create_or_get_token("PERSON", "John Doe")

    assert token1 == "PERSON_0001"
    assert token1 == token2
    assert tokenization_vault.detokenize(token1) == "John Doe"


def test_different_entities_produce_different_tokens() -> None:
    person_token = tokenization_vault.create_or_get_token("PERSON", "John Doe")
    email_token = tokenization_vault.create_or_get_token("EMAIL", "john@example.com")
    phone_token = tokenization_vault.create_or_get_token("PHONE", "555-555-1234")

    assert person_token == "PERSON_0001"
    assert email_token == "EMAIL_0001"
    assert phone_token == "PHONE_0001"
    assert person_token != email_token
    assert email_token != phone_token


def test_repeated_calls_return_identical_tokens() -> None:
    token1 = tokenization_vault.create_or_get_token("EMAIL", "john@example.com")
    token2 = tokenization_vault.create_or_get_token("EMAIL", "john@example.com")

    assert token1 == token2


def test_session_reset_clears_mappings() -> None:
    token1 = tokenization_vault.create_or_get_token("PERSON", "John Doe")
    assert tokenization_vault.detokenize(token1) == "John Doe"

    reset_session()

    token2 = tokenization_vault.create_or_get_token("PERSON", "John Doe")
    assert token2 == "PERSON_0001"
    assert token2 != token1 or token1 == token2
    assert tokenization_vault.detokenize(token2) == "John Doe"


def test_process_text_replaces_identifiers_with_tokens() -> None:
    text = "Patient John Doe called from 555-555-1234 and sent an email to john@example.com."
    processed = process_text(text)

    assert "PERSON_0001" in processed
    assert "PHONE_0001" in processed
    assert "EMAIL_0001" in processed
    assert "John Doe" not in processed
    assert "555-555-1234" not in processed
    assert "john@example.com" not in processed

    # Ensure tokens are reversible through the vault.
    assert tokenization_vault.detokenize("PERSON_0001") == "John Doe"
    assert tokenization_vault.detokenize("PHONE_0001") == "555-555-1234"
    assert tokenization_vault.detokenize("EMAIL_0001") == "john@example.com"
