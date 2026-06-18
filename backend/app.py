from flask import Flask, jsonify, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib
import os
app = Flask(__name__)

API_KEY = "infotact-secret-key"

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def verify_api_key():
    api_key = request.headers.get("X-API-KEY")
    return api_key == API_KEY

def calculate_sha256(filepath):

    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()
@app.route("/")
def home():
    return jsonify({
        "message": "OTA Mock Server Running"
    })

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))

    return jsonify({
        "status": "success",
        "filename": file.filename
    })

@app.route("/download/<filename>")
@limiter.limit("5 per minute")
def download_file(filename):

    if not verify_api_key():
        return jsonify({
            "error": "Unauthorized"
        }), 401

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )
@app.route("/hash/<filename>")
def firmware_hash(filename):

    path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(path):
        return jsonify({
            "error": "File not found"
        }), 404

    return jsonify({
        "filename": filename,
        "sha256": calculate_sha256(path)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)