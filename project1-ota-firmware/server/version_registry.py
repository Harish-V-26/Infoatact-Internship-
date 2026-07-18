import json
import os
from datetime import datetime
def version_tuple(v):
    """
    Converts '1.0.0' -> (1, 0, 0)
    """
    return tuple(int(x) for x in v.split("."))


def is_newer_version(candidate, current):
    return version_tuple(candidate) > version_tuple(current)


REGISTRY_FILE = "firmware_registry.json"

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {}

    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def register_version(version, filename):
    data = load_registry()
    latest = get_latest_version()

    if latest and not is_newer_version(version, latest):
        raise ValueError(
            f"Rejected: {version} is not newer than current latest {latest}"
        )

    data[version] = {
        "filename": filename,
        "build_number": len(data) + 1,
        "uploaded_at": datetime.utcnow().isoformat() + "Z"
    }

    save_registry(data)

def get_latest_version():
    data = load_registry()

    if not data:
        return None
    
    latest = max(data.keys(), key=version_tuple)
    return latest
    