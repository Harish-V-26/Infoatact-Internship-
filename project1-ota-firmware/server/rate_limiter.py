import time
from flask import request, jsonify
from functools import wraps

request_log = {}

MAX_REQUESTS = 10
WINDOW_SECONDS = 60


def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()

        if ip not in request_log:
            request_log[ip] = []

        request_log[ip] = [
            t for t in request_log[ip]
            if current_time - t < WINDOW_SECONDS
        ]

        if len(request_log[ip]) >= MAX_REQUESTS:
            return jsonify({
                "error": "Too Many Requests"
            }), 429

        request_log[ip].append(current_time)

        return f(*args, **kwargs)

    return decorated