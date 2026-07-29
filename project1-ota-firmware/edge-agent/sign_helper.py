import argparse
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def sign_hash(private_key_path, firmware_hash_hex):
    """
    Signs a pre-computed SHA-256 firmware hash using an RSA private key.
    Args:
        private_key_path (str): Path to the PEM private key file.
        firmware_hash_hex (str): The SHA-256 hash of the firmware in hex format.
    Returns:
        bytes: Base64-encoded RSA signature.
    """
    # 1. Convert hex hash string back to raw bytes
    try:
        hash_bytes = bytes.fromhex(firmware_hash_hex)
    except ValueError:
        raise ValueError("The provided firmware hash must be a valid hexadecimal string.")

    # 2. Load the private key from the specified path
    with open(private_key_path, "rb") as key_file:
        private_key = load_pem_private_key(
            key_file.read(),
            password=None
        )

    # 3. Sign the pre-hashed data using PKCS1v15 with Prehashed
    signature = private_key.sign(
        hash_bytes,
        padding.PKCS1v15(),
        utils.Prehashed(hashes.SHA256())
    )

    # 4. Base64 encode the raw signature for safe storage/transport
    base64_signature = base64.b64encode(signature)
    return base64_signature


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sign a firmware hash using an RSA private key."
    )
    parser.add_argument("-k", "--key", required=True, help="Path to the private key file (.pem)")
    parser.add_argument("--hash", required=True, help="The firmware SHA-256 hash in hex format")
    parser.add_argument("-o", "--output", default="firmware.sig", help="Output .sig file path")

    args = parser.parse_args()

    try:
        sig_data = sign_hash(args.key, args.hash)
        with open(args.output, "wb") as sig_file:
            sig_file.write(sig_data)
        print(f"[[OK]] Signature saved to: {args.output}")
    except Exception as e:
        print(f"[[ERROR]] Signing failed: {e}")
