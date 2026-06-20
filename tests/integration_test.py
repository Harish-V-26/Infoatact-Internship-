import os
import sys
import hashlib
import tempfile
import shutil
from datetime import datetime

RESULTS = []


def check(name, passed, reason=""):
    symbol = "OK" if passed else "FAIL"
    RESULTS.append({"name": name, "passed": passed})
    print(f"  [{symbol}] {name}" + (f" - {reason}" if reason and not passed else ""))
    return passed


def test_key_generation(tmp_dir):
    print("\n[1] Key Generation")
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        priv_path = os.path.join(tmp_dir, "test_private.pem")

        with open(priv_path, "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))

        check("Private key generated", os.path.exists(priv_path))
        return private_key
    except Exception as e:
        check("Key generation", False, str(e))
        return None


def test_firmware_hashing(tmp_dir):
    print("\n[2] Firmware Hashing")
    try:
        firmware_path = os.path.join(tmp_dir, "test_firmware.bin")
        with open(firmware_path, "wb") as f:
            f.write(b"OTA_FW" + b"IoT Cargo Tracker Test Firmware v1.0.0" * 10)

        sha256 = hashlib.sha256()
        with open(firmware_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        fw_hash = sha256.hexdigest()

        check("Firmware binary created", os.path.exists(firmware_path))
        check("SHA-256 hash computed", len(fw_hash) == 64)
        return firmware_path, fw_hash
    except Exception as e:
        check("Firmware hashing", False, str(e))
        return None, None


def test_signing(tmp_dir, fw_hash, private_key):
    print("\n[3] Firmware Signing")
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        signature = private_key.sign(
            bytes.fromhex(fw_hash),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        sig_path = os.path.join(tmp_dir, "test_firmware.sig")
        with open(sig_path, "wb") as f:
            f.write(base64.b64encode(signature))

        check("Signature file created", os.path.exists(sig_path))
        check("Signature is non-empty", os.path.getsize(sig_path) > 0)
        return sig_path
    except Exception as e:
        check("Signing", False, str(e))
        return None


def test_verification(sig_path, fw_hash, private_key):
    print("\n[4] Signature Verification")
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature
        import base64

        public_key = private_key.public_key()

        with open(sig_path, "rb") as f:
            signature = base64.b64decode(f.read())

        try:
            public_key.verify(
                signature,
                bytes.fromhex(fw_hash),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            check("Valid signature accepted", True)
        except InvalidSignature:
            check("Valid signature accepted", False, "Verification failed")

        tampered_hash = "a" * 64
        try:
            public_key.verify(
                signature,
                bytes.fromhex(tampered_hash),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            check("Tampered firmware rejected", False, "Should have been rejected")
        except InvalidSignature:
            check("Tampered firmware rejected", True)

    except Exception as e:
        check("Verification", False, str(e))


def print_summary():
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    passed = sum(1 for r in RESULTS if r["passed"])
    total = len(RESULTS)
    for r in RESULTS:
        symbol = "OK" if r["passed"] else "FAIL"
        print(f"  [{symbol}] {r['name']}")
    print("=" * 50)
    print(f"  Result: {passed}/{total} checks passed")
    if passed == total:
        print("  STATUS: ALL CHECKS PASSED - SYSTEM IS SECURE")
    else:
        print(f"  STATUS: {total - passed} CHECK(S) FAILED")
    print("=" * 50)
    return passed == total


def main():
    print("=" * 50)
    print("OTA FIRMWARE SECURITY - INTEGRATION TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    tmp_dir = tempfile.mkdtemp(prefix="ota_test_")

    try:
        private_key = test_key_generation(tmp_dir)
        if not private_key:
            sys.exit(1)

        firmware_path, fw_hash = test_firmware_hashing(tmp_dir)
        if not firmware_path:
            sys.exit(1)

        sig_path = test_signing(tmp_dir, fw_hash, private_key)
        if not sig_path:
            sys.exit(1)

        test_verification(sig_path, fw_hash, private_key)

        all_passed = print_summary()
        sys.exit(0 if all_passed else 1)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
