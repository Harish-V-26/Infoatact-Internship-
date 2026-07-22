# Week 1 -- Mock Distribution Server (Placeholder)
# Simple Flask server to simulate OTA firmware distribution
# Full implementation due Week 2
# Owner: Member 2 (DevOps)

from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# Directory where signed firmware bundles will be stored
FIRMWARE_DIR = os.path.join(os.path.dirname(__file__), "firmware_store")
os.makedirs(FIRMWARE_DIR, exist_ok=True)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint -- confirms server is running."""
    return jsonify({"status": "ok", "message": "OTA Distribution Server is running"})
@app.route("/firmware/latest", methods=["GET"])
def latest_firmware():
    files = os.listdir(FIRMWARE_DIR)

    if not files:
        return jsonify({"error": "No firmware found"}), 404

    latest = files[0]

    return jsonify({
        "version": "1.0.1",
        "filename": latest,
        "download_url": f"http://127.0.0.1:5000/firmware/{latest}"
    })


@app.route("/firmware/<filename>", methods=["GET"])
def serve_firmware(filename):
    """
    Serves a firmware file from the firmware store.
    Edge agent will call this endpoint to download updates.
    """
    return send_from_directory(FIRMWARE_DIR, filename)



@app.route("/firmware", methods=["GET"])
def list_firmware():
    files = os.listdir(FIRMWARE_DIR)
    return jsonify({"available_firmware": files})


if __name__ == "__main__":
    print("[*] Starting OTA Mock Distribution Server on http://localhost:5000")
    print("[*] Firmware store directory:", FIRMWARE_DIR)
    app.run(debug=True, port=5000)
