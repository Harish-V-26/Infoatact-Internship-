import json
import os

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

    data[version] = {
        "filename": filename
    }

    save_registry(data)

def get_latest_version():
    data = load_registry()

    if not data:
        return None

    return list(data.keys())[-1]