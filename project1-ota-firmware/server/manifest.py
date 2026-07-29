import json
import hashlib

def calculate_sha256(filepath):
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()

def generate_manifest(version, filename, filepath):
    return {
    "version": version,
    "filename": filename,
    "sha256": calculate_sha256(filepath),
    "build_number": 1,
    "uploaded_at": "2026-07-06T00:00:00Z"
}
    

def save_manifest(manifest_data, output_file="manifest.json"):
    with open(output_file, "w") as f:
        json.dump(manifest_data, f, indent=4)