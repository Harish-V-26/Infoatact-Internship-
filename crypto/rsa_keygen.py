from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

# Create keys directory if it does not exist
os.makedirs("keys", exist_ok=True)

# Generate RSA-2048 private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Generate public key
public_key = private_key.public_key()

# Save private key
with open("keys/private_key.pem", "wb") as private_file:
    private_file.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# Save public key
with open("keys/public_key.pem", "wb") as public_file:
    public_file.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print("RSA-2048 key pair generated successfully!")
