import os
import sys
import hashlib
import subprocess
from flask import Flask, jsonify, request, send_from_directory, render_template

# Fix import path so manifest.py is always found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import generate_manifest  # noqa: E402

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
EDGE_DIR = os.path.join(ROOT_DIR, "edge-agent")
PRIVATE_KEY_PATH = os.path.join(ROOT_DIR, "private_key.pem")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return jsonify({"message": "OTA Mock Server Running", "status": "ok"})


@app.route("/admin")
def admin_dashboard():
    return render_template("admin.html")


@app.route("/admin/deploy", methods=["POST"])
def admin_deploy():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    version = request.form.get("version", "").strip()
    if not version:
        return jsonify({"error": "Version is required"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
        
    # Ensure standard filename based on version
    filename = f"{version}.bin" if not version.endswith(".bin") else version
    sig_filename = filename.replace(".bin", ".sig")
    
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    sig_path = os.path.join(UPLOAD_FOLDER, sig_filename)
    
    file.save(save_path)
    
    # Sign the firmware automatically using signer.py
    try:
        subprocess.run(
            [
                sys.executable, "signer.py",
                "-k", PRIVATE_KEY_PATH,
                "-f", save_path,
                "-o", sig_path
            ],
            cwd=EDGE_DIR,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        # If signing fails, clean up the uploaded bin
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": f"Failed to sign firmware: {e.stderr}"}), 500

    return jsonify({
        "status": "success",
        "message": f"Firmware {version} successfully signed and deployed!"
    })


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Optional: verify hash if client sends X-Firmware-Hash header
    expected_hash = request.headers.get("X-Firmware-Hash")
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    if expected_hash:
        sha256 = hashlib.sha256()
        with open(save_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        computed = sha256.hexdigest()
        if computed != expected_hash:
            os.remove(save_path)
            return jsonify({
                "error": "Hash mismatch -- upload rejected",
                "expected": expected_hash,
                "computed": computed
            }), 400

    return jsonify({
        "status": "success",
        "filename": file.filename,
        "message": f"Firmware '{file.filename}' uploaded successfully"
    })


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/firmware", methods=["GET"])
def list_firmware():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({"available_firmware": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/manifest.json", methods=["GET"])
def get_manifest():
    """
    Live manifest endpoint polled by edge agents every 30 seconds.
    Returns latest firmware version, hash, download URL, and signature URL.
    """
    try:
        files = os.listdir(UPLOAD_FOLDER)
        bin_files = [f for f in files if f.endswith(".bin")]

        if not bin_files:
            return jsonify({"error": "No firmware available yet"}), 404

        bin_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(UPLOAD_FOLDER, f))
        )
        latest_file = bin_files[-1]
        latest_path = os.path.join(UPLOAD_FOLDER, latest_file)

        manifest = generate_manifest(
            version=os.path.splitext(latest_file)[0],
            filename=latest_file,
            filepath=latest_path
        )
        manifest["download_url"] = f"/download/{latest_file}"

        sig_filename = os.path.splitext(latest_file)[0] + ".sig"
        sig_path = os.path.join(UPLOAD_FOLDER, sig_filename)
        manifest["signature_url"] = (
            f"/download/{sig_filename}" if os.path.exists(sig_path) else None
        )

        return jsonify(manifest)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("[*] Starting OTA Mock Distribution Server on http://localhost:5000")
    print("[*] Upload directory:", UPLOAD_FOLDER)
    app.run(host="0.0.0.0", port=5000, debug=True)
