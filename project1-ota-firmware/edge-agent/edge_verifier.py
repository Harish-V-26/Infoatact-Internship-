import json
import os
import sys

# Allow importing from crypto/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crypto.engine import CryptoEngine
from crypto.sha256_hash import calculate_sha256


def verify_firmware(
    firmware_path,
    metadata_path,
    signature_path,
    public_key_path
):
    """
    Verify firmware integrity and authenticity.

    Returns:
        True  -> Firmware is valid
        False -> Firmware verification failed
    """

    # Load metadata
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Failed to load metadata: {e}")
        return False

    # Read metadata fields
    algorithm = metadata.get("algorithm")
    expected_hash = metadata.get("sha256_hash")

    if not algorithm:
        print("Metadata missing 'algorithm'")
        return False

    if not expected_hash:
        print("Metadata missing 'sha256_hash'")
        return False

    # Calculate firmware hash
    try:
        calculated_hash = calculate_sha256(firmware_path)
    except Exception as e:
        print(f"Failed to calculate firmware hash: {e}")
        return False

    print("Expected Hash   :", expected_hash)
    print("Calculated Hash :", calculated_hash)

    # Compare hashes
    if calculated_hash != expected_hash:
        print("\nHash Verification: FAILED")
        return False

    print("\nHash Verification: PASSED")

    # Verify digital signature
    try:
        engine = CryptoEngine(algorithm)

        signature_valid = engine.verify(
            firmware_path,
            signature_path,
            public_key_path
        )

    except Exception as e:
        print(f"Verification Error: {e}")
        return False

    if not signature_valid:
        print("Signature Verification: FAILED")
        return False

    print("Signature Verification: PASSED")

    print("\nFirmware Verification: PASS")
    return True


if __name__ == "__main__":

    firmware = "firmware/firmware.bin"
    metadata = "metadata/metadata.json"
    signature = "firmware/rsa.sig"      # Change to ecdsa.sig if testing ECDSA
    public_key = "keys/public_key.pem"

    result = verify_firmware(
        firmware,
        metadata,
        signature,
        public_key
    )

    if result:
        print("\nPASS")
    else:
        print("\nFAIL")