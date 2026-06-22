# Week 1 — Key Generation Script
# Generates RSA-2048 asymmetric key pair
# Private key must NEVER be committed to GitHub (blocked by .gitignore)
# Public key is safe to commit — edge agent uses it for verification

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os


def generate_rsa_keypair(private_key_path="private_key.pem", public_key_path="crypto/public_key.pem"):
    """
    Generates an RSA-2048 key pair.
    - Private key saved locally (NEVER commit this)
    - Public key saved to crypto/ folder (safe to commit)
    """
    print("[*] Generating RSA-2048 key pair...")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serialize and save private key (PEM format, no encryption for dev use)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(private_key_path, "wb") as f:
        f.write(private_pem)
    print(f"[✓] Private key saved to: {private_key_path}  <-- DO NOT COMMIT THIS FILE")

    # Serialize and save public key (safe to commit)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Ensure output directory exists
    os.makedirs(os.path.dirname(public_key_path), exist_ok=True)
    with open(public_key_path, "wb") as f:
        f.write(public_pem)
    print(f"[✓] Public key saved to: {public_key_path}  <-- Safe to commit")


if __name__ == "__main__":
    generate_rsa_keypair()
