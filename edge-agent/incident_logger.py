"""
Edge Agent - Incident Logger
Owner: Rishi (Edge Agent / QA)

Writes a detailed incident report to edge-agent/logs/ whenever
the agent's state machine fails at any stage (download, hash
mismatch, signature failure, server unreachable, etc).
"""

import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def log_incident(state_at_failure, firmware_version, reason, action_taken, alert_level="WARNING"):
    """
    alert_level: INFO | WARNING | CRITICAL
    """
    timestamp = datetime.now(timezone.utc)
    incident_id = f"INC-{timestamp.strftime('%Y%m%d%H%M%S')}"

    incident = {
        "incident_id": incident_id,
        "timestamp": timestamp.isoformat(),
        "state_at_failure": state_at_failure,
        "firmware_version": firmware_version,
        "failure_reason": reason,
        "action_taken": action_taken,
        "alert_level": alert_level
    }

    filepath = os.path.join(LOG_DIR, f"{incident_id}.json")
    with open(filepath, "w") as f:
        json.dump(incident, f, indent=2)

    print(f"[{alert_level}] Incident logged: {incident_id} -> {filepath}")
    return incident
