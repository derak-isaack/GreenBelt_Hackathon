from flask import Blueprint, request, jsonify
import uuid
import datetime
import json
import os
import jwt
import hashlib

whistle_bp = Blueprint("whistleblower", __name__)

# Storage for anonymous reports
STORAGE_FILE = "whistleblower_reports.json"

SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")

def get_user_role():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or " " not in auth_header:
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("role")
    except:
        return None


def save_report(data):
    """Save whistleblower report into JSON storage."""
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "w") as f:
            json.dump([], f)

    with open(STORAGE_FILE, "r") as f:
        reports = json.load(f)

    reports.append(data)

    with open(STORAGE_FILE, "w") as f:
        json.dump(reports, f, indent=4)


@whistle_bp.route("/submit", methods=["POST"])
def submit_report():
    payload = request.get_json()
    print("Received payload:", payload)  # Debug log

    if not payload:
        return jsonify({"error": "Missing report payload"}), 400

    report_text = payload.get("report", "")
    attachments = payload.get("attachments", [])
    forest = payload.get("forest")  # NEW FIELD

    if not report_text:
        return jsonify({"error": "Report text is required"}), 400

    if not forest:
        return jsonify({"error": "Forest name is required"}), 400

    report_data = {
        "id": str(uuid.uuid4()),
        "report": report_text,
        "attachments": attachments,
        "forest": forest,   # SAVE HERE
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "received"
    }

    save_report(report_data)

    return jsonify({
        "message": "Report submitted anonymously.",
        "reference_id": report_data["id"]
    }), 200


@whistle_bp.route("/reports", methods=["GET"])
def get_reports():
    role = get_user_role()
    if role is None or role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    if not os.path.exists(STORAGE_FILE):
        return jsonify([]), 200

    with open(STORAGE_FILE, "r") as f:
        reports = json.load(f)

    # Transform reports to match frontend format
    transformed_reports = []
    for report in reports:
        report_text = report.get("report", "")
        lines = report_text.split('\n', 1)
        location = lines[0] if lines else "Unknown"
        incident_details = lines[1] if len(lines) > 1 else report_text

        # Convert timestamp to microseconds since epoch
        timestamp_micros = 0
        if report.get("timestamp"):
            try:
                dt = datetime.datetime.fromisoformat(report["timestamp"])
                timestamp_micros = int(dt.timestamp() * 1_000_000)
            except:
                pass

        transformed_reports.append({
            "id": hashlib.sha256(report.get("id", str(uuid.uuid4())).encode()).hexdigest(),
            "location": location,
            "incidentDetails": incident_details,
            "timestamp": timestamp_micros
        })

    return jsonify(transformed_reports), 200
