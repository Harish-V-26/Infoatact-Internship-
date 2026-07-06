import json
import os
import argparse
from datetime import datetime, timezone

AUDIT_FILE = "docs/signing_history.json"


def load_history():
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "total_releases": 0}


def write_entry(version, run_id, hash_file):
    history = load_history()

    firmware_hash = "unknown"
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            firmware_hash = f.read().strip()

    entry = {
        "entry_id": len(history["history"]) + 1,
        "firmware_version": version,
        "run_id": run_id,
        "firmware_hash": firmware_hash,
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_status": "success",
        "signed_by": "GitHub Actions CI/CD"
    }

    history["history"].append(entry)
    history["total_releases"] = len(history["history"])
    history["last_release"] = version

    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)

    with open(AUDIT_FILE, "w") as f:
        json.dump(history, f, indent=2)

    print(f"[OK] Audit entry written for version {version}")
    print(f"[OK] Total releases recorded: {history['total_releases']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hash-file", required=True)
    args = parser.parse_args()

    write_entry(args.version, args.run_id, args.hash_file)
