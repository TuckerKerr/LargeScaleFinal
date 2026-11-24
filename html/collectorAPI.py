
from datetime import datetime, timezone
import re
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from proj_library import collector_lib as lib

# Directory containing collectorAPI.py and index.html
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)


# Serve the frontend
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# Retrieve events from PostgreSQL
@app.route("/api/events", methods=["GET"])
def get_events():
    try:
        events = lib.getEvents()

        return jsonify(events), 200

    except Exception:
        app.logger.exception("Error retrieving events")
        return jsonify({
            "error": "Unable to retrieve events"
        }), 500


# Receive registration requests
@app.route("/api/reservations", methods=["POST"])
def reserve_event():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid JSON request",
            "status": "rejected",
            "rejection_reason": "invalid_json"
        }), 400

    username = data.get("username")
    event_id = data.get("eventId")

    if not isinstance(username, str) or not username.strip():
        return jsonify({
            "error": "Username is required",
            "status": "rejected",
            "rejection_reason": "missing_username"
        }), 400

    try:
        event_id = int(event_id)

        if event_id <= 0:
            raise ValueError()

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid event ID",
            "status": "rejected",
            "rejection_reason": "invalid_event_id"
        }), 400

    requested_at = datetime.now(timezone.utc).isoformat()
    try:
        # Pass data to collector_lib
        message_id = lib.handleRequests({
            "username": username,
            "event": event_id,
            "requested_at": requested_at
        })

        if message_id == "Duplicate":
            return jsonify({
                "error": message_id,
                "status": "rejected",
                "rejection_reason": "duplicate_request",
                "requested_at": requested_at
            }), 409

        return jsonify({
            "status": "pending",
            "rejection_reason": None,
            "requested_at": requested_at,
            "message": "Registration request queued",
            "requestId": message_id
        }), 202

    except Exception:
        app.logger.exception("Error submitting registration")
        return jsonify({
            "error": "Unable to submit registration",
            "status": "unavailable",
            "requested_at": requested_at
        }), 503

@app.get("/api/reservations/<request_id>")
def get_reservation(request_id):
    if re.fullmatch(r"[0-9]{1,20}-[0-9]{1,20}", request_id) is None or any(
        int(part) > 2**64 - 1 for part in request_id.split("-")
    ):
        return jsonify({"error": "Invalid request ID"}), 400

    try:
        outcome = lib.getReservationOutcome(request_id)
        if outcome is not None:
            requested_at = outcome["requested_at"]
            return jsonify({
                "requestId": request_id,
                "status": outcome["status"],
                "rejection_reason": outcome["rejection_reason"],
                "requested_at": requested_at.isoformat() if requested_at else None,
            }), 200

        queued = lib.getQueuedRequest(request_id)
        if queued is not None:
            return jsonify({
                "requestId": request_id,
                "status": "pending",
                "rejection_reason": None,
                "requested_at": queued.get("requested_at"),
            }), 200

        return jsonify({"error": "Request not found"}), 404
    except Exception:
        app.logger.exception("Error looking up reservation")
        return jsonify({
            "status": "unavailable",
            "error": "Unable to retrieve reservation status",
        }), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
