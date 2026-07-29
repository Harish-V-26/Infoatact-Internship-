from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# 1. Load the private key (Ensure private_key.pem is in the same folder!)
try:
    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
except FileNotFoundError:
    print("Error: 'private_key.pem' not found. Please get this from Sourish.")
    exit()

# 2. Read the firmware file
try:
    with open("firmware_v1.bin", "rb") as f:
        firmware_data = f.read()
except FileNotFoundError:
    print("Error: 'firmware_v1.bin' not found. Ensure the file exists.")
    exit()

# 3. Sign the data (Hashing and Signing combined)
signature = private_key.sign(
    firmware_data,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH  
    ),
    hashes.SHA256()
)

# 4. Save the signature file
with open("firmware_v1.sig", "wb") as sig_file:
    sig_file.write(signature)

print("Success! 'firmware_v1.sig' has been created.")
