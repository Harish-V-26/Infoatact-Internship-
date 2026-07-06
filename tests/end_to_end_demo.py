"""
Week 3 - End-to-End Demo Script
Owner: Harish (Lead)

Runs the FULL real chain on one machine:
  1. Starts Jagadesh's mock OTA server in a background thread
  2. Generates a real RSA key pair
  3. Creates dummy firmware + computes SHA-256 hash
  4. Signs the firmware
  5. Uploads the signed bundle to the live server (/upload)
  6. Downloads it back from the server (/download/<filename>)
  7. Verifies hash + signature on the downloaded copy
  8. Prints a clear PASS/FAIL demo report

This is the script to run live during Mid Review / Final Review demos.

Run with: python tests/end_to_end_demo.py
Requires: pip install flask requests cryptography
"""

import os
import sys
import time
import hashlib
import threading
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

RESULTS = []


def check(name, passed, detail=""):
    symbol = "PASS" if passed else "FAIL"
    RESULTS.append({"name": name, "passed": passed})
    print(f"  [{symbol}] {name}" + (f" - {detail}" if detail else ""))
    return passed


def start_server_in_background(upload_dir):
    """Starts a minimal version of Jagadesh's server in-process,
    pointed at a temporary upload directory for this demo run."""
    from flask import Flask, jsonify, request, send_from_directory

    app = Flask(__name__)

    @app.route("/")
    def home():
        return jsonify({"status": "ok"})

    @app.route("/upload", methods=["POST"])
    def upload_file():
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        save_path = os.path.join(upload_dir, file.filename)
        file.save(save_path)
        return jsonify({"status": "success", "filename": file.filename})

    @app.route("/download/<filename>")
    def download_file(filename):
        return send_from_directory(upload_dir, filename, as_attachment=True)

    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5099, debug=False, use_reloader=False),
        daemon=True
    )
    thread.start()
    time.sleep(1.5)  # give Flask time to bind the port
    return thread


def main():
    print("=" * 60)
    print("OTA FIRMWARE SECURITY - FULL END-TO-END LIVE DEMO")
    print("=" * 60)

    tmp_dir = tempfile.mkdtemp(prefix="ota_demo_")
    upload_dir = os.path.join(tmp_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    try:
        import requests
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature
        import base64

        # Step 1 - Start the live mock server
        print("\n[1] Starting mock OTA distribution server on :5099")
        start_server_in_background(upload_dir)
        try:
            health = requests.get("http://127.0.0.1:5099/", timeout=3)
            check("Server is reachable", health.status_code == 200)
        except Exception as e:
            check("Server is reachable", False, str(e))
            return 1

        # Step 2 - Generate real key pair
        print("\n[2] Generating RSA-2048 key pair")
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        check("Key pair generated", True)

        # Step 3 - Create dummy firmware + hash it
        print("\n[3] Creating dummy firmware and computing SHA-256")
        firmware_path = os.path.join(tmp_dir, "demo_firmware_v1.0.0.bin")
        with open(firmware_path, "wb") as f:
            f.write(b"OTA_FW Demo IoT Cargo Tracker Firmware v1.0.0" * 5)

        with open(firmware_path, "rb") as f:
            firmware_bytes = f.read()
        firmware_hash = hashlib.sha256(firmware_bytes).digest()
        check("Firmware hashed", True, f"sha256={firmware_hash.hex()[:16]}...")

        # Step 4 - Sign the firmware
        print("\n[4] Signing firmware with private key")
        signature = private_key.sign(
            firmware_hash,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        sig_path = os.path.join(tmp_dir, "demo_firmware_v1.0.0.sig")
        with open(sig_path, "wb") as f:
            f.write(base64.b64encode(signature))
        check("Firmware signed", os.path.getsize(sig_path) > 0)

        # Step 5 - Upload signed firmware to the LIVE server
        print("\n[5] Uploading signed firmware to live server")
        with open(firmware_path, "rb") as f:
            resp = requests.post(
                "http://127.0.0.1:5099/upload",
                files={"file": ("demo_firmware_v1.0.0.bin", f)}
            )
        check("Upload accepted by server", resp.status_code == 200, f"status={resp.status_code}")

        # Step 6 - Download it back from the server
        print("\n[6] Downloading firmware back from live server")
        download_resp = requests.get("http://127.0.0.1:5099/download/demo_firmware_v1.0.0.bin")
        check("Download succeeded", download_resp.status_code == 200)
        downloaded_bytes = download_resp.content

        # Step 7 - Verify integrity + signature on the DOWNLOADED copy
        print("\n[7] Verifying downloaded firmware (hash + signature)")
        downloaded_hash = hashlib.sha256(downloaded_bytes).digest()
        check("Downloaded hash matches original", downloaded_hash == firmware_hash)

        try:
            public_key.verify(
                signature,
                downloaded_hash,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            check("Signature verification passed", True)
        except InvalidSignature:
            check("Signature verification passed", False)

        # Summary
        print("\n" + "=" * 60)
        print("END-TO-END DEMO SUMMARY")
        print("=" * 60)
        passed = sum(1 for r in RESULTS if r["passed"])
        total = len(RESULTS)
        for r in RESULTS:
            print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['name']}")
        print("=" * 60)
        print(f"  Result: {passed}/{total} steps passed")
        if passed == total:
            print("  STATUS: FULL CHAIN WORKS END TO END")
        print("=" * 60)

        return 0 if passed == total else 1

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    exit(main())
