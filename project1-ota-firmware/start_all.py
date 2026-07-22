"""
One-Command System Launcher
Owner: Harish (Lead)

Starts the REAL server, generates + signs a real firmware bundle,
places it where the server can serve it, then runs the REAL edge
agent against it -- all with a single command.

Run with: python start_all.py
Requires: pip install flask requests cryptography
"""

import os
import sys
import subprocess

# --- Auto-install required packages if missing ---
REQUIRED_PACKAGES = ["flask", "requests", "cryptography"]

def ensure_dependencies():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Missing dependencies detected: {missing}. Installing automatically...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("[*] All dependencies installed successfully!\n")

ensure_dependencies()

import time
import shutil
import hashlib
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(ROOT, "server")
CRYPTO_DIR = os.path.join(ROOT, "crypto")
EDGE_DIR = os.path.join(ROOT, "edge-agent")
UPLOAD_DIR = os.path.join(SERVER_DIR, "uploads")



def step(msg):
    print(f"\n{'=' * 60}\n{msg}\n{'=' * 60}")


def kill_stale_server():
    """Kill any process already listening on port 5000 and wait until the port is free."""
    import time
    for attempt in range(5):
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            pids = set()
            for line in result.stdout.splitlines():
                if ":5000" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    pids.add(pid)
            if not pids:
                break  # Port is free
            for pid in pids:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                print(f"      Killed stale server (PID: {pid})")
            time.sleep(1)
        except Exception:
            break


def start_server():
    """Starts server/app.py as a background subprocess."""
    step("[1/5] Starting OTA distribution server (server/app.py)")
    kill_stale_server()
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=SERVER_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    print("      Server started in background (PID: %s)" % proc.pid)
    return proc


def cleanup_stale_files():
    """Remove stale uploads, downloads, and old keys to ensure a clean run."""
    step("[0/5] Cleaning up stale files from previous runs")
    stale_files = [
        os.path.join(ROOT, "private_key.pem"),
        os.path.join(CRYPTO_DIR, "public_key.pem"),
        os.path.join(EDGE_DIR, "firmware.sig"),
    ]
    for f in stale_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"      Removed: {f}")
    for d in [UPLOAD_DIR, os.path.join(EDGE_DIR, "downloads")]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"      Cleared: {d}")
    print("      Cleanup done.")


def generate_keys():
    step("[2/5] Generating RSA key pair (crypto/keygen.py)")
    subprocess.run([sys.executable, os.path.join("crypto", "keygen.py")], cwd=ROOT, check=True)
    print("      private_key.pem and crypto/public_key.pem ready")


def build_and_sign_firmware():
    step("[3/5] Building and signing firmware v1.0.0")

    firmware_path = os.path.join(EDGE_DIR, "dummy_firmware.bin")
    if not os.path.exists(firmware_path):
        with open(firmware_path, "wb") as f:
            f.write(b"OTA_FW Cargo Tracker Firmware v1.0.0" * 5)

    hasher = hashlib.sha256()
    with open(firmware_path, "rb") as f:
        hasher.update(f.read())
    firmware_hash = hasher.hexdigest()

    private_key_path = os.path.join(ROOT, "private_key.pem")
    sig_path = os.path.join(EDGE_DIR, "firmware.sig")

    subprocess.run(
        [
            sys.executable, "signer.py",
            "-k", private_key_path,
            "-f", firmware_path,
            "-o", sig_path
        ],
        cwd=EDGE_DIR,
        check=True
    )
    print(f"      Signed. SHA-256: {firmware_hash[:16]}...")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    shutil.copy(firmware_path, os.path.join(UPLOAD_DIR, "v1.0.0.bin"))
    shutil.copy(sig_path, os.path.join(UPLOAD_DIR, "v1.0.0.sig"))
    print("      Bundle placed in server/uploads/")


def run_agent():
    step("[4/5] Running the real Edge Agent (edge-agent/agent.py)")
    subprocess.run([sys.executable, "agent.py"], cwd=EDGE_DIR, check=False)


def main():
    print("=" * 60)
    print("OTA FIRMWARE SECURITY - ONE-COMMAND SYSTEM LAUNCH")
    print("=" * 60)

    cleanup_stale_files()
    server_proc = start_server()

    try:
        generate_keys()
        build_and_sign_firmware()
        run_agent()

        step("[5/5] Done. Check edge-agent/state.json and edge-agent/logs/")

    finally:
        print("\nShutting down server...")
        server_proc.terminate()


if __name__ == "__main__":
    main()
