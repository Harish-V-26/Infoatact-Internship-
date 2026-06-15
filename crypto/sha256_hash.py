import hashlib
import sys

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


if len(sys.argv) != 2:
    print("Usage: py sha256_hash.py <file>")
    exit()

hash_value = calculate_sha256(sys.argv[1])

print("SHA-256 Hash:")
print(hash_value)
