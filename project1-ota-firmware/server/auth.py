import os
from flask import request, jsonify
from functools import wraps

OTA_SERVER_TOKEN = os.getenv("OTA_SERVER_TOKEN", "test-token")


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing Authorization Header"}), 401

        expected = f"Bearer {OTA_SERVER_TOKEN}"

        if auth_header != expected:
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated