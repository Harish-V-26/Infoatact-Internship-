from flask import Flask, jsonify, request, send_from_directory
from manifest import generate_manifest
import os

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return jsonify({"message": "OTA Mock Server Running", "status": "ok"})


@app.route("/upload", methods=["POST"])
def upload_file():
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
    Live manifest endpoint. Edge agents poll this to discover
    the latest available firmware version, its hash, and where
    to download it + its signature from.
    """
    try:
        files = os.listdir(UPLOAD_FOLDER)
        bin_files = [f for f in files if f.endswith(".bin")]

        if not bin_files:
            return jsonify({"error": "No firmware available yet"}), 404

        # Latest = most recently uploaded .bin file
        bin_files.sort(key=lambda f: os.path.getmtime(os.path.join(UPLOAD_FOLDER, f)))
        latest_file = bin_files[-1]
        latest_path = os.path.join(UPLOAD_FOLDER, latest_file)

        manifest = generate_manifest(
            version=os.path.splitext(latest_file)[0],
            filename=latest_file,
            filepath=latest_path
        )
        manifest["download_url"] = f"/download/{latest_file}"

        # Signature file is expected to share the same base name
        sig_filename = os.path.splitext(latest_file)[0] + ".sig"
        sig_path = os.path.join(UPLOAD_FOLDER, sig_filename)
        if os.path.exists(sig_path):
            manifest["signature_url"] = f"/download/{sig_filename}"
        else:
            manifest["signature_url"] = None

        return jsonify(manifest)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("[*] Starting OTA Mock Distribution Server on http://localhost:5000")
    print("[*] Upload directory:", UPLOAD_FOLDER)
    app.run(host="0.0.0.0", port=5000, debug=True)
