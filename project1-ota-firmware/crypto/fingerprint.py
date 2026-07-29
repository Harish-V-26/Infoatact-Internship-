import hashlib


def generate_fingerprint(public_key_path):
    # Read public key bytes
    with open(public_key_path, "rb") as file:
        public_key_data = file.read()

    # Generate SHA-256 hash
    digest = hashlib.sha256(public_key_data).digest()

    # Take first 16 bytes and format as AA:BB:CC
    fingerprint = ":".join(
        f"{byte:02X}" for byte in digest[:16]
    )

    return fingerprint


# Test
if __name__ == "__main__":
    fingerprint = generate_fingerprint(
        "crypto/ecdsa_public.pem"
    )

    print("Key Fingerprint:", fingerprint)