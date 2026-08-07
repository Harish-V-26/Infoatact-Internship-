from token_vault import TokenVault


def test_token_vault():
    vault = TokenVault()

    # 1. Same value must get the same token in one session
    token1 = vault.tokenize("John Smith", "PERSON")
    token2 = vault.tokenize("John Smith", "PERSON")

    assert token1 == token2
    print("PASS: Same value gets same token")

    # 2. Different value must get a different token
    token3 = vault.tokenize("Jane Smith", "PERSON")

    assert token1 != token3
    print("PASS: Different values get different tokens")

    # 3. Token must not expose original PII
    assert "John Smith" not in token1
    print("PASS: Token does not expose original value")

    # 4. Original value must be recoverable
    assert vault.detokenize(token1) == "John Smith"
    print("PASS: Reverse mapping works")

    # 5. Clearing the session must remove mappings
    vault.clear()

    assert vault.detokenize(token1) is None
    print("PASS: Session mappings cleared")

    print("ALL TOKEN VAULT TESTS PASSED")


if __name__ == "__main__":
    test_token_vault()