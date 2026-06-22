from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os

# Create keys directory if it does not exist
os.makedirs("keys", exist_ok=True)

# Generate ECDSA P-256 private key
private_key = ec.generate_private_key(ec.SECP256R1())

# Generate public key
public_key = private_key.public_key()

# Save private key
with open("keys/ecdsa_private.pem", "wb") as private_file:
    private_file.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# Save public key
with open("crypto/ecdsa_public.pem", "wb") as public_file:
    public_file.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print("ECDSA P-256 key pair generated successfully!")
print("RSA-2048 signature size : 256 bytes")
print("ECDSA-P256 signature size : ~72 bytes")
