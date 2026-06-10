# Week 1 — OTA Mock Distribution Server
# Owner: Jagadesh (Backend/DevOps)
# Branch: jagadesh-backend
# Serves signed firmware bundles to the Edge Agent

from flask import Flask, jsonify, request, send_from_directory
import os

app = Flask(__name__)

# Directory where signed firmware bundles are stored
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    """Health check — confirms OTA server is running."""
    return jsonify({
        "message": "OTA Mock Server Running",
        "status": "ok"
    })


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Receives signed firmware bundle from CI/CD pipeline.
    Expected: multipart/form-data with 'file' field.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    return jsonify({
        "status": "success",
        "filename": file.filename,
        "message": f"Firmware '{file.filename}' uploaded successfully"
    })


@app.route("/download/<filename>")
def download_file(filename):
    """
    Serves firmware file to the Edge Agent for download and verification.
    """
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/firmware", methods=["GET"])
def list_firmware():
    """Lists all available firmware bundles on the server."""
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({"available_firmware": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("[*] Starting OTA Mock Distribution Server on http://localhost:5000")
    print("[*] Upload directory:", UPLOAD_FOLDER)
    app.run(host="0.0.0.0", port=5000, debug=True)
