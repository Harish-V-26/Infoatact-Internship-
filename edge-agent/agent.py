"""
Edge Agent - Real State Machine
Owner: Rishi (Edge Agent / QA)

Connects to the REAL OTA server (server/app.py) and uses the REAL
CryptoEngine (crypto/engine.py) for signature verification.
No more mocked manifest or fake hash-only checks.

States: IDLE -> POLLING -> DOWNLOADING -> VERIFYING -> APPLYING -> IDLE/FAULT

Run with: python edge-agent/agent.py
Requires: server/app.py running on http://localhost:5000
          pip install requests cryptography
"""

import os
import sys
import time
import json
import hashlib
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crypto"))

# Helper functions for Semantic Versioning
def version_tuple(v):
    # Converts "1.0.2" to (1, 0, 2) for numeric comparison
    return tuple(int(x) for x in v.split('.'))

def is_newer(candidate, current):
    # Returns True if candidate version is strictly greater than current
    return version_tuple(candidate) > version_tuple(current)

from engine import CryptoEngine  # noqa: E402
from incident_logger import log_incident  # noqa: E402

SERVER_URL = "http://localhost:5000"
PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto", "public_key.pem")
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
CHUNK_SIZE = 4096

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class EdgeAgent:
    def __init__(self, current_version="0.0.0"):
        self.state = "IDLE"
        self.manifest = None
        self.current_version = current_version
        self._save_state()
        print(f"[STATE] Agent started. Current version: {self.current_version}")

    def _save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump({
                "current_state": self.state,
                "firmware_version": self.current_version
            }, f, indent=2)

    def change_state(self, new_state):
        print(f"\n[STATE TRANSITION] {self.state} --> {new_state}")
        self.state = new_state
        self._save_state()

    # ── Module 1: Real Manifest Poller ──────────────────────────
    def poll_manifest(self):
        self.change_state("POLLING")
        print(f"[POLLER] Checking {SERVER_URL}/manifest.json for updates...")

        try:
            resp = requests.get(f"{SERVER_URL}/manifest.json", timeout=5)
            if resp.status_code != 200:
                log_incident(self.state, self.current_version,
                             f"Manifest endpoint returned {resp.status_code}",
                             "Staying on current version", "WARNING")
                self.change_state("IDLE")
                return False

            self.manifest = resp.json()
            latest_version = self.manifest.get("version", "unknown")
            print(f"[POLLER] Found firmware version: {latest_version}")

            if latest_version == self.current_version:
                print("[POLLER] Already up to date. No action needed.")
                self.change_state("IDLE")
                return False

            return True

        except requests.exceptions.RequestException as e:
            log_incident(self.state, self.current_version,
                         f"Server unreachable: {e}",
                         "Staying on current version", "INFO")
            self.change_state("IDLE")
            return False

    # ── Module 2: Real Chunked Downloader ───────────────────────
    def download_firmware(self):
        self.change_state("DOWNLOADING")
        download_url = SERVER_URL + self.manifest["download_url"]
        filename = self.manifest["filename"]
        local_path = os.path.join(DOWNLOAD_DIR, filename)

        print(f"[DOWNLOADER] Fetching {download_url} in {CHUNK_SIZE}-byte chunks...")

        try:
            resp = requests.get(download_url, stream=True, timeout=10)
            if resp.status_code != 200:
                raise requests.exceptions.RequestException(f"HTTP {resp.status_code}")

            hasher = hashlib.sha256()
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        hasher.update(chunk)

            downloaded_hash = hasher.hexdigest()
            print(f"[DOWNLOADER] Download complete. Computed hash: {downloaded_hash[:16]}...")

            return local_path, downloaded_hash

        except requests.exceptions.RequestException as e:
            log_incident(self.state, self.manifest.get("version"),
                         f"Download failed: {e}",
                         "Discarding partial file, keeping current version", "WARNING")
            if os.path.exists(local_path):
                os.remove(local_path)
            self.change_state("FAULT")
            return None, None

    # ── Module 3: Real Signature Verification via CryptoEngine ──
    def verify_and_apply(self, firmware_path, downloaded_hash):
        self.change_state("VERIFYING")

        expected_hash = self.manifest.get("sha256")
        print(f"[SECURITY] Layer 1 - Hash check: downloaded vs manifest")
        print(f"  Downloaded: {downloaded_hash}")
        print(f"  Expected:   {expected_hash}")

        if downloaded_hash != expected_hash:
            log_incident("VERIFYING", self.manifest.get("version"),
                         "SHA-256 mismatch - download corrupted or tampered",
                         "Payload discarded - rollback to current version", "CRITICAL")
            os.remove(firmware_path)
            self.change_state("FAULT")
            return

        sig_url = self.manifest.get("signature_url")
        if not sig_url:
            log_incident("VERIFYING", self.manifest.get("version"),
                         "No signature available for this firmware",
                         "Payload discarded - signature required", "CRITICAL")
            os.remove(firmware_path)
            self.change_state("FAULT")
            return

        sig_resp = requests.get(SERVER_URL + sig_url, timeout=5)
        sig_path = firmware_path + ".sig"
        with open(sig_path, "wb") as f:
            f.write(sig_resp.content)

        print("[SECURITY] Layer 2 - Digital signature verification (CryptoEngine)")
        engine = CryptoEngine(algorithm="RSA")
        is_valid = engine.verify(firmware_path, sig_path, PUBLIC_KEY_PATH)

        if is_valid:
            print("\n[SUCCESS] Signature verified. Applying update.")
            self.change_state("APPLYING")
            self.current_version = self.manifest["version"]
            self._save_state()
            print(f"[APPLY] Firmware updated to version {self.current_version}")
            self.change_state("IDLE")
        else:
            log_incident("VERIFYING", self.manifest.get("version"),
                         "Digital signature verification failed - possible tampering",
                         "Payload discarded - remaining on current version", "CRITICAL")
            os.remove(firmware_path)
            os.remove(sig_path)
            self.change_state("FAULT")

    def run_cycle(self):
        if self.poll_manifest():
            firmware_path, downloaded_hash = self.download_firmware()
            if firmware_path:
                self.verify_and_apply(firmware_path, downloaded_hash)


if __name__ == "__main__":
    agent = EdgeAgent(current_version="0.0.0")
    agent.run_cycle()
