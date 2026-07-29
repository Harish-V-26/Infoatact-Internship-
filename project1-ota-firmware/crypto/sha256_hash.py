import hashlib
import sys


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py sha256_hash.py <file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        hash_value = calculate_sha256(file_path)

        print("SHA-256 Hash:")
        print(hash_value)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)