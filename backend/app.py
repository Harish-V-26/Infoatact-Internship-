from flask import Flask, jsonify, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib
import os
import json
from datetime import datetime
app = Flask(__name__)

API_KEY = "infotact-secret-key"

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
REGISTRY_FILE = os.path.join(os.path.dirname(__file__), 
"firmware_registry.json")

def verify_api_key():
    api_key = request.headers.get("X-API-KEY")
    return api_key == API_KEY

def calculate_sha256(filepath):

    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()
def update_registry(filename, sha256_hash):
    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)

    version = f"1.0.{registry['total_releases'] + 1}"

    entry = {
        "version": version,
        "filename": filename,
        "sha256": sha256_hash,
        "upload_timestamp": datetime.utcnow().isoformat(),
        "is_latest": True
    }

    for v in registry["versions"]:
        v["is_latest"] = False

    registry["versions"].append(entry)
    registry["latest_version"] = version
    registry["total_releases"] += 1

    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=4)

@app.route("/")
def home():
    return jsonify({
        "message": "OTA Mock Server Running"
    })
@app.route("/manifest.json")
def manifest():

    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)

    return jsonify({
        "manifest_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "latest_version": registry["latest_version"],
        "total_releases": registry["total_releases"]
    })
@app.route("/version/check")
def version_check():

    current_version = request.args.get("current", "0.0.0")

    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)

    latest_version = registry["latest_version"]

    return jsonify({
        "update_available": current_version != latest_version,
        "current_version": current_version,
        "latest_version": latest_version
    })

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    sha256_hash = calculate_sha256(filepath)
    update_registry(file.filename, sha256_hash)

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