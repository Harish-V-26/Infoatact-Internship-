import json
import base64
import hashlib
from datetime import datetime, UTC


def create_signature_bundle(
    algorithm,
    firmware_path,
    signature_path,
    key_fingerprint,
    firmware_version,
    output_path
):
    # Calculate firmware SHA-256
    with open(firmware_path, "rb") as file:
        firmware_data = file.read()

    firmware_hash = hashlib.sha256(
        firmware_data
    ).hexdigest()

    # Read signature
    with open(signature_path, "rb") as file:
        signature = file.read()

    # Convert signature to Base64
    signature_b64 = base64.b64encode(
        signature
    ).decode()

    # Create JSON structure
    bundle = {
        "algorithm": algorithm,
        "key_fingerprint": key_fingerprint,
        "firmware_hash": firmware_hash,
        "signature_b64": signature_b64,
        "signed_at": datetime.now(UTC).isoformat(),
        "firmware_version": firmware_version
    }

    # Save JSON file
    with open(output_path, "w") as file:
        json.dump(
            bundle,
            file,
            indent=4
        )

    print(
        f"Signature bundle saved to {output_path}"
    )


# Example test
if __name__ == "__main__":
    create_signature_bundle(
        algorithm="ECDSA-P256-SHA256",
        firmware_path="firmware.bin",
        signature_path="ecdsa.sig",
        key_fingerprint="TEST:FINGERPRINT",
        firmware_version="1.0.0",
        output_path="ecdsa.sig.json"
    )