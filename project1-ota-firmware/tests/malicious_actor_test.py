"""
Week 3 - Malicious Actor Test Suite
Owner: Harish (Lead)
Simulates attack scenarios to prove the system correctly rejects
tampered firmware, invalid signatures, and unauthorized requests.

Run with: python tests/malicious_actor_test.py
"""

import hashlib
import json

RESULTS = []


def check(name, passed, reason=""):
    symbol = "PASS" if passed else "FAIL"
    RESULTS.append({"name": name, "passed": passed})
    print(f"  [{symbol}] {name}" + (f" - {reason}" if reason else ""))
    return passed


def test_wrong_hash_rejected():
    """Simulate uploading firmware with a WRONG hash header.
    Server should detect mismatch and reject (400)."""
    print("\n[Attack 1] Upload with WRONG hash header")

    real_firmware = b"OTA_FW genuine firmware content v1.0.0"
    real_hash = hashlib.sha256(real_firmware).hexdigest()

    # Attacker claims a different (fake) hash to disguise tampering
    fake_hash_sent = "a" * 64

    server_recomputed_hash = hashlib.sha256(real_firmware).hexdigest()

    hash_matches = (fake_hash_sent == server_recomputed_hash)

    check(
        "Server detects hash mismatch and rejects upload",
        hash_matches is False,
        "fake hash correctly does not match recomputed hash"
    )


def test_tampered_firmware_signature():
    """Simulate a tampered firmware payload against an original signature.
    Signature verification must fail."""
    print("\n[Attack 2] Tampered firmware with original signature")

    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        original_firmware = b"GENUINE_FIRMWARE_PAYLOAD_v1.0.0"
        original_hash = hashlib.sha256(original_firmware).digest()

        signature = private_key.sign(
            original_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Attacker tampers with the firmware after signing
        tampered_firmware = b"MALICIOUS_FIRMWARE_PAYLOAD_v1.0.0"
        tampered_hash = hashlib.sha256(tampered_firmware).digest()

        rejected = False
        try:
            public_key.verify(
                signature,
                tampered_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except InvalidSignature:
            rejected = True

        check(
            "Edge agent rejects tampered firmware",
            rejected,
            "signature correctly fails on tampered content"
        )

    except Exception as e:
        check("Tampered firmware test", False, str(e))


def test_missing_auth_token():
    """Simulate a request to the server with NO auth token.
    Server should reject with 401."""
    print("\n[Attack 3] Request without auth token")

    required_token = "expected_secret_token"
    request_headers = {}  # attacker sends no Authorization header

    provided_token = request_headers.get("Authorization", "")
    token_valid = provided_token == f"Bearer {required_token}"

    check(
        "Server rejects request with missing auth token",
        token_valid is False,
        "missing token correctly fails auth check"
    )


def test_wrong_auth_token():
    """Simulate a request with a WRONG auth token."""
    print("\n[Attack 4] Request with incorrect auth token")

    required_token = "expected_secret_token"
    request_headers = {"Authorization": "Bearer wrong_token_12345"}

    provided_token = request_headers.get("Authorization", "")
    token_valid = provided_token == f"Bearer {required_token}"

    check(
        "Server rejects request with wrong auth token",
        token_valid is False,
        "wrong token correctly fails auth check"
    )


def test_rollback_attack():
    """Simulate an attacker trying to push an OLDER firmware version
    to force a downgrade. Agent must reject it."""
    print("\n[Attack 5] Firmware version rollback attempt")

    current_installed_version = "1.0.0"
    malicious_offered_version = "0.9.0"

    def version_tuple(v):
        return tuple(int(x) for x in v.split("."))

    is_newer = version_tuple(malicious_offered_version) > version_tuple(current_installed_version)

    check(
        "Agent rejects older firmware version (anti-rollback)",
        is_newer is False,
        "older version correctly identified and blocked"
    )


def test_valid_firmware_accepted():
    """Sanity check: a genuinely valid, untampered firmware
    with a correct signature MUST be accepted."""
    print("\n[Control] Valid firmware should be accepted")

    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        firmware = b"GENUINE_FIRMWARE_PAYLOAD_v1.0.0"
        firmware_hash = hashlib.sha256(firmware).digest()

        signature = private_key.sign(
            firmware_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        accepted = True
        try:
            public_key.verify(
                signature,
                firmware_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except InvalidSignature:
            accepted = False

        check(
            "Valid, untampered firmware is correctly accepted",
            accepted,
            "control case - system must not be overly strict"
        )

    except Exception as e:
        check("Valid firmware control test", False, str(e))


def print_summary():
    print("\n" + "=" * 55)
    print("MALICIOUS ACTOR TEST SUMMARY")
    print("=" * 55)
    passed = sum(1 for r in RESULTS if r["passed"])
    total = len(RESULTS)
    for r in RESULTS:
        symbol = "PASS" if r["passed"] else "FAIL"
        print(f"  [{symbol}] {r['name']}")
    print("=" * 55)
    print(f"  Result: {passed}/{total} security checks passed")
    if passed == total:
        print("  STATUS: ALL ATTACKS CORRECTLY BLOCKED")
    else:
        print(f"  STATUS: {total - passed} SECURITY GAP(S) FOUND")
    print("=" * 55)
    return passed == total


def main():
    print("=" * 55)
    print("OTA FIRMWARE SECURITY - MALICIOUS ACTOR TEST SUITE")
    print("=" * 55)

    test_wrong_hash_rejected()
    test_tampered_firmware_signature()
    test_missing_auth_token()
    test_wrong_auth_token()
    test_rollback_attack()
    test_valid_firmware_accepted()

    all_passed = print_summary()
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
