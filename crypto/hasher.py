# Week 1 — Firmware SHA-256 Hasher
# Computes the SHA-256 hash of a firmware binary file
# Output hash is passed to sign_helper.py for signing

import hashlib
import argparse
import os


def compute_sha256(firmware_path):
    """
    Computes the SHA-256 hash of a firmware binary file.
    Args:
        firmware_path (str): Path to the firmware .bin file.
    Returns:
        str: Hex string of the SHA-256 hash.
    """
    if not os.path.exists(firmware_path):
        raise FileNotFoundError(f"Firmware file not found: {firmware_path}")

    sha256 = hashlib.sha256()
    with open(firmware_path, "rb") as f:
        # Read in chunks to handle large firmware files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute the SHA-256 hash of a firmware binary."
    )
    parser.add_argument(
        "-f", "--firmware",
        required=True,
        help="Path to the firmware .bin file"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Optional: save hash to a .txt file"
    )

    args = parser.parse_args()

    try:
        firmware_hash = compute_sha256(args.firmware)
        print(f"[✓] SHA-256 Hash: {firmware_hash}")

        if args.output:
            with open(args.output, "w") as out:
                out.write(firmware_hash)
            print(f"[✓] Hash saved to: {args.output}")
    except Exception as e:
        print(f"[✗] Error: {e}")
