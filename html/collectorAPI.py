
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
            "error": "Invalid JSON request"
        }), 400

    username = data.get("username")
    event_id = data.get("eventId")

    if not isinstance(username, str) or not username.strip():
        return jsonify({
            "error": "Username is required"
        }), 400

    try:
        event_id = int(event_id)

        if event_id <= 0:
            raise ValueError()

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid event ID"
        }), 400

    try:
        # Pass data to collector_lib
        message_id = lib.handleRequests({
            "username": username,
            "event": event_id
        })

        if message_id == "Duplicate":
            return jsonify(message_id), 409

        return jsonify({
            "status": "pending",
            "message": "Registration request queued",
            "requestId": message_id
        }), 202

    except Exception:
        app.logger.exception("Error submitting registration")
        return jsonify({
            "error": "Unable to submit registration"
        }), 503

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
