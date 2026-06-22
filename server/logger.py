import json
import os
from datetime import datetime

LOG_FILE = "server/logs/access_log.json"


def log_request(data):
    os.makedirs("server/logs", exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }

    logs = []

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)