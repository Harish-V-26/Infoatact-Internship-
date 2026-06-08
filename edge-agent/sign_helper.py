import argparse
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def sign_hash(private_key_path, firmware_hash_hex):
    # 1. Convert the hex string hash back into raw bytes
    try:
        hash_bytes = bytes.fromhex(firmware_hash_hex)
    except ValueError:
        raise ValueError("The provided firmware hash must be a valid hexadecimal string.")

    # 2. Load the private key from the specified path
    with open(private_key_path, "rb") as key_file:
        private_key = load_pem_private_key(
            key_file.read(),
            password=None  # Change this if your test private key is password-protected
        )

    # 3. Sign the hash
    # Note: Prehashed padding is used because the firmware is already hashed
    signature = private_key.sign(
        hash_bytes,
        padding.PKCS1v15(),
        utils.Prehashed(hashes.SHA256()) # Adjust to hashes.SHA512() if using SHA-512
    )

    # 4. Base64 encode the resulting raw signature
    base64_signature = base64.b64encode(signature)
    return base64_signature

if __name__ == "__main__":
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(description="Sign a firmware hash using an RSA private key.")
    parser.add_argument("-k", "--key", required=True, help="Path to the private key file (.pem)")
    parser.add_argument("-hash", "--hash", required=True, help="The firmware hash in hex format")
    parser.add_argument("-o", "--output", default="firmware.sig", help="Output .sig file path")

    args = parser.parse_args()
    from cryptography.hazmat.primitives.asymmetric import utils

    try:
        sig_data = sign_hash(args.key, args.hash)
        
        # Write the base64 signature to the output file
        with open(args.output, "wb") as sig_file:
            sig_file.write(sig_data)
            
        print(f"[✓] Successfully generated signature file: {args.output}")
    except Exception as e:
        print(f"[✗] Error: {e}")
