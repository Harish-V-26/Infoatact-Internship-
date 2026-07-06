# Week 1 — Firmware Signing Script
# Owner: Rishi (Edge Agent / QA)
# Branch: rishi-edge
# Takes firmware binary + private key → produces .sig signature file
# NOTE: Week 2 upgrade — private key will come from env variable, not file path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import argparse
import os


def sign_firmware(key_path, firmware_path, output_path):
    """
    Signs a firmware binary using RSA-PSS with SHA-256.
    Args:
        key_path (str): Path to the RSA private key (.pem)
        firmware_path (str): Path to the firmware binary (.bin)
        output_path (str): Path to save the signature (.sig)
    """
    # 1. Load private key
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Private key not found: {key_path}")

    with open(key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

    # 2. Read firmware binary
    if not os.path.exists(firmware_path):
        raise FileNotFoundError(f"Firmware file not found: {firmware_path}")

    with open(firmware_path, "rb") as f:
        firmware_data = f.read()

    # 3. Sign firmware using RSA-PSS with SHA-256
    signature = private_key.sign(
        firmware_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # 4. Save signature file
    with open(output_path, "wb") as sig_file:
        sig_file.write(signature)

    print(f"[✓] Signature saved to: {output_path}")
    print(f"[✓] Firmware signed: {firmware_path}")
    print(f"[✓] Signature size: {len(signature)} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sign a firmware binary using RSA private key."
    )
    parser.add_argument("-k", "--key", required=True, help="Path to private key (.pem)")
    parser.add_argument("-f", "--firmware", required=True, help="Path to firmware binary (.bin)")
    parser.add_argument("-o", "--output", default="firmware.sig", help="Output signature file (.sig)")

    args = parser.parse_args()

    try:
        sign_firmware(args.key, args.firmware, args.output)
    except Exception as e:
        print(f"[✗] Signing failed: {e}")
        exit(1)
