"""
Edge Agent - Secure OTA State Machine
Owner: Rishi (Edge Agent / QA) + Harish (Integration)

States: IDLE -> POLLING -> DOWNLOADING -> VERIFYING -> APPLYING -> IDLE
                                              |
                                           FAULT (on any failure)

Run with: python edge-agent/agent.py
Requires: server/app.py running on http://localhost:5000
          pip install requests cryptography
"""

import os
import sys
import json
import hashlib
import requests

# Fix import path — works regardless of which directory you run from
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
CRYPTO_DIR = os.path.join(AGENT_DIR, "..", "crypto")
sys.path.insert(0, CRYPTO_DIR)
sys.path.insert(0, AGENT_DIR)

from engine import CryptoEngine          # noqa: E402
from incident_logger import log_incident  # noqa: E402

SERVER_URL = "http://localhost:5000"
PUBLIC_KEY_PATH = os.path.join(CRYPTO_DIR, "public_key.pem")
STATE_FILE = os.path.join(AGENT_DIR, "state.json")
DOWNLOAD_DIR = os.path.join(AGENT_DIR, "downloads")
CHUNK_SIZE = 4096

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def version_tuple(v):
    """Convert 'v1.0.2' or '1.0.2' -> (1, 0, 2) for correct numeric comparison."""
    v = v.lstrip("vV")
    return tuple(int(x) for x in v.split("."))


def is_newer(candidate, current):
    """Return True only if candidate is strictly newer than current."""
    return version_tuple(candidate) > version_tuple(current)


class EdgeAgent:

    def __init__(self, current_version="0.0.0"):
        self.state = "IDLE"
        self.manifest = None
        self.current_version = current_version
        self._save_state()
        print(f"[AGENT] Started. Current version: {self.current_version}")

    def _save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump({
                "current_state": self.state,
                "firmware_version": self.current_version
            }, f, indent=2)

    def change_state(self, new_state):
        print(f"\n[STATE] {self.state} --> {new_state}")
        self.state = new_state
        self._save_state()

    # ── POLLING ─────────────────────────────────────────────────
    def poll_manifest(self):
        self.change_state("POLLING")
        print(f"[POLLER] Checking {SERVER_URL}/manifest.json ...")

        try:
            resp = requests.get(f"{SERVER_URL}/manifest.json", timeout=5)

            if resp.status_code != 200:
                log_incident(self.state, self.current_version,
                             f"Manifest returned HTTP {resp.status_code}",
                             "Staying on current version", "WARNING")
                self.change_state("IDLE")
                return False

            self.manifest = resp.json()
            latest = self.manifest.get("version", "unknown")
            print(f"[POLLER] Latest version on server: {latest}")
            print(f"[POLLER] Current installed version: {self.current_version}")

            # Anti-rollback: reject if server offers same or older version
            if not is_newer(latest, self.current_version):
                if latest == self.current_version:
                    print("[POLLER] Already up to date. Nothing to do.")
                else:
                    print(f"[POLLER] ROLLBACK BLOCKED: {latest} <= {self.current_version}")
                    log_incident(self.state, latest,
                                 f"Rollback attempt: offered {latest} <= current {self.current_version}",
                                 "Staying on current version", "WARNING")
                self.change_state("IDLE")
                return False

            print(f"[POLLER] New version available: {latest}. Proceeding to download.")
            return True

        except requests.exceptions.RequestException as e:
            log_incident(self.state, self.current_version,
                         f"Server unreachable: {e}",
                         "Staying on current version", "INFO")
            self.change_state("IDLE")
            return False

    # ── DOWNLOADING ──────────────────────────────────────────────
    def download_firmware(self):
        self.change_state("DOWNLOADING")
        download_url = SERVER_URL + self.manifest["download_url"]
        filename = self.manifest.get("filename", "firmware.bin")
        local_path = os.path.join(DOWNLOAD_DIR, filename)

        print(f"[DOWNLOAD] Fetching: {download_url}")
        print(f"[DOWNLOAD] Saving to: {local_path}")

        try:
            resp = requests.get(download_url, stream=True, timeout=10)
            if resp.status_code != 200:
                raise requests.exceptions.RequestException(f"HTTP {resp.status_code}")

            hasher = hashlib.sha256()
            total_bytes = 0

            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        hasher.update(chunk)
                        total_bytes += len(chunk)

            downloaded_hash = hasher.hexdigest()
            print(f"[DOWNLOAD] Complete. {total_bytes} bytes received.")
            print(f"[DOWNLOAD] SHA-256: {downloaded_hash[:24]}...")
            return local_path, downloaded_hash

        except requests.exceptions.RequestException as e:
            log_incident(self.state, self.manifest.get("version"),
                         f"Download failed: {e}",
                         "Discarding partial file, keeping current version", "WARNING")
            if os.path.exists(local_path):
                os.remove(local_path)
            self.change_state("FAULT")
            return None, None

    # ── VERIFYING ────────────────────────────────────────────────
    def verify_and_apply(self, firmware_path, downloaded_hash):
        self.change_state("VERIFYING")

        # Layer 1 — SHA-256 hash check
        expected_hash = self.manifest.get("sha256")
        print(f"\n[VERIFY] Layer 1 — SHA-256 hash check")
        print(f"  Downloaded : {downloaded_hash}")
        print(f"  Expected   : {expected_hash}")

        if downloaded_hash != expected_hash:
            log_incident("VERIFYING", self.manifest.get("version"),
                         "SHA-256 mismatch — firmware corrupted or tampered in transit",
                         "Payload discarded — staying on current version", "CRITICAL")
            os.remove(firmware_path)
            self.change_state("FAULT")
            return

        print("[VERIFY] Layer 1 PASSED — hash matches")

        # Layer 2 — Digital signature check
        sig_url = self.manifest.get("signature_url")
        if not sig_url:
            log_incident("VERIFYING", self.manifest.get("version"),
                         "No signature URL in manifest — cannot verify authenticity",
                         "Payload discarded — signature required", "CRITICAL")
            os.remove(firmware_path)
            self.change_state("FAULT")
            return

        print(f"\n[VERIFY] Layer 2 — Digital signature verification (CryptoEngine RSA)")
        sig_resp = requests.get(SERVER_URL + sig_url, timeout=5)
        sig_path = firmware_path + ".sig"
        with open(sig_path, "wb") as f:
            f.write(sig_resp.content)

        if not os.path.exists(PUBLIC_KEY_PATH):
            log_incident("VERIFYING", self.manifest.get("version"),
                         f"Public key not found at: {PUBLIC_KEY_PATH}",
                         "Cannot verify signature — payload discarded", "CRITICAL")
            self.change_state("FAULT")
            return

        engine = CryptoEngine(algorithm="RSA")
        is_valid = engine.verify(firmware_path, sig_path, PUBLIC_KEY_PATH)

        if is_valid:
            print("[VERIFY] Layer 2 PASSED — signature is authentic")
            self.change_state("APPLYING")
            self.current_version = self.manifest["version"]
            self._save_state()
            print(f"\n[APPLY] Firmware installed successfully.")
            print(f"[APPLY] Device is now running version: {self.current_version}")
            self.change_state("IDLE")
        else:
            log_incident("VERIFYING", self.manifest.get("version"),
                         "Digital signature INVALID — firmware may have been tampered with",
                         "Payload discarded — staying on current version", "CRITICAL")
            os.remove(firmware_path)
            if os.path.exists(sig_path):
                os.remove(sig_path)
            self.change_state("FAULT")

    # ── MAIN CYCLE ───────────────────────────────────────────────
    def run_cycle(self):
        """Run one complete update check cycle."""
        if self.poll_manifest():
            firmware_path, downloaded_hash = self.download_firmware()
            if firmware_path:
                self.verify_and_apply(firmware_path, downloaded_hash)


if __name__ == "__main__":
    agent = EdgeAgent(current_version="0.0.0")
    agent.run_cycle()
