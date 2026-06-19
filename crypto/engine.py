from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, ec
from cryptography.exceptions import InvalidSignature


class CryptoEngine:
    def __init__(self, algorithm):
        self.algorithm = algorithm.upper()

        if self.algorithm not in ["RSA", "ECDSA"]:
            raise ValueError("Unsupported algorithm. Use RSA or ECDSA")

    def sign(self, firmware_path, key_path, output_sig_path):
        # Read firmware data
        with open(firmware_path, "rb") as file:
            data = file.read()

        # Load private key
        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )

        # RSA-PSS Signing
        if self.algorithm == "RSA":
            signature = private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

        # ECDSA Signing
        elif self.algorithm == "ECDSA":
            signature = private_key.sign(
                data,
                ec.ECDSA(hashes.SHA256())
            )

        # Save signature
        with open(output_sig_path, "wb") as sig_file:
            sig_file.write(signature)

        print(f"{self.algorithm} signature generated successfully!")

    def verify(self, firmware_path, sig_path, public_key_path):
        # Read firmware
        with open(firmware_path, "rb") as file:
            data = file.read()

        # Read signature
        with open(sig_path, "rb") as sig_file:
            signature = sig_file.read()

        # Load public key
        with open(public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read()
            )

        try:
            # RSA-PSS Verification
            if self.algorithm == "RSA":
                public_key.verify(
                    signature,
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )

            # ECDSA Verification
            elif self.algorithm == "ECDSA":
                public_key.verify(
                    signature,
                    data,
                    ec.ECDSA(hashes.SHA256())
                )

            print("Signature verification successful!")
            return True

        except InvalidSignature:
            print("Signature verification failed!")
            return False